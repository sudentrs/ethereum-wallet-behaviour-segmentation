import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def clean_wallet(series):
    return series.astype("string").str.strip().str.lower()


def safe_divide(numerator, denominator):
    result = numerator / denominator
    if isinstance(result, pd.Series):
        return result.replace([np.inf, -np.inf], np.nan).fillna(0)
    if pd.isna(result) or np.isinf(result):
        return 0
    return result


def read_labels(path):
    labels = pd.read_csv(path, usecols=["wallet", "cluster"], dtype={"wallet": str})
    labels["wallet"] = clean_wallet(labels["wallet"])
    labels["cluster"] = labels["cluster"].astype(int)
    labels = labels.drop_duplicates("wallet")
    return labels


def aggregate_daily_features(daily_path, labels, chunksize):
    wallet_universe = set(labels["wallet"])
    parts = []
    total_rows = 0
    kept_rows = 0

    usecols = ["wallet", "date", "total_in", "total_out", "tx_count"]
    for chunk_id, chunk in enumerate(
        pd.read_csv(daily_path, usecols=usecols, dtype={"wallet": str}, chunksize=chunksize),
        start=1,
    ):
        total_rows += len(chunk)
        chunk["wallet"] = clean_wallet(chunk["wallet"])
        chunk = chunk[chunk["wallet"].isin(wallet_universe)].copy()
        kept_rows += len(chunk)

        if chunk.empty:
            continue

        chunk["date"] = pd.to_datetime(chunk["date"], errors="coerce")
        chunk["tx_count"] = pd.to_numeric(chunk["tx_count"], errors="coerce").fillna(0.0)
        chunk["total_in"] = pd.to_numeric(chunk["total_in"], errors="coerce").fillna(0.0)
        chunk["total_out"] = pd.to_numeric(chunk["total_out"], errors="coerce").fillna(0.0)

        chunk["net_flow"] = chunk["total_in"] - chunk["total_out"]
        chunk["total_flow"] = chunk["total_in"] + chunk["total_out"]

        chunk["in_active"] = (chunk["total_in"] > 0).astype(np.int8)
        chunk["out_active"] = (chunk["total_out"] > 0).astype(np.int8)
        chunk["both_active"] = ((chunk["total_in"] > 0) & (chunk["total_out"] > 0)).astype(np.int8)

        chunk["tx_count_sq"] = chunk["tx_count"] ** 2
        chunk["total_in_sq"] = chunk["total_in"] ** 2
        chunk["total_out_sq"] = chunk["total_out"] ** 2
        chunk["net_flow_sq"] = chunk["net_flow"] ** 2
        chunk["total_flow_sq"] = chunk["total_flow"] ** 2

        grouped = chunk.groupby("wallet", sort=False).agg(
            active_days_observed=("date", "count"),
            first_active_date=("date", "min"),
            last_active_date=("date", "max"),
            total_tx=("tx_count", "sum"),
            total_in_sum=("total_in", "sum"),
            total_out_sum=("total_out", "sum"),
            total_net_flow_sum=("net_flow", "sum"),
            total_flow_sum=("total_flow", "sum"),
            max_daily_tx_count=("tx_count", "max"),
            max_daily_total_in=("total_in", "max"),
            max_daily_total_out=("total_out", "max"),
            max_daily_total_flow=("total_flow", "max"),
            tx_count_sq_sum=("tx_count_sq", "sum"),
            total_in_sq_sum=("total_in_sq", "sum"),
            total_out_sq_sum=("total_out_sq", "sum"),
            net_flow_sq_sum=("net_flow_sq", "sum"),
            total_flow_sq_sum=("total_flow_sq", "sum"),
            in_active_days=("in_active", "sum"),
            out_active_days=("out_active", "sum"),
            both_active_days=("both_active", "sum"),
        ).reset_index()

        parts.append(grouped)
        print(
            f"chunk={chunk_id:03d} rows_read={total_rows:,} rows_kept={kept_rows:,} "
            f"wallets_in_chunk={len(grouped):,}"
        )

    if not parts:
        raise RuntimeError("No rows matched the cluster wallet universe.")

    combined = pd.concat(parts, ignore_index=True)
    wallet_agg = combined.groupby("wallet", sort=False).agg(
        active_days_observed=("active_days_observed", "sum"),
        first_active_date=("first_active_date", "min"),
        last_active_date=("last_active_date", "max"),
        total_tx=("total_tx", "sum"),
        total_in_sum=("total_in_sum", "sum"),
        total_out_sum=("total_out_sum", "sum"),
        total_net_flow_sum=("total_net_flow_sum", "sum"),
        total_flow_sum=("total_flow_sum", "sum"),
        max_daily_tx_count=("max_daily_tx_count", "max"),
        max_daily_total_in=("max_daily_total_in", "max"),
        max_daily_total_out=("max_daily_total_out", "max"),
        max_daily_total_flow=("max_daily_total_flow", "max"),
        tx_count_sq_sum=("tx_count_sq_sum", "sum"),
        total_in_sq_sum=("total_in_sq_sum", "sum"),
        total_out_sq_sum=("total_out_sq_sum", "sum"),
        net_flow_sq_sum=("net_flow_sq_sum", "sum"),
        total_flow_sq_sum=("total_flow_sq_sum", "sum"),
        in_active_days=("in_active_days", "sum"),
        out_active_days=("out_active_days", "sum"),
        both_active_days=("both_active_days", "sum"),
    ).reset_index()

    return wallet_agg, total_rows, kept_rows


def derive_features(wallet_agg):
    wallet_agg["activity_span_days"] = (
        wallet_agg["last_active_date"] - wallet_agg["first_active_date"]
    ).dt.days + 1

    wallet_agg["activity_density"] = safe_divide(
        wallet_agg["active_days_observed"], wallet_agg["activity_span_days"]
    )

    wallet_agg["avg_daily_tx_count"] = safe_divide(wallet_agg["total_tx"], wallet_agg["active_days_observed"])
    wallet_agg["avg_daily_total_in"] = safe_divide(wallet_agg["total_in_sum"], wallet_agg["active_days_observed"])
    wallet_agg["avg_daily_total_out"] = safe_divide(wallet_agg["total_out_sum"], wallet_agg["active_days_observed"])
    wallet_agg["avg_daily_net_flow"] = safe_divide(wallet_agg["total_net_flow_sum"], wallet_agg["active_days_observed"])
    wallet_agg["avg_daily_total_flow"] = safe_divide(wallet_agg["total_flow_sum"], wallet_agg["active_days_observed"])

    ex2_tx = safe_divide(wallet_agg["tx_count_sq_sum"], wallet_agg["active_days_observed"])
    ex2_in = safe_divide(wallet_agg["total_in_sq_sum"], wallet_agg["active_days_observed"])
    ex2_out = safe_divide(wallet_agg["total_out_sq_sum"], wallet_agg["active_days_observed"])
    ex2_net = safe_divide(wallet_agg["net_flow_sq_sum"], wallet_agg["active_days_observed"])
    ex2_flow = safe_divide(wallet_agg["total_flow_sq_sum"], wallet_agg["active_days_observed"])

    wallet_agg["std_daily_tx_count"] = np.sqrt(np.maximum(ex2_tx - wallet_agg["avg_daily_tx_count"] ** 2, 0))
    wallet_agg["std_daily_total_in"] = np.sqrt(np.maximum(ex2_in - wallet_agg["avg_daily_total_in"] ** 2, 0))
    wallet_agg["std_daily_total_out"] = np.sqrt(np.maximum(ex2_out - wallet_agg["avg_daily_total_out"] ** 2, 0))
    wallet_agg["std_daily_net_flow"] = np.sqrt(np.maximum(ex2_net - wallet_agg["avg_daily_net_flow"] ** 2, 0))
    wallet_agg["std_daily_total_flow"] = np.sqrt(np.maximum(ex2_flow - wallet_agg["avg_daily_total_flow"] ** 2, 0))

    wallet_agg["in_active_day_ratio"] = safe_divide(wallet_agg["in_active_days"], wallet_agg["active_days_observed"])
    wallet_agg["out_active_day_ratio"] = safe_divide(wallet_agg["out_active_days"], wallet_agg["active_days_observed"])
    wallet_agg["both_active_day_ratio"] = safe_divide(wallet_agg["both_active_days"], wallet_agg["active_days_observed"])
    wallet_agg["in_out_day_balance"] = safe_divide(
        wallet_agg["in_active_days"] - wallet_agg["out_active_days"],
        wallet_agg["active_days_observed"],
    )

    wallet_agg["tx_count_cv"] = safe_divide(wallet_agg["std_daily_tx_count"], wallet_agg["avg_daily_tx_count"])
    wallet_agg["total_flow_cv"] = safe_divide(wallet_agg["std_daily_total_flow"], wallet_agg["avg_daily_total_flow"])
    wallet_agg["tx_concentration_ratio"] = safe_divide(wallet_agg["max_daily_tx_count"], wallet_agg["total_tx"])
    wallet_agg["flow_concentration_ratio"] = safe_divide(wallet_agg["max_daily_total_flow"], wallet_agg["total_flow_sum"])

    final_cols = [
        "wallet",
        "active_days_observed",
        "first_active_date",
        "last_active_date",
        "activity_span_days",
        "activity_density",
        "total_tx",
        "total_in_sum",
        "total_out_sum",
        "total_net_flow_sum",
        "total_flow_sum",
        "avg_daily_tx_count",
        "avg_daily_total_in",
        "avg_daily_total_out",
        "avg_daily_net_flow",
        "avg_daily_total_flow",
        "max_daily_tx_count",
        "max_daily_total_in",
        "max_daily_total_out",
        "max_daily_total_flow",
        "std_daily_tx_count",
        "std_daily_total_in",
        "std_daily_total_out",
        "std_daily_net_flow",
        "std_daily_total_flow",
        "in_active_days",
        "out_active_days",
        "both_active_days",
        "in_active_day_ratio",
        "out_active_day_ratio",
        "both_active_day_ratio",
        "in_out_day_balance",
        "tx_count_cv",
        "total_flow_cv",
        "tx_concentration_ratio",
        "flow_concentration_ratio",
    ]
    return wallet_agg[final_cols].copy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--daily-file", default="dataverse_files/wallet_daily_2022.csv")
    parser.add_argument("--cluster-file", default="dataverse_files/wallet_kmeans_clusters.csv")
    parser.add_argument("--output", default="dataverse_files/wallet_kmeans6_expanded_daily_features.csv")
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    args = parser.parse_args()

    labels = read_labels(args.cluster_file)
    agg, total_rows, kept_rows = aggregate_daily_features(args.daily_file, labels, args.chunksize)
    features = derive_features(agg)
    out = features.merge(labels[["wallet", "cluster"]], on="wallet", how="inner")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)

    summary = pd.DataFrame([{
        "daily_file": args.daily_file,
        "cluster_file": args.cluster_file,
        "output": str(output),
        "daily_rows_read": total_rows,
        "daily_rows_matching_cluster_wallets": kept_rows,
        "cluster_wallets": labels["wallet"].nunique(),
        "output_wallets": out["wallet"].nunique(),
        "feature_columns_excluding_wallet_cluster": len(out.columns) - 2,
    }])
    summary.to_csv(output.with_name(output.stem + "_build_summary.csv"), index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
