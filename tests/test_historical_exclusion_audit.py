"""Offline tests: no RPC endpoint or scientific data required."""

import unittest
import tempfile
from pathlib import Path

import pandas as pd
from scipy.stats import hypergeom

from scripts.prepare_historical_exclusion_audit import addresses, draw
from scripts.run_historical_exclusion_sample import outcome, parse_code
from scripts.summarize_historical_exclusion_sample import population_interval
from scripts.build_historical_wallet_cohort import connect, counts, export_status, record
from scripts.benchmark_year_end_rpc import decode_response


class HistoricalAuditTests(unittest.TestCase):
    def test_benchmark_reorders_and_rejects_bad_responses(self):
        self.assertEqual(decode_response([{"id": 1, "result": "0x6000"},
                                         {"id": 0, "result": "0x"}], 2), [0, 2])
        for data in ([{"id": 0, "result": "0x"}],
                     [{"id": 0, "result": "0x"}, {"id": 0, "result": "0x"}],
                     [{"id": 0, "error": {}}, {"id": 1, "result": "0x"}],
                     [{"id": 0, "result": None}, {"id": 1, "result": "0x"}]):
            with self.assertRaises(ValueError):
                decode_response(data, 2)

    def test_address_normalization(self):
        address = "0" * 39 + "1"
        self.assertEqual(addresses(pd.Series([address])).iloc[0], "0x" + address)
        self.assertEqual(addresses(pd.Series(["0x" + address])).iloc[0], "0x" + address)
        with self.assertRaises(ValueError):
            addresses(pd.Series(["bad"]))
        with self.assertRaises(ValueError):
            addresses(pd.Series([address, "0x" + address]))

    def test_sample_order_weights_and_census(self):
        frame = pd.DataFrame({"address": [f"0x{i:040x}" for i in range(1, 13)],
                              "total_tx": [1]*4 + [5]*4 + [30]*4})
        sample = draw(frame, 2, 42)
        self.assertEqual(sample.address.tolist(), draw(frame.iloc[::-1], 2, 42).address.tolist())
        self.assertEqual(sample.address.nunique(), 6)
        self.assertAlmostEqual(sample.sampling_weight.sum(), 12)
        self.assertEqual(len(draw(frame, 10, 42)), 12)

    def test_unresolved_is_not_empty(self):
        self.assertEqual(outcome([]), "unresolved")
        self.assertEqual(outcome([0]*11), "unresolved")
        self.assertEqual(outcome([0]*12), "empty_all_12_month_ends")
        self.assertEqual(outcome([1]), "does_not_meet_all_month_ends_empty")

    def test_code_validation(self):
        self.assertEqual(parse_code("0x"), 0)
        self.assertEqual(parse_code("0x6000"), 2)
        for malformed in (None, "", "0x0", "0xgg"):
            with self.assertRaises(ValueError):
                parse_code(malformed)

    def test_exact_interval_against_enumeration(self):
        tail = .01
        for N in (10, 25):
            for n in (2, 5, N):
                for x in range(n + 1):
                    allowed = [K for K in range(x, N-n+x+1)
                               if hypergeom.sf(x-1, N, K, n) >= tail
                               and hypergeom.cdf(x, N, K, n) >= tail]
                    self.assertEqual(population_interval(N, n, x, tail),
                                     (min(allowed), max(allowed)))

    def test_zero_events_not_zero_uncertainty(self):
        lower, upper = population_interval(1000, 200, 0, .01)
        self.assertEqual(lower, 0)
        self.assertGreater(upper, 0)

    def test_registry_requires_twelve_snapshots(self):
        db = connect(":memory:")
        a, b, c = [f"0x{i:040x}" for i in (1, 2, 3)]
        db.executemany("INSERT INTO population(address,baseline_retained,total_tx) VALUES(?,?,?)",
                       [(a, 1, 10), (b, 0, 20), (c, 0, 30)])
        for month in range(1, 13):
            record(db, a, month, 0, "test")
        record(db, b, 12, 10, "test")
        record(db, c, 12, 0, "test")
        result = counts(db)
        self.assertEqual(result["snapshot_included"], 1)
        self.assertEqual(result["snapshot_excluded"], 1)
        self.assertEqual(result["snapshot_unresolved"], 1)
        record(db, a, 1, 0, "duplicate_same_observation")
        self.assertEqual(db.execute("SELECT count(*) FROM observations").fetchone()[0], 14)
        with self.assertRaises(ValueError):
            record(db, a, 1, 2, "conflict")
        db.close()

    def test_registry_never_exports_unresolved_population(self):
        db = connect(":memory:")
        a = f"0x{1:040x}"
        db.execute("INSERT INTO population(address,baseline_retained,total_tx) VALUES(?,1,10)", (a,))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pins = root / "pins.csv"
            pins.write_text("test", encoding="ascii")
            result = export_status(db, root, root, pins, 0)
            self.assertFalse(result["complete"])
            self.assertEqual(result["maximum_remaining_address_month_checks"], 12)
            self.assertFalse((root / "COHORT_READY.json").exists())
            self.assertFalse((root / "cohort_members.csv").exists())
            for month in range(1, 13):
                record(db, a, month, 0, "test")
            result = export_status(db, root, root, pins, 0)
            self.assertTrue(result["complete"])
            self.assertTrue((root / "COHORT_READY.json").exists())
            self.assertEqual(pd.read_csv(root / "cohort_members.csv", dtype=str).wallet.iloc[0], a[2:])
        db.close()


if __name__ == "__main__":
    unittest.main()
