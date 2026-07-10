import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add net flow to a wallet-daily CSV.")
    parser.add_argument(
        "--input-csv",
        default="data/processed/wallet_daily_merged.csv",
        help="Wallet-daily CSV with total_in and total_out columns.",
    )
    parser.add_argument(
        "--output-csv",
        default="data/processed/wallet_daily_merged_netflow.csv",
        help="Output CSV with net_flow added.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input_csv)
    df["total_in"] = pd.to_numeric(df["total_in"], errors="coerce").fillna(0.0)
    df["total_out"] = pd.to_numeric(df["total_out"], errors="coerce").fillna(0.0)
    df["net_flow"] = df["total_in"] - df["total_out"]

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Saved {output_csv}")


if __name__ == "__main__":
    main()
