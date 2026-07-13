import argparse
from pathlib import Path

import numpy as np
import pandas as pd


RAW_RATIO_FEATURES = {
    "activity_density",
    "in_active_day_ratio",
    "out_active_day_ratio",
    "both_active_day_ratio",
    "in_out_day_balance",
    "tx_count_cv",
    "total_flow_cv",
    "tx_concentration_ratio",
    "flow_concentration_ratio",
}

SIGNED_FEATURE_HINTS = ("net_flow", "balance")


def transform_series(name, s):
    s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if name in RAW_RATIO_FEATURES:
        return s, "raw"
    if any(hint in name for hint in SIGNED_FEATURE_HINTS):
        return np.sign(s) * np.log1p(np.abs(s)), "signed_log1p"
    if (s < 0).any():
        return np.sign(s) * np.log1p(np.abs(s)), "signed_log1p"
    return np.log1p(s), "log1p"


def detect_feature_cols(path):
    sample = pd.read_csv(path, nrows=5000, dtype={"wallet": str})
    id_cols = ["wallet", "cluster"]
    return [
        c for c in sample.columns
        if c not in set(id_cols + ["first_active_date", "last_active_date"])
        and pd.api.types.is_numeric_dtype(sample[c])
    ]


def compute_streaming_stats(path, feature_cols, chunksize):
    stats = []
    for idx, col in enumerate(feature_cols, start=1):
        values = []
        transform_type = None
        for chunk in pd.read_csv(path, usecols=[col], chunksize=chunksize):
            transformed, transform_type = transform_series(col, chunk[col])
            values.append(transformed.astype("float64", copy=False))

        transformed_all = pd.concat(values, ignore_index=True)
        q25 = transformed_all.quantile(0.25)
        median = transformed_all.quantile(0.50)
        q75 = transformed_all.quantile(0.75)
        iqr = q75 - q25
        stats.append({
            "feature": col,
            "median": median,
            "q25": q25,
            "q75": q75,
            "iqr": iqr,
            "transform_type": transform_type,
        })
        print(f"stats {idx:02d}/{len(feature_cols):02d}: {col}")
    return pd.DataFrame(stats)


def scale_with_stats(path, output, stats_df, chunksize):
    stats = stats_df.set_index("feature").to_dict(orient="index")
    feature_cols = list(stats_df["feature"])
    usecols = ["wallet", *feature_cols, "cluster"]

    if output.exists():
        output.unlink()

    first = True
    total_rows = 0
    for chunk_id, df in enumerate(
        pd.read_csv(path, usecols=usecols, dtype={"wallet": str}, chunksize=chunksize),
        start=1,
    ):
        out = df[["wallet"]].copy()
        for col in feature_cols:
            transformed, _ = transform_series(col, df[col])
            meta = stats[col]
            iqr = meta["iqr"]
            if pd.isna(iqr) or iqr == 0:
                scaled = transformed - meta["median"]
            else:
                scaled = (transformed - meta["median"]) / iqr
            out[col] = scaled.astype("float32")
        out["cluster"] = df["cluster"].astype(int)
        out.to_csv(output, mode="w" if first else "a", header=first, index=False)
        first = False
        total_rows += len(df)
        print(f"scaled chunk={chunk_id:03d} rows_written={total_rows:,}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="dataverse_files/wallet_kmeans6_expanded_daily_features.csv")
    parser.add_argument("--output", default="dataverse_files/wallet_kmeans6_expanded_daily_features_robust_scaled.csv")
    parser.add_argument(
        "--chunksize",
        type=int,
        default=100_000,
        help="Rows to process at once. Lower this on low-RAM machines.",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    feature_cols = detect_feature_cols(args.input)
    stats_df = compute_streaming_stats(args.input, feature_cols, args.chunksize)
    stats_df.to_csv(output.with_name(output.stem + "_scaling_stats.csv"), index=False)
    scale_with_stats(args.input, output, stats_df, args.chunksize)

    print(f"Saved scaled features: {output}")
    print(f"Scaled feature count: {len(feature_cols)}")


if __name__ == "__main__":
    main()
