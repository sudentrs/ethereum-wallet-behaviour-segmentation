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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="dataverse_files/wallet_kmeans6_expanded_daily_features.csv")
    parser.add_argument("--output", default="dataverse_files/wallet_kmeans6_expanded_daily_features_robust_scaled.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.input, dtype={"wallet": str})
    id_cols = ["wallet", "cluster"]
    feature_cols = [
        c for c in df.columns
        if c not in set(id_cols + ["first_active_date", "last_active_date"])
        and pd.api.types.is_numeric_dtype(df[c])
    ]

    out = df[["wallet"]].copy()
    stats = []
    for col in feature_cols:
        transformed, transform_type = transform_series(col, df[col])
        q25 = transformed.quantile(0.25)
        median = transformed.quantile(0.50)
        q75 = transformed.quantile(0.75)
        iqr = q75 - q25
        if pd.isna(iqr) or iqr == 0:
            scaled = transformed - median
        else:
            scaled = (transformed - median) / iqr
        out[col] = scaled.astype("float32")
        stats.append({
            "feature": col,
            "median": median,
            "q25": q25,
            "q75": q75,
            "iqr": iqr,
            "transform_type": transform_type,
        })

    out["cluster"] = df["cluster"].astype(int)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)
    pd.DataFrame(stats).to_csv(output.with_name(output.stem + "_scaling_stats.csv"), index=False)
    print(f"Saved scaled features: {output}")
    print(f"Scaled feature count: {len(feature_cols)}")


if __name__ == "__main__":
    main()
