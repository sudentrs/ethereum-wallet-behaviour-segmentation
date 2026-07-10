import argparse
import glob
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate wallet-direction rows into daily wallet flow totals."
    )
    parser.add_argument(
        "--input-glob",
        required=True,
        help="Glob for wallet-direction CSV files, for example data/interim/wallet_2022*.csv.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/wallet_daily",
        help="Directory for wallet-daily CSV outputs.",
    )
    return parser.parse_args()


def aggregate_file(input_path: Path, output_dir: Path) -> Path:
    print(f"Processing {input_path}")
    df = pd.read_csv(input_path)
    df["date"] = pd.to_datetime(df["time"], errors="coerce").dt.date
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0.0)
    df["in_value"] = df["value"].where(df["direction"] == "in", 0.0)
    df["out_value"] = df["value"].where(df["direction"] == "out", 0.0)

    wallet_daily = (
        df.groupby(["wallet", "date"], dropna=True)
        .agg(
            total_in=("in_value", "sum"),
            total_out=("out_value", "sum"),
            tx_count=("value", "count"),
        )
        .reset_index()
    )

    output_path = output_dir / f"{input_path.stem}_daily.csv"
    wallet_daily.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = [Path(path) for path in sorted(glob.glob(args.input_glob))]
    if not files:
        raise FileNotFoundError(f"No files matched --input-glob {args.input_glob!r}")

    for input_path in files:
        output_path = aggregate_file(input_path, output_dir)
        print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
