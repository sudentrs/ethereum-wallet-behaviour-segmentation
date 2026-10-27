"""Resumable month-end audit of the fixed exclusion probability sample.

No cohort changes. Offline reporting is the default; --execute enables RPC.
Transaction origination is a separate outcome and is not inferred from code.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/validation"))
from historical_monthly_code_check import RPC, month_blocks, rpc_url


def outcome(values):
    if any(value > 0 for value in values):
        return "does_not_meet_all_month_ends_empty"
    if len(values) == 12:
        return "empty_all_12_month_ends"
    return "unresolved"


def parse_code(code):
    if not isinstance(code, str) or not code.startswith("0x") or len(code) % 2:
        raise ValueError("Malformed code response")
    return len(bytes.fromhex(code[2:]))


def summarize(sample, cache, output):
    rows = []
    for item in sample.itertuples(index=False):
        observed = [value for (address, _), value in cache.items() if address == item.address]
        rows.append({"address": item.address, "activity_stratum": item.activity_stratum,
                     "population_n": item.population_n, "sample_n": item.sample_n,
                     "sampling_weight": item.sampling_weight,
                     "observed_months": len(observed),
                     "months_with_code": sum(v > 0 for v in observed),
                     "snapshot_outcome": outcome(observed),
                     "origination_evidence_status": item.evidence_status})
    frame = pd.DataFrame(rows)
    frame.to_csv(output / "address_results.csv", index=False)
    population = sample.groupby("activity_stratum").population_n.first().sum()
    positive = frame.snapshot_outcome.eq("empty_all_12_month_ends")
    unknown = frame.snapshot_outcome.eq("unresolved")
    lower = float(frame.loc[positive, "sampling_weight"].sum() / population)
    upper = float(frame.loc[positive | unknown, "sampling_weight"].sum() / population)
    result = {
        "sample_addresses": len(frame), "cached_address_months": len(cache),
        "required_address_months": len(frame) * 12,
        "empty_all_month_ends_n": int(positive.sum()),
        "unresolved_snapshot_n": int(unknown.sum()),
        "weighted_identification_lower": lower,
        "weighted_identification_upper": upper,
        "sampling_confidence_interval": None,
        "note": "Identification bounds are not confidence intervals. No origination negatives inferred."
    }
    (output / "progress.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", default="results_v3/historical_exclusion_audit_design")
    parser.add_argument("--output-dir", default="data/interim/historical_exclusion_probability_audit")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 100:
        parser.error("batch-size must be between 1 and 100")
    sample_path = ROOT / args.design_dir / "sample.csv"
    sample = pd.read_csv(sample_path)
    if sample.address.duplicated().any() or not sample.address.str.fullmatch(r"0x[0-9a-f]{40}").all():
        raise ValueError("Invalid sample addresses")
    output = ROOT / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(sample_path.read_bytes()).hexdigest()
    meta_path = output / "sample_identity.json"
    identity = {"sample_sha256": digest, "year": 2022, "chain_id": 1}
    if meta_path.exists() and json.loads(meta_path.read_text()) != identity:
        raise ValueError("Sample changed; use a separate output directory")
    meta_path.write_text(json.dumps(identity, indent=2), encoding="utf-8")
    cache_path = output / "address_month_cache.csv"
    cache = {}
    if cache_path.exists():
        for row in pd.read_csv(cache_path).itertuples(index=False):
            key = (row.address, row.month)
            if row.address not in set(sample.address) or row.month not in [f"2022-{m:02d}" for m in range(1, 13)]:
                raise ValueError("Cache has unexpected address or month")
            if key in cache or row.code_bytes < 0:
                raise ValueError("Invalid/duplicate cache observation")
            cache[key] = int(row.code_bytes)
    print(json.dumps(summarize(sample, cache, output), indent=2), flush=True)
    if not args.execute:
        print("Offline report only. Use --execute after configuring an archive-capable RPC.")
        return
    if args.env_file:
        # Explicit local file only; never echo credentials or provider errors.
        for line in args.env_file.read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.strip().removeprefix("export ").partition("=")
            if sep and key.strip() == "ETH_RPC_URL":
                os.environ["ETH_RPC_URL"] = value.strip().strip("\"'")
    rpc = RPC(rpc_url(), 0.3)
    if rpc.call("eth_chainId", []) != "0x1":
        raise ValueError("Expected Ethereum Mainnet")
    try:
        blocks = month_blocks(rpc, 2022, output)
        # Confirm saved pins against the endpoint on every resumed run.
        for block in blocks.itertuples(index=False):
            header = rpc.call("eth_getBlockByNumber", [hex(block.block_number), False])
            if header["hash"] != block.block_hash:
                raise ValueError("Pinned block hash mismatch")
        for block in blocks.itertuples(index=False):
            missing = [a for a in sample.address if (a, block.month) not in cache]
            for start in range(0, len(missing), args.batch_size):
                batch = missing[start:start + args.batch_size]
                codes = rpc.batch([("eth_getCode", [a, hex(block.block_number)]) for a in batch])
                rows = [{"address": a, "month": block.month,
                         "block_number": block.block_number, "block_hash": block.block_hash,
                         "code_bytes": parse_code(code)} for a, code in zip(batch, codes)]
                exists = cache_path.exists() and cache_path.stat().st_size > 0
                with cache_path.open("a", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    if not exists:
                        writer.writeheader()
                    writer.writerows(rows)
                for row in rows:
                    cache[(row["address"], row["month"])] = row["code_bytes"]
                print(f"{block.month}: cached {len(cache)}/{len(sample)*12}", flush=True)
    finally:
        print(json.dumps(summarize(sample, cache, output), indent=2), flush=True)
    if len(cache) == len(sample) * 12:
        (output / "MONTHLY_CODE_COMPLETE").write_text(digest + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
