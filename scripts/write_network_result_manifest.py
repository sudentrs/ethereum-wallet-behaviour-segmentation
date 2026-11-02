"""Record provenance for a completed monthly network-null validation run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_raw(raw_root: Path, month: str) -> Path:
    for path in (raw_root / f"{month}.tsv" / f"{month}.tsv", raw_root / f"{month}.tsv"):
        if path.is_file():
            return path
    raise FileNotFoundError(month)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--labels-npy", type=Path, required=True)
    parser.add_argument("--wallet-source", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--sample-edges", type=int, required=True)
    parser.add_argument("--permutations", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    summary = args.out_dir / "monthly_network_validation_summary.csv"
    months = pd.read_csv(summary)["month"].astype(str).tolist()
    raw = []
    for month in months:
        path = resolve_raw(args.raw_root, month)
        stat = path.stat()
        raw.append({"month": month, "path": str(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    (args.out_dir / "manifest.json").write_text(json.dumps({
        "labels_npy": str(args.labels_npy), "labels_npy_sha256": sha256(args.labels_npy),
        "wallet_source": str(args.wallet_source), "wallet_source_sha256": sha256(args.wallet_source),
        "sample_edges": args.sample_edges, "permutations": args.permutations, "seed": args.seed,
        "test": "upper-tail same-label fraction under endpoint-wallet label permutation",
        "raw_sources": raw, "summary_sha256": sha256(summary),
        "interpretation": "The null preserves sampled transfer edges and label composition among endpoint wallets. It tests label-network alignment, not causal preference or transaction-community identity."
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
