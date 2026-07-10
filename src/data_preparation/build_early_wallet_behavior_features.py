import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build early wallet-level behaviour features from wallet-daily flows."
    )
    parser.add_argument(
        "--input-csv",
        default="data/processed/wallet_daily_merged_netflow.csv",
        help="Wallet-daily CSV with wallet, date, total_in, total_out, tx_count, and net_flow.",
    )
    parser.add_argument(
        "--output-csv",
        default="data/processed/wallet_behavior_features.csv",
        help="Output wallet-level feature CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input_csv)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["total_in", "total_out", "tx_count", "net_flow"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    wallet_features = (
        df.groupby("wallet")
        .agg(
            active_days=("date", "nunique"),
            first_day=("date", "min"),
            last_day=("date", "max"),
            total_tx=("tx_count", "sum"),
            total_in=("total_in", "sum"),
            total_out=("total_out", "sum"),
            avg_tx_size=("net_flow", "mean"),
            flow_volatility=("net_flow", "std"),
            tx_size_volatility=("tx_count", "std"),
            mean_tx_daily=("tx_count", "mean"),
            std_tx_daily=("tx_count", "std"),
        )
        .reset_index()
    )

    wallet_features["activity_span"] = (
        wallet_features["last_day"] - wallet_features["first_day"]
    ).dt.days + 1
    wallet_features["activity_density"] = (
        wallet_features["active_days"] / wallet_features["activity_span"].replace(0, pd.NA)
    ).fillna(0)
    wallet_features["avg_tx_per_day"] = (
        wallet_features["total_tx"] / wallet_features["active_days"].replace(0, pd.NA)
    ).fillna(0)
    wallet_features["net_flow"] = wallet_features["total_in"] - wallet_features["total_out"]
    wallet_features["in_out_ratio"] = wallet_features["total_in"] / (wallet_features["total_out"] + 1)
    wallet_features["directionality"] = wallet_features["total_in"] / (
        wallet_features["total_in"] + wallet_features["total_out"] + 1
    )
    wallet_features["burstiness"] = (
        (wallet_features["std_tx_daily"] - wallet_features["mean_tx_daily"])
        / (wallet_features["std_tx_daily"] + wallet_features["mean_tx_daily"] + 1e-9)
    ).fillna(0)

    wallet_features = wallet_features.drop(
        columns=["first_day", "last_day", "mean_tx_daily", "std_tx_daily"]
    )

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    wallet_features.to_csv(output_csv, index=False)
    print(f"Saved {output_csv}")


if __name__ == "__main__":
    main()
