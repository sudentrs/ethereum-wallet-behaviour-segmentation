"""Exact one-pass robust scaling for the year-end count/activity feature table."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


RAW_FEATURES = {
    "activity_density", "in_active_day_ratio", "out_active_day_ratio",
    "both_active_day_ratio", "in_out_day_balance", "tx_count_cv",
    "tx_concentration_ratio",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def transform(values: np.ndarray, feature: str) -> tuple[np.ndarray, str]:
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    if feature in RAW_FEATURES:
        return values, "raw"
    if np.any(values < 0):
        return np.sign(values) * np.log1p(np.abs(values)), "signed_log1p"
    return np.log1p(values), "log1p"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--matrix-output", type=Path, required=True)
    parser.add_argument("--stats-output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--chunksize", type=int, default=100_000)
    args = parser.parse_args()
    if args.matrix_output.exists() or args.stats_output.exists() or args.manifest.exists():
        raise FileExistsError("Refusing to overwrite existing scaling artifacts")
    header = pd.read_csv(args.input, nrows=1, dtype={"wallet": "string"})
    features = [c for c in header.columns if c not in {"wallet", "cluster"}]
    if not features:
        raise ValueError("No features found")
    n = sum(len(chunk) for chunk in pd.read_csv(args.input, usecols=["wallet"], chunksize=args.chunksize))
    if n == 0:
        raise ValueError("Empty input")
    args.matrix_output.parent.mkdir(parents=True, exist_ok=True)
    matrix = np.lib.format.open_memmap(args.matrix_output, mode="w+", dtype=np.float32,
                                       shape=(n, len(features)))
    offset = 0
    transform_types: dict[str, str] = {}
    for chunk_no, chunk in enumerate(pd.read_csv(args.input, usecols=features, chunksize=args.chunksize), 1):
        values = chunk[features].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
        for j, feature in enumerate(features):
            converted, kind = transform(values[:, j], feature)
            matrix[offset:offset + len(chunk), j] = converted.astype(np.float32)
            previous = transform_types.setdefault(feature, kind)
            if previous != kind:
                raise ValueError("Inconsistent feature transform")
        offset += len(chunk)
        print(f"transformed chunk={chunk_no:03d} rows={offset:,}/{n:,}", flush=True)
    if offset != n or not np.isfinite(matrix).all():
        raise ValueError("Invalid transformed feature matrix")
    stats = []
    for j, feature in enumerate(features):
        q25, median, q75 = np.quantile(matrix[:, j], [0.25, 0.5, 0.75])
        iqr = q75 - q25
        stats.append({"feature": feature, "median": float(median), "q25": float(q25),
                      "q75": float(q75), "iqr": float(iqr),
                      "transform_type": transform_types[feature]})
    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(args.stats_output, index=False)
    medians = stats_df["median"].to_numpy(dtype=np.float32)
    iqrs = stats_df["iqr"].to_numpy(dtype=np.float32)
    denominators = np.where(np.isfinite(iqrs) & (iqrs != 0), iqrs, 1.0)
    written = 0
    for chunk_no, start in enumerate(range(0, n, args.chunksize), 1):
        end = min(start + args.chunksize, n)
        scaled = (np.asarray(matrix[start:end]) - medians) / denominators
        if not np.isfinite(scaled).all():
            raise ValueError("Nonfinite scaled values")
        matrix[start:end] = scaled.astype(np.float32)
        written = end
        print(f"scaled chunk={chunk_no:03d} rows={written:,}/{n:,}", flush=True)
    matrix.flush()
    manifest = {"input": str(args.input), "input_sha256": sha256(args.input),
                "matrix_output": str(args.matrix_output), "matrix_sha256": sha256(args.matrix_output),
                "stats": str(args.stats_output), "stats_sha256": sha256(args.stats_output),
                "wallets": n, "feature_count": len(features), "features": features,
                "method": "exact_quantiles_over_transformed_full_cohort_v1"}
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
