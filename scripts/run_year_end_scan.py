"""Resumable full-population scan of code at the last block of 2022."""

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.benchmark_year_end_rpc import BatchClient
from scripts.build_historical_wallet_cohort import record
from src.validation.historical_monthly_code_check import RPC

DEFINITION = "empty_code_at_last_block_of_2022_not_year_long_EOA_identity"


def endpoint_urls(env_file=None, environ=None):
    """Read numbered RPCs locally; never print credentials or URLs."""
    values = {}
    path = ROOT / '.env' if env_file is None else Path(env_file)
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            key, sep, value = line.strip().removeprefix('export ').partition('=')
            if sep:
                values[key.strip()] = value.strip().strip("\"'")
    values.update(os.environ if environ is None else environ)
    keys = ['ETH_RPC_URL'] + sorted(
        (key for key in values if key.startswith('ETH_RPC_URL_') and key[12:].isdigit()),
        key=lambda key: int(key[12:]))
    urls = list(dict.fromkeys(values[key] for key in keys if values.get(key)))
    if not urls:
        raise SystemExit('Set ETH_RPC_URL in the environment or project .env.')
    return urls


def request_with_recovery(client, batch, block, rounds, stop, sleep=None):
    attempts = errors = 0
    for recovery in range(rounds + 1):
        if stop.is_set():
            return None, attempts, errors
        sizes, retries, submitted = client.request(batch, block)
        attempts += submitted
        errors += retries
        if sizes is not None:
            return sizes, attempts, errors
        if recovery < rounds:
            delay = min(120, 15 * 2**recovery)
            print(f'RPC batch unresolved; waiting {delay}s before recovery '
                  f'{recovery+1}/{rounds}.', flush=True)
            if sleep is None:
                stop.wait(delay)
            else:
                sleep(delay)
    return None, attempts, errors


def scan_parallel(db, clients, block, limit, progress, recovery_rounds=5, sleep=None):
    """One in-flight batch per endpoint; only the coordinator touches SQLite."""
    if not clients:
        raise ValueError('At least one RPC client is required')
    last = ""
    completed = attempts = errors = scheduled = 0
    stop = threading.Event()
    pool = ThreadPoolExecutor(max_workers=len(clients))
    pending = {}
    failed = False

    def submit(client):
        nonlocal last, scheduled
        if scheduled >= limit:
            return
        batch = [r[0] for r in db.execute(
            "SELECT address FROM population WHERE address>? AND (checked_mask&2048)=0 "
            "ORDER BY address LIMIT ?", (last, min(20, limit-scheduled)))]
        if not batch:
            return
        last = batch[-1]
        scheduled += len(batch)
        future = pool.submit(request_with_recovery, client, batch, block,
                             recovery_rounds, stop, sleep)
        pending[future] = (client, batch)

    try:
        for client in clients:
            submit(client)
        while pending:
            done, _ = wait(pending, timeout=1, return_when=FIRST_COMPLETED)
            for future in done:
                client, batch = pending.pop(future)
                sizes, submitted, retries = future.result()
                attempts += submitted
                errors += retries
                if sizes is None:
                    failed = True
                    stop.set()
                else:
                    if len(sizes) != len(batch):
                        raise RuntimeError('Incomplete RPC batch; progress preserved.')
                    with db:
                        for address, size in zip(batch, sizes):
                            record(db, address, 12, size, 'year_end_full_scan')
                    completed += len(batch)
                progress(completed, attempts, errors)
                if not failed:
                    submit(client)
            if not done:
                progress(completed, attempts, errors)
        if failed:
            raise RuntimeError('RPC remained unavailable after cooldowns; saved progress is preserved. Resume with the same command.')
    finally:
        stop.set()
        pool.shutdown(wait=True, cancel_futures=True)
    return completed


def scan(db, client, block, limit, progress, recovery_rounds=5, sleep=time.sleep):
    """Compatibility entry point for single-endpoint callers."""
    return scan_parallel(db, [client], block, limit, progress, recovery_rounds, sleep)


def atomic_json(path, data):
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def export_members(db, output, pin):
    temp = output / "cohort_members.csv.tmp"
    with temp.open("w", newline="", encoding="ascii") as stream:
        writer = csv.writer(stream)
        writer.writerow(["wallet"])
        writer.writerows((address[2:],) for (address,) in db.execute(
            "SELECT address FROM population WHERE (checked_mask&2048)>0 "
            "AND (code_mask&2048)=0 ORDER BY address"))
    target = output / "cohort_members.csv"
    temp.replace(target)
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    atomic_json(output / "YEAR_END_READY.json", dict(
        definition=DEFINITION, block_number=int(pin["block_number"]),
        block_hash=pin["block_hash"], cohort_sha256=digest.hexdigest(),
        cohort_file=target.name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Enable RPC calls; default only reports local status")
    parser.add_argument("--max-code-queries", type=int, default=2738243,
                        help="Successful new checks allowed this run; retries add provider requests")
    parser.add_argument("--recovery-rounds", type=int, default=5,
                        help="Additional batch retry rounds with 15-120 second cooldowns")
    parser.add_argument('--rpc-count', type=int, default=None,
                        help='Use only the first N configured endpoints; default uses all')
    args = parser.parse_args()
    if args.max_code_queries < 1:
        parser.error("max-code-queries must be positive")
    if not 0 <= args.recovery_rounds <= 10:
        parser.error("recovery-rounds must be between 0 and 10")
    urls = endpoint_urls()
    if args.rpc_count is not None:
        if not 1 <= args.rpc_count <= len(urls):
            parser.error('rpc-count exceeds the number of configured endpoints or is less than 1')
        urls = urls[:args.rpc_count]
    registry = ROOT / "data/interim/historical_wallet_cohort_v1/registry.sqlite"
    if not registry.exists():
        raise SystemExit("Prepare the population registry first.")
    output = ROOT / "data/interim/year_end_2022_full_scan"
    output.mkdir(parents=True, exist_ok=True)
    # Separate lock DB: prevents duplicate scanners without blocking evidence commits.
    lock = sqlite3.connect(output / "runner_lock.sqlite", timeout=0)
    try:
        lock.execute("BEGIN EXCLUSIVE")
    except sqlite3.OperationalError:
        raise SystemExit("Another year-end scanner is running.") from None
    db = sqlite3.connect(registry, timeout=30)
    try:
        if not db.execute("SELECT value FROM metadata WHERE key='population_ready'").fetchone():
            raise SystemExit("Population initialization is incomplete.")
        with (ROOT / "results_v3/historical_exclusion_audit_results/month_end_blocks.csv").open(newline="") as stream:
            pin = next(row for row in csv.DictReader(stream) if row["month"] == "2022-12")
        pin_identity = json.dumps({"block_number": int(pin["block_number"]), "block_hash": pin["block_hash"]}, sort_keys=True)
        old = db.execute("SELECT value FROM metadata WHERE key='year_end_scan_pin'").fetchone()
        if old and old[0] != pin_identity:
            raise SystemExit("Year-end pin changed; refusing to reuse evidence.")
        started = time.monotonic()
        last_report = [0.0]

        def status(completed=0, attempts=0, errors=0, force=False, state="running"):
            if not force and time.monotonic()-last_report[0] < 30:
                return
            total, cached, included = db.execute(
                "SELECT count(*),sum((checked_mask&2048)>0),"
                "sum((checked_mask&2048)>0 AND (code_mask&2048)=0) FROM population").fetchone()
            cached, included = cached or 0, included or 0
            elapsed = time.monotonic()-started
            result = dict(definition=DEFINITION, block_number=int(pin["block_number"]),
                          block_hash=pin["block_hash"], population=total, cached=cached,
                          included=included, excluded=cached-included, remaining=total-cached,
                          complete=cached == total, state=state, new_checks_this_run=completed,
                          attempts_this_run=attempts, batch_errors_this_run=errors,
                          rpc_workers=len(urls),
                          elapsed_seconds=round(elapsed, 2))
            atomic_json(output / "status.json", result)
            print(json.dumps(result), flush=True)
            last_report[0] = time.monotonic()

        status(force=True, state="starting" if args.execute else "status_only")
        if not args.execute:
            return
        block = int(pin["block_number"])
        for index, url in enumerate(urls, 1):
            print(f'Validating RPC {index}/{len(urls)}...', flush=True)
            rpc = RPC(url, 0)
            if rpc.call("eth_chainId", []) != "0x1":
                raise SystemExit(f'RPC {index}: expected Ethereum Mainnet.')
            header = rpc.call("eth_getBlockByNumber", [hex(block), False])
            following = rpc.call("eth_getBlockByNumber", [hex(block+1), False])
            if header["hash"] != pin["block_hash"] or not int(header["timestamp"], 16) < 1672531200 <= int(following["timestamp"], 16):
                raise SystemExit(f'RPC {index}: invalid pinned year-end boundary.')
        with db:
            db.execute("INSERT OR REPLACE INTO metadata VALUES('year_end_scan_pin',?)", (pin_identity,))
        latest = [0, 0, 0]

        def progress(*values):
            latest[:] = values
            status(*values)

        try:
            scan_parallel(db, [BatchClient(url) for url in urls], block,
                          args.max_code_queries, progress, recovery_rounds=args.recovery_rounds)
        except (KeyboardInterrupt, Exception):
            status(*latest, force=True, state="stopped")
            raise
        remaining = db.execute("SELECT count(*) FROM population WHERE (checked_mask&2048)=0").fetchone()[0]
        if not remaining:
            export_members(db, output, pin)
        status(*latest, force=True, state="complete" if not remaining else "budget_reached")
    finally:
        db.close()
        lock.close()


if __name__ == "__main__":
    main()
