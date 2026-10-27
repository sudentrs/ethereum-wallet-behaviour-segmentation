"""Bounded historical-RPC benchmark, never an automatic full-population scan."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import random
import sys
import threading
import time
import urllib.error
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_historical_wallet_cohort import connect, record
from scripts.run_historical_exclusion_sample import parse_code
from src.validation.historical_monthly_code_check import RPC, rpc_url


def decode_response(data, expected):
    if not isinstance(data, list) or len(data) != expected:
        raise ValueError("Incomplete batch")
    by_id = {row.get("id"): row for row in data}
    if len(by_id) != expected or set(by_id) != set(range(expected)):
        raise ValueError("Missing or duplicate response IDs")
    if any("error" in row or row.get("result") is None for row in by_id.values()):
        raise ValueError("RPC error in batch")
    return [parse_code(by_id[i]["result"]) for i in range(expected)]


class BatchClient:
    def __init__(self, url, starts_per_second=4):
        self.url = url
        self.lock = threading.Lock()
        self.next_start = 0.
        self.spacing = 1 / starts_per_second

    def request(self, batch, block):
        payload = [{"jsonrpc": "2.0", "id": i, "method": "eth_getCode",
                    "params": [a, hex(block)]} for i, a in enumerate(batch)]
        errors = 0
        attempted_checks = 0
        for attempt in range(3):
            with self.lock:
                wait = max(0, self.next_start-time.perf_counter())
                self.next_start = max(self.next_start, time.perf_counter()) + self.spacing
            if wait:
                time.sleep(wait)
            attempted_checks += len(batch)
            try:
                request = urllib.request.Request(self.url, json.dumps(payload).encode(),
                                                 {"Content-Type": "application/json"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    sizes = decode_response(json.load(response), len(batch))
                return sizes, errors, attempted_checks
            except (urllib.error.URLError, OSError, ValueError):
                errors += 1
                if attempt < 2:
                    time.sleep(2 ** (attempt+1))
        # No provider strings/URLs in errors or output artifacts.
        return None, errors, attempted_checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default="results_v3/year_end_2022_rpc_benchmark")
    parser.add_argument("--profiles", nargs="+", default=["20:1", "50:2", "100:2"],
                        help="Batch-size:worker-count pairs; at most three profiles")
    args = parser.parse_args()
    try:
        profiles = [tuple(map(int, item.split(":"))) for item in args.profiles]
        if not 1 <= len(profiles) <= 3 or any(len(p) != 2 or not 1 <= p[0] <= 100 or not 1 <= p[1] <= 2 for p in profiles):
            raise ValueError()
    except ValueError:
        parser.error("Use one to three batch:worker profiles, batch <=100, workers <=2")
    output = ROOT / args.report_dir
    if output.exists():
        raise SystemExit("Use a new report directory for another benchmark")
    registry = ROOT / "data/interim/historical_wallet_cohort_v1/registry.sqlite"
    if not registry.exists():
        raise SystemExit("Prepare the population registry first")
    pins = pd.read_csv(ROOT / "results_v3/historical_exclusion_audit_results/month_end_blocks.csv")
    pin = pins.loc[pins.month.eq("2022-12")].iloc[0]
    rpc = RPC(rpc_url(), 0)
    if rpc.call("eth_chainId", []) != "0x1":
        raise ValueError("Expected Ethereum Mainnet")
    header = rpc.call("eth_getBlockByNumber", [hex(int(pin.block_number)), False])
    following = rpc.call("eth_getBlockByNumber", [hex(int(pin.block_number)+1), False])
    boundary = 1672531200
    if header["hash"] != pin.block_hash or not int(header["timestamp"], 16) < boundary <= int(following["timestamp"], 16):
        raise ValueError("Invalid pinned year-end boundary")
    output.mkdir(parents=True)
    results = []
    client = BatchClient(rpc_url())
    with connect(registry) as db:
        identity = db.execute("SELECT value FROM metadata WHERE key='population_ready'").fetchone()
        if not identity:
            raise ValueError("Incomplete population registry")
        groups = {}
        per_group = 200 * len(profiles)
        for retained in (0, 1):
            groups[retained] = [r[0] for r in db.execute(
                "SELECT address FROM population WHERE baseline_retained=? AND (checked_mask&2048)=0 ORDER BY address LIMIT ?",
                (retained, per_group))]
            if len(groups[retained]) != per_group:
                raise ValueError("Insufficient uncached addresses for fixed benchmark")
            random.Random(492+retained).shuffle(groups[retained])
        for i, (batch_size, workers) in enumerate(profiles):
            wallets = groups[0][i*200:(i+1)*200] + groups[1][i*200:(i+1)*200]
            random.Random(492+i).shuffle(wallets)
            pd.DataFrame({"address": wallets}).to_csv(output / f"profile_{i}_addresses.csv", index=False)
            batches = [wallets[j:j+batch_size] for j in range(0, len(wallets), batch_size)]
            errors = attempts = completed = failed = 0
            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=workers) as executor:
                pending = {executor.submit(client.request, batch, int(pin.block_number)): batch for batch in batches}
                for future in as_completed(pending):
                    batch = pending[future]
                    sizes, retries, submitted = future.result()
                    errors += retries
                    attempts += submitted
                    if sizes is None:
                        failed += len(batch)
                        continue
                    with db:
                        for address, size in zip(batch, sizes):
                            record(db, address, 12, size, f"year_end_benchmark_profile_{i}")
                    completed += len(batch)
            elapsed = time.perf_counter()-start
            result = {"profile": i, "batch_size": batch_size, "workers": workers,
                      "selected_addresses": len(wallets), "successful_checks": completed,
                      "failed_unresolved_checks": failed, "attempted_code_checks_including_retries": attempts,
                      "batch_error_responses": errors, "elapsed_seconds": elapsed,
                      "successful_checks_per_second": completed/elapsed}
            results.append(result)
            pd.DataFrame(results).to_csv(output / "benchmark.csv", index=False)
            print(json.dumps(result), flush=True)
            if failed:
                print("Stopping escalation after unresolved batch failures.", flush=True)
                break
        remaining = db.execute("SELECT count(*) FROM population WHERE (checked_mask&2048)=0").fetchone()[0]
        cached = db.execute("SELECT count(*) FROM population WHERE (checked_mask&2048)>0").fetchone()[0]
    usable = [r for r in results if r["failed_unresolved_checks"] == 0]
    best = max(usable, key=lambda r: r["successful_checks_per_second"]) if usable else None
    summary = {"definition": "empty_code_at_last_block_of_2022_not_year_long_EOA_identity",
               "block_number": int(pin.block_number), "block_hash": pin.block_hash,
               "unique_check_budget": 400*len(profiles), "max_code_attempts_with_retries": 1200*len(profiles),
               "global_http_start_cap_per_second": 4,
               "cached_year_end_addresses": cached, "remaining_year_end_addresses": remaining,
               "best_measured_profile": best,
               "projected_remaining_hours_at_best_short_run_rate": remaining/best["successful_checks_per_second"]/3600 if best else None,
               "caveat": "Short benchmark only; not sustained provider capacity or quota. No full run started. Cached month-end observations reused; no cohort definition overwritten."}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
