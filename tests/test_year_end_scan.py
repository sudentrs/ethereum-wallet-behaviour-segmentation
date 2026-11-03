"""Offline scan recovery tests; no RPC calls."""
import tempfile
import threading
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
from http.client import IncompleteRead
from scripts.benchmark_year_end_rpc import BatchClient
from src.validation.historical_monthly_code_check import RPC
from scripts.build_historical_wallet_cohort import connect, record
from scripts.run_year_end_scan import scan, scan_parallel, endpoint_urls


class Client:
    def __init__(self, fail=False):
        self.fail = fail
        self.seen = []

    def request(self, batch, block):
        self.seen.extend(batch)
        return (None if self.fail else [0 if int(a, 16) % 2 else 2 for a in batch],
                3 if self.fail else 0, len(batch)*(3 if self.fail else 1))


class ScanTests(unittest.TestCase):
    def test_truncated_batch_response_retries_and_counts_attempts(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.side_effect = [IncompleteRead(b'partial'), b'[{"id":0,"result":"0x"}]']
        with patch('urllib.request.urlopen', return_value=response), patch('time.sleep'):
            self.assertEqual(BatchClient('https://example.invalid').request(['0x'+'0'*40], 16308189),
                             ([0], 1, 2))

    def test_persistently_truncated_batch_remains_unresolved(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.side_effect = IncompleteRead(b'partial')
        with patch('urllib.request.urlopen', return_value=response), patch('time.sleep'):
            self.assertEqual(BatchClient('https://example.invalid').request(['0x'+'0'*40], 16308189),
                             (None, 3, 3))

    def test_validation_rpc_also_retries_truncated_response(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.side_effect = [IncompleteRead(b'partial'), b'[{"id":0,"result":"0x1"}]']
        with patch('urllib.request.urlopen', return_value=response), patch('time.sleep'):
            self.assertEqual(RPC('https://example.invalid', 0).call('eth_chainId', []), '0x1')

    def setUp(self):
        self.db = connect(':memory:')
        with self.db:
            self.db.executemany('INSERT INTO population(address,baseline_retained,total_tx) VALUES(?,1,1)',
                                [(f'0x{i:040x}',) for i in range(1, 46)])

    def tearDown(self):
        self.db.close()

    def test_resume_budget_and_month_isolation(self):
        with self.db:
            record(self.db, f'0x{1:040x}', 12, 0, 'benchmark')
            record(self.db, f'0x{2:040x}', 1, 4, 'monthly')
        client = Client()
        self.assertEqual(scan(self.db, client, 16308189, 23, lambda *a: None), 23)
        self.assertEqual(len(set(client.seen)), 23)
        self.assertNotIn(f'0x{1:040x}', client.seen)
        self.assertIn(f'0x{2:040x}', client.seen)
        resumed = Client()
        self.assertEqual(scan(self.db, resumed, 16308189, 100, lambda *a: None), 21)
        self.assertFalse(set(client.seen) & set(resumed.seen))
        self.assertEqual(self.db.execute('SELECT count(*) FROM observations WHERE month=12').fetchone()[0], 45)
        self.assertEqual(self.db.execute('SELECT code_bytes FROM observations WHERE month=1').fetchone()[0], 4)

    def test_failed_batch_never_becomes_empty_evidence(self):
        with self.assertRaises(RuntimeError):
            scan(self.db, Client(fail=True), 16308189, 45, lambda *a: None,
                 recovery_rounds=0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM observations').fetchone()[0], 0)
        self.assertEqual(scan(self.db, Client(), 16308189, 45, lambda *a: None), 45)

    def test_transient_failure_recovers_without_skipping_addresses(self):
        client = Client()
        request = client.request
        calls = []
        def flaky(batch, block):
            calls.append(list(batch))
            if len(calls) == 1:
                return None, 3, len(batch)*3
            return request(batch, block)
        client.request = flaky
        waits = []
        progress = []
        self.assertEqual(scan(self.db, client, 16308189, 45,
                              lambda *a: progress.append(a), sleep=waits.append), 45)
        self.assertEqual(waits, [15])
        self.assertEqual(calls[0], calls[1])
        self.assertEqual(progress[-1], (45, 105, 3))

    def test_parallel_distribution_and_exact_budget(self):
        rendezvous = threading.Barrier(2, timeout=5)
        class ParallelClient(Client):
            def request(self, batch, block):
                if not self.seen:
                    rendezvous.wait()
                return super().request(batch, block)
        clients = [ParallelClient(), ParallelClient()]
        self.assertEqual(scan_parallel(self.db, clients, 16308189, 43,
                                       lambda *a: None), 43)
        self.assertTrue(all(c.seen for c in clients))
        self.assertFalse(set(clients[0].seen) & set(clients[1].seen))
        self.assertEqual(sum(len(c.seen) for c in clients), 43)
        self.assertEqual(scan_parallel(self.db, [Client(), Client()], 16308189,
                                       100, lambda *a: None), 2)

    def test_parallel_failure_preserves_successes_and_resume(self):
        rendezvous = threading.Barrier(2, timeout=5)
        class StartedClient(Client):
            def request(self, batch, block):
                rendezvous.wait()
                return super().request(batch, block)
        with self.assertRaises(RuntimeError):
            scan_parallel(self.db, [StartedClient(fail=True), StartedClient()], 16308189,
                          40, lambda *a: None, recovery_rounds=0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM observations').fetchone()[0], 20)
        self.assertEqual(scan_parallel(self.db, [Client(), Client()], 16308189,
                                       100, lambda *a: None), 25)

    def test_endpoint_configuration_override_order_and_deduplication(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text('ETH_RPC_URL=https://one\nETH_RPC_URL_2=https://two\n'
                            'ETH_RPC_URL_10=https://ten\nETH_RPC_URL_3=https://two\n')
            self.assertEqual(endpoint_urls(path, {}), ['https://one', 'https://two', 'https://ten'])
            self.assertEqual(endpoint_urls(path, {'ETH_RPC_URL_2': 'https://override'}),
                             ['https://one', 'https://override', 'https://two', 'https://ten'])


if __name__ == '__main__':
    unittest.main()
