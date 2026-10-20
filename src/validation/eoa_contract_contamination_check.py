import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd


def normalize_address(value: object) -> str | None:
    text = str(value).strip().lower()
    if text.startswith("0x"):
        text = text[2:]
    if len(text) != 40:
        return None
    if any(ch not in "0123456789abcdef" for ch in text):
        return None
    return "0x" + text


def load_rpc_url(cli_value: str | None) -> str:
    if cli_value:
        return cli_value
    env_value = os.environ.get("ETH_RPC_URL")
    if env_value:
        return env_value
    raise SystemExit("Provide --rpc-url or set ETH_RPC_URL.")


def load_cache(path: Path, block: str | None = None) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["address"].lower(): row for row in reader
                if block is None or row.get("block") == block}


def append_cache(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["address", "block", "account_type", "code_length_hex"]
        )
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def rpc_batch_get_code(rpc_url: str, addresses: list[str], block: str, timeout: int) -> list[dict]:
    payload = [
        {
            "jsonrpc": "2.0",
            "id": idx,
            "method": "eth_getCode",
            "params": [address, block],
        }
        for idx, address in enumerate(addresses)
    ]
    request = urllib.request.Request(
        rpc_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    if isinstance(data, dict):
        data = [data]
    return sorted(data, key=lambda item: item.get("id", 0))


def classify_addresses(
    rpc_url: str,
    addresses: list[str],
    block: str,
    cache_path: Path,
    batch_size: int,
    sleep_seconds: float,
    timeout: int,
) -> pd.DataFrame:
    cache = load_cache(cache_path, block=block)
    missing = [address for address in addresses if address.lower() not in cache]
    print(f"Addresses requested: {len(addresses):,}")
    print(f"Already cached: {len(addresses) - len(missing):,}")
    print(f"Need RPC lookup: {len(missing):,}")

    for start in range(0, len(missing), batch_size):
        batch = missing[start : start + batch_size]
        responses = None
        for attempt in range(1, 7):
            try:
                responses = rpc_batch_get_code(rpc_url, batch, block, timeout)
            except urllib.error.HTTPError as exc:
                if exc.code != 429:
                    raise
                wait = min(120, sleep_seconds * (2 ** attempt) + attempt)
                print(f"HTTP 429 rate limit; waiting {wait:.1f}s before retry {attempt}/6")
                time.sleep(wait)
                continue
            except urllib.error.URLError as exc:
                wait = min(120, sleep_seconds * (2 ** attempt) + attempt)
                print(f"RPC connection error ({exc.reason}); waiting {wait:.1f}s before retry {attempt}/6")
                time.sleep(wait)
                continue
            except ConnectionResetError as exc:
                wait = min(120, sleep_seconds * (2 ** attempt) + attempt)
                print(f"RPC connection reset ({exc}); waiting {wait:.1f}s before retry {attempt}/6")
                time.sleep(wait)
                continue
            retryable = [
                item.get("error", {})
                for item in responses
                if item.get("error", {}).get("code") == 429
            ]
            if not retryable:
                break
            wait = min(60, sleep_seconds * (2 ** attempt) + attempt)
            print(f"Rate limit hit; waiting {wait:.1f}s before retry {attempt}/6")
            time.sleep(wait)
        if responses is None:
            raise RuntimeError("No RPC responses received.")
        cache_rows = []
        for address, response in zip(batch, responses):
            if "error" in response:
                raise RuntimeError(f"RPC error for {address}: {response['error']}")
            code = response.get("result", "0x")
            account_type = "EOA" if code == "0x" else "contract"
            cache_rows.append(
                {
                    "address": address.lower(),
                    "block": block,
                    "account_type": account_type,
                    "code_length_hex": str(max(len(code) - 2, 0)),
                }
            )
        append_cache(cache_path, cache_rows)
        for row in cache_rows:
            cache[row["address"]] = row
        print(f"Looked up {min(start + batch_size, len(missing)):,}/{len(missing):,}")
        if sleep_seconds:
            time.sleep(sleep_seconds)

    return pd.DataFrame([cache[address.lower()] for address in addresses])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate EOA/contract contamination for wallet clusters using eth_getCode."
    )
    parser.add_argument(
        "--labels-csv",
        required=True,
        help="CSV containing wallet addresses and cluster labels.",
    )
    parser.add_argument("--wallet-column", default="wallet")
    parser.add_argument("--cluster-column", default="cluster")
    parser.add_argument(
        "--sample-per-cluster",
        type=int,
        default=5000,
        help="Maximum wallets to sample per cluster. Use 0 for all wallets.",
    )
    parser.add_argument("--random-seed", type=int, default=492)
    parser.add_argument(
        "--block",
        default="latest",
        help="Block tag or hex block number for eth_getCode, e.g. latest or 0xf00000.",
    )
    parser.add_argument("--rpc-url", default=None)
    parser.add_argument(
        "--cache-csv",
        default="data/interim/eoa_contract_cache.csv",
        help="Local cache of address classifications.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/eoa_contract_contamination",
        help="Directory for contamination outputs.",
    )
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rpc_url = load_rpc_url(args.rpc_url)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    labels = pd.read_csv(
        args.labels_csv,
        usecols=[args.wallet_column, args.cluster_column],
        dtype={args.wallet_column: str},
    ).dropna()
    labels["address"] = labels[args.wallet_column].map(normalize_address)
    invalid = labels["address"].isna().sum()
    labels = labels.dropna(subset=["address"]).copy()
    labels[args.cluster_column] = labels[args.cluster_column].astype(int)

    if args.sample_per_cluster > 0:
        labels = (
            labels.groupby(args.cluster_column, group_keys=False)
            .apply(
                lambda group: group.sample(
                    n=min(len(group), args.sample_per_cluster),
                    random_state=args.random_seed,
                )
            )
            .reset_index(drop=True)
        )

    addresses = labels["address"].drop_duplicates().tolist()
    classifications = classify_addresses(
        rpc_url=rpc_url,
        addresses=addresses,
        block=args.block,
        cache_path=Path(args.cache_csv),
        batch_size=args.batch_size,
        sleep_seconds=args.sleep_seconds,
        timeout=args.timeout,
    )

    classified = labels.merge(classifications, on="address", how="left")
    summary = (
        classified.groupby(args.cluster_column)
        .agg(
            sampled_addresses=("address", "nunique"),
            eoa_count=("account_type", lambda s: int((s == "EOA").sum())),
            contract_count=("account_type", lambda s: int((s == "contract").sum())),
        )
        .reset_index()
    )
    summary["contract_share"] = (
        summary["contract_count"] / summary["sampled_addresses"].replace(0, pd.NA)
    ).fillna(0)
    summary["invalid_wallet_values_in_input"] = int(invalid)

    classified.to_csv(output_dir / "sampled_address_classifications.csv", index=False)
    summary.to_csv(output_dir / "cluster_contract_contamination_summary.csv", index=False)

    print("\nCluster contract contamination summary:")
    print(summary.to_string(index=False))
    print(f"\nSaved outputs to {output_dir}")


if __name__ == "__main__":
    main()
