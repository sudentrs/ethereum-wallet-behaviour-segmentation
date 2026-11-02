"""Build the annual count-and-activity feature table for the year-end cohort.

This excludes pooled token-value fields because their denominational
comparability is unresolved. It never replaces legacy EOA-only artifacts.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd


COUNT_ACTIVITY_FEATURES = [
    "active_days_observed",
    "activity_span_days",
    "activity_density",
    "total_tx",
    "avg_daily_tx_count",
    "max_daily_tx_count",
    "std_daily_tx_count",
    "in_active_days",
    "out_active_days",
    "both_active_days",
    "in_active_day_ratio",
    "out_active_day_ratio",
    "both_active_day_ratio",
    "in_out_day_balance",
    "tx_count_cv",
    "tx_concentration_ratio",
]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_wallet(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip().str.lower().str.removeprefix("0x")
    if not values.str.fullmatch(r"[0-9a-f]{40}").all():
        raise ValueError("Invalid wallet identifier")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--chunksize", type=int, default=100_000)
    args = parser.parse_args()
    if args.chunksize < 1:
        parser.error("chunksize must be positive")

    cohort = pd.read_csv(args.cohort, compression="infer", dtype={"wallet": "string"})
    if cohort.columns.tolist() != ["wallet"]:
        raise ValueError("Cohort must contain exactly one wallet column")
    cohort["wallet"] = normalize_wallet(cohort.wallet)
    if cohort.wallet.duplicated().any():
        raise ValueError("Duplicate wallets in cohort")
    cohort_set = set(cohort.wallet)

    header = pd.read_csv(args.features, nrows=0).columns.tolist()
    needed = {"wallet", "cluster", *COUNT_ACTIVITY_FEATURES}
    missing = sorted(needed - set(header))
    if missing:
        raise ValueError(f"Source features missing columns: {missing}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output}")

    written = 0
    seen: set[str] = set()
    first = True
    usecols = ["wallet", *COUNT_ACTIVITY_FEATURES, "cluster"]
    for i, chunk in enumerate(pd.read_csv(args.features, usecols=usecols,
                                          dtype={"wallet": "string"}, chunksize=args.chunksize), 1):
        chunk["wallet"] = normalize_wallet(chunk.wallet)
        keep = chunk.loc[chunk.wallet.isin(cohort_set)].copy()
        if keep.wallet.duplicated().any() or set(keep.wallet) & seen:
            raise ValueError("Duplicate wallet in source feature table")
        seen.update(keep.wallet)
        if not keep.empty:
            keep.to_csv(args.output, index=False, mode="w" if first else "a", header=first)
            first = False
            written += len(keep)
        print(f"chunk={i:03d} retained={written:,}", flush=True)
    if seen != cohort_set:
        missing_wallets = len(cohort_set - seen)
        raise ValueError(f"Cohort-feature coverage incomplete: {missing_wallets:,} wallets missing")

    manifest = {
        "definition": "empty_code_at_last_block_of_2022_not_year_long_EOA_identity",
        "representation": "count_and_activity_only_v1",
        "excluded_feature_family": "pooled_token_value_and_value_derived_features",
        "feature_columns": COUNT_ACTIVITY_FEATURES,
        "cohort_file": str(args.cohort),
        "cohort_sha256": file_hash(args.cohort),
        "source_feature_file": str(args.features),
        "source_feature_sha256": file_hash(args.features),
        "output_file": str(args.output),
        "output_sha256": file_hash(args.output),
        "cohort_wallets": len(cohort),
        "written_wallets": written,
        "legacy_cluster_column_retained_for_traceability_only": True,
    }
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
