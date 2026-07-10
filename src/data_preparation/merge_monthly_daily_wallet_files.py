import argparse
import glob
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge wallet-daily CSV files.")
    parser.add_argument(
        "--input-glob",
        required=True,
        help="Glob for wallet-daily CSV files, for example data/processed/wallet_daily/*_daily.csv.",
    )
    parser.add_argument(
        "--output-csv",
        default="data/processed/wallet_daily_merged.csv",
        help="Merged wallet-daily output CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    files = [Path(path) for path in sorted(glob.glob(args.input_glob))]
    if not files:
        raise FileNotFoundError(f"No files matched --input-glob {args.input_glob!r}")

    frames = []
    for path in files:
        print(f"Loading {path}")
        frames.append(pd.read_csv(path))

    merged = pd.concat(frames, ignore_index=True)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_csv, index=False)
    print(f"Saved {output_csv}")


if __name__ == "__main__":
    main()
