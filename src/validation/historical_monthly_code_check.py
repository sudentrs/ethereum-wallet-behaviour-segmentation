"""Sample historical month-end code states. No RPC calls are made on import."""

import argparse
import calendar
import csv
import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def normalize(value):
    value = str(value).strip().lower().removeprefix("0x")
    return "0x" + value if len(value) == 40 and all(c in "0123456789abcdef" for c in value) else None


def rpc_url():
    value = os.environ.get("ETH_RPC_URL")
    if not value and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
            key, sep, candidate = line.strip().removeprefix("export ").partition("=")
            if sep and key.strip() == "ETH_RPC_URL":
                value = candidate.strip().strip("\"'")
                break
    if not value:
        raise SystemExit("Set ETH_RPC_URL or add it to the project .env file.")
    return value


class RPC:
    def __init__(self, url, pause):
        self.url, self.pause = url, pause

    def batch(self, calls):
        payload = [{"jsonrpc": "2.0", "id": i, "method": method, "params": params}
                   for i, (method, params) in enumerate(calls)]
        for attempt in range(6):
            try:
                request = urllib.request.Request(self.url, json.dumps(payload).encode(),
                                                 {"Content-Type": "application/json"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = json.load(response)
                if not isinstance(data, list):
                    raise ValueError("Expected a JSON-RPC batch response")
                by_id = {item.get("id"): item for item in data}
                if len(by_id) != len(calls) or set(by_id) != set(range(len(calls))):
                    raise ValueError("Missing or duplicate RPC response IDs")
                values = []
                for i in range(len(calls)):
                    item = by_id[i]
                    if "error" in item or "result" not in item or item["result"] is None:
                        # Do not include provider messages, which could contain credentials.
                        raise ValueError(f"RPC error code={item.get('error', {}).get('code', 'missing_result')}")
                    values.append(item["result"])
                time.sleep(self.pause)
                return values
            except (urllib.error.URLError, OSError, ValueError) as exc:
                if attempt == 5:
                    raise RuntimeError(f"RPC failed after 6 attempts ({type(exc).__name__}); cached progress is preserved.") from None
                delay = min(60, 2 ** (attempt + 1))
                print(f"RPC retry {attempt + 1}/5 in {delay}s ({type(exc).__name__})", flush=True)
                time.sleep(delay)

    def call(self, method, params):
        return self.batch([(method, params)])[0]


def make_sample(args, output):
    path = output / "sample.csv"
    settings = {"year": args.year, "per_stratum": args.per_stratum, "seed": args.seed}
    excluded = set()
    for filename in args.exclude_sample:
        exclusion_path = ROOT / filename
        if not exclusion_path.is_file():
            raise SystemExit(f"Exclusion sample not found: {exclusion_path}")
        addresses = pd.read_csv(exclusion_path, usecols=["address"], dtype=str).address.map(normalize)
        if addresses.isna().any():
            raise SystemExit(f"Invalid address in exclusion sample: {exclusion_path}")
        excluded.update(addresses)
    if args.exclude_sample:
        settings["excluded_addresses_sha256"] = hashlib.sha256(
            "\n".join(sorted(excluded)).encode()).hexdigest()
        settings["excluded_address_count"] = len(excluded)
    settings_path = output / "sample_settings.json"
    if path.exists():
        if not settings_path.exists() or json.loads(settings_path.read_text()) != settings:
            raise SystemExit("Sample settings differ. Use a new --output-dir.")
        print("Reusing saved sample.csv", flush=True)
        saved = pd.read_csv(path, dtype={"address": str})
        if set(saved.address) & excluded:
            raise SystemExit("Saved sample overlaps exclusions. Use a new --output-dir.")
        return saved
    print("[1/6] Reading baseline address cache...", flush=True)
    base = pd.read_csv(ROOT / "data/interim/eoa_contract_cache.csv", dtype=str,
                       usecols=["address", "block", "account_type"])
    print(f"  Loaded {len(base):,} baseline rows; normalizing addresses...", flush=True)
    if not base["block"].eq("latest").all():
        raise SystemExit("Baseline cache must contain only latest observations.")
    base["address"] = base.address.map(normalize)
    base = base.dropna(subset=["address"]).drop_duplicates("address", keep="last")
    base = base[["address", "account_type"]].rename(columns={"account_type": "baseline_type"})
    if not base.baseline_type.isin(["EOA", "contract"]).all():
        raise SystemExit("Unexpected baseline account_type.")
    for k in (4, 5, 6):
        print(f"[{k - 2}/6] Reading and merging K{k} labels...", flush=True)
        labels = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv", dtype=str)
        labels["address"] = labels.wallet.map(normalize)
        labels = labels[["address", "cluster"]].rename(columns={"cluster": f"k{k}"})
        base = base.merge(labels, on="address", how="left", validate="one_to_one")
        base[f"k{k}"] = base[f"k{k}"].fillna("excluded")
    print("[5/6] Reading activity features...", flush=True)
    features = pd.read_csv(ROOT / "data/processed/wallet_kmeans6_expanded_daily_features.csv",
                           usecols=["wallet", "total_tx"], dtype={"wallet": str})
    print(f"  Loaded {len(features):,} feature rows; merging activity...", flush=True)
    features["address"] = features.wallet.map(normalize)
    base = base.merge(features[["address", "total_tx"]], on="address", how="left", validate="one_to_one")
    # Quantile boundaries without arbitrarily splitting tied transaction counts.
    base["activity_band"] = pd.qcut(base.total_tx, q=3, duplicates="drop").astype(str)
    if excluded:
        before = len(base)
        base = base.loc[~base.address.isin(excluded)].copy()
        print(f"Excluded {before - len(base):,} previously sampled addresses; sampling the remaining population.", flush=True)
    print("[6/6] Selecting stratified sample...", flush=True)
    strata = ["baseline_type", "k4", "k5", "k6", "activity_band"]
    base = base.sort_values("address").reset_index(drop=True)
    rng = random.Random(args.seed)
    chosen = []
    for _, group in base.groupby(strata, sort=True, dropna=False):
        chosen.extend(rng.sample(list(group.index), min(len(group), args.per_stratum)))
    sample = base.loc[chosen].sort_values("address").reset_index(drop=True)
    if sample.empty:
        raise SystemExit("No addresses sampled.")
    counts = base.groupby(strata, dropna=False).size().rename("population_n").reset_index()
    sample = sample.merge(counts, on=strata, validate="many_to_one")
    sample["sample_n"] = sample.groupby(strata, dropna=False).address.transform("size")
    sample["sampling_weight"] = sample.population_n / sample.sample_n
    sample.to_csv(path, index=False)
    settings_path.write_text(json.dumps(settings, indent=2))
    return sample


def month_blocks(rpc, year, output):
    path = output / "month_end_blocks.csv"
    if path.exists():
        frame = pd.read_csv(path)
        expected = [f"{year}-{month:02d}" for month in range(1, 13)]
        if frame.month.tolist() != expected:
            raise SystemExit("Saved month blocks do not match requested year.")
        return frame
    latest = int(rpc.call("eth_blockNumber", []), 16)
    rows = []
    for month in range(1, 13):
        next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
        boundary = calendar.timegm(datetime(next_year, next_month, 1).timetuple())
        lo, hi = 0, latest
        while lo < hi:
            mid = (lo + hi + 1) // 2
            block = rpc.call("eth_getBlockByNumber", [hex(mid), False])
            if int(block["timestamp"], 16) < boundary:
                lo = mid
            else:
                hi = mid - 1
        block = rpc.call("eth_getBlockByNumber", [hex(lo), False])
        following = rpc.call("eth_getBlockByNumber", [hex(lo + 1), False])
        if not int(block["timestamp"], 16) < boundary <= int(following["timestamp"], 16):
            raise RuntimeError("Month-end boundary verification failed")
        rows.append({"month": f"{year}-{month:02d}", "block_number": lo,
                     "block_hash": block["hash"], "timestamp_utc": datetime.fromtimestamp(
                         int(block["timestamp"], 16), timezone.utc).isoformat()})
        print(f"{year}-{month:02d}: month-end block {lo:,}", flush=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    return frame


def run(args):
    print("Historical monthly code check starting (sampling first, RPC queries afterwards).", flush=True)
    output = ROOT / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    sample = make_sample(args, output)
    print(f"Sample: {len(sample):,} addresses; up to {len(sample) * 12:,} code queries.", flush=True)
    if args.prepare_only:
        print("Sample prepared; no RPC requests made.")
        return
    rpc = RPC(rpc_url(), args.sleep_seconds)
    if rpc.call("eth_chainId", []) != "0x1":
        raise SystemExit("RPC must be Ethereum Mainnet.")
    blocks = month_blocks(rpc, args.year, output)
    cache_path = output / "address_block_cache.csv"
    fields = ["address", "block_number", "code_present", "code_bytes"]
    cache = {}
    if cache_path.exists():
        with cache_path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                cache[(row["address"], int(row["block_number"]))] = row
    for block in blocks.itertuples(index=False):
        missing = [a for a in sample.address if (a, block.block_number) not in cache]
        print(f"{block.month}: {len(missing):,} uncached queries", flush=True)
        for start in range(0, len(missing), args.batch_size):
            batch = missing[start:start + args.batch_size]
            values = rpc.batch([("eth_getCode", [a, hex(block.block_number)]) for a in batch])
            rows = []
            for address, code in zip(batch, values):
                if not isinstance(code, str) or not code.startswith("0x") or len(code) % 2:
                    raise RuntimeError("Invalid code response; not classifying it as empty code.")
                try:
                    code_bytes = len(bytes.fromhex(code[2:]))
                except ValueError:
                    raise RuntimeError("Invalid hex code response") from None
                rows.append(dict(address=address, block_number=block.block_number,
                                 code_present=int(code_bytes > 0), code_bytes=code_bytes))
            exists = cache_path.exists() and cache_path.stat().st_size > 0
            with cache_path.open("a", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                if not exists:
                    writer.writeheader()
                writer.writerows(rows)
            for row in rows:
                cache[(row["address"], row["block_number"])] = row
            print(f"  {min(start + len(batch), len(missing)):,}/{len(missing):,}", flush=True)
    records = []
    for block in blocks.itertuples(index=False):
        for address in sample.address:
            row = dict(cache[(address, block.block_number)])
            row["month"] = block.month
            row["code_present"] = int(row["code_present"])
            records.append(row)
    detail = pd.DataFrame(records).merge(sample, on="address", validate="many_to_one")
    detail["differs_from_baseline"] = detail.code_present.ne(detail.baseline_type.eq("contract").astype(int)).astype(int)
    detail.to_csv(output / "monthly_address_states.csv", index=False)
    for name, groups in [("monthly_summary", ["month", "baseline_type"]),
                         *[(f"monthly_k{k}_summary", ["month", "baseline_type", f"k{k}"]) for k in (4, 5, 6)]]:
        rows = []
        for keys, group in detail.groupby(groups, dropna=False):
            rows.append(dict(zip(groups, keys)) | {
                "sample_n": len(group), "code_present_n": int(group.code_present.sum()),
                "differs_from_baseline_n": int(group.differs_from_baseline.sum()),
                "weighted_code_share": float((group.code_present * group.sampling_weight).sum() / group.sampling_weight.sum()),
                "weighted_difference_share": float((group.differs_from_baseline * group.sampling_weight).sum() / group.sampling_weight.sum())})
        pd.DataFrame(rows).to_csv(output / f"{name}.csv", index=False)
    pivot = detail.pivot(index="address", columns="month", values="code_present").sort_index(axis=1)
    address_summary = pd.DataFrame({"months_with_code": pivot.sum(axis=1),
                                    "observed_monthly_state_changes": pivot.diff(axis=1).iloc[:, 1:].abs().sum(axis=1)})
    address_summary.join(sample.set_index("address")).to_csv(output / "address_summary.csv")
    print(f"Complete. Outputs: {output}")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2022)
    parser.add_argument("--per-stratum", type=int, default=20,
                        help="Maximum per baseline type x K4/K5/K6 combination x activity band")
    parser.add_argument("--seed", type=int, default=492)
    parser.add_argument("--exclude-sample", action="append", default=[], metavar="CSV",
                        help="Exclude addresses from an earlier sample.csv; repeat for multiple samples. Weights describe the remaining population.")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    parser.add_argument("--output-dir", default="data/interim/historical_monthly_code_2022")
    parser.add_argument("--prepare-only", action="store_true", help="Prepare sample only; no network requests")
    args = parser.parse_args()
    if args.per_stratum < 1 or args.batch_size < 1 or args.sleep_seconds < 0:
        parser.error("per-stratum and batch-size must be positive; sleep-seconds must be nonnegative")
    if args.year < 2016 or args.year >= datetime.now(timezone.utc).year:
        parser.error("Choose a completed calendar year from 2016 onward")
    return args


if __name__ == "__main__":
    run(parse_args())
