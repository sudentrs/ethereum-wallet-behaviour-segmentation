import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert raw transfer rows into wallet-direction rows."
    )
    parser.add_argument("--input-tsv", required=True, help="Path to raw monthly TSV file.")
    parser.add_argument(
        "--output-csv",
        default="data/interim/wallet_direction_rows.csv",
        help="Output CSV containing wallet, time, token, direction, and value.",
    )
    parser.add_argument("--chunk-size", type=int, default=100_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    first = True
    for chunk in pd.read_csv(args.input_tsv, sep="\t", chunksize=args.chunk_size, dtype=str):
        sender_df = pd.DataFrame(
            {
                "wallet": chunk["sender"],
                "time": chunk["time"],
                "token": chunk["token_symbol"],
                "direction": "out",
                "value": chunk["value"],
            }
        )
        recipient_df = pd.DataFrame(
            {
                "wallet": chunk["recipient"],
                "time": chunk["time"],
                "token": chunk["token_symbol"],
                "direction": "in",
                "value": chunk["value"],
            }
        )

        result = pd.concat([sender_df, recipient_df], ignore_index=True)
        result.to_csv(output_csv, mode="a", header=first, index=False)
        first = False

    print(f"Saved wallet-direction rows to {output_csv}")


if __name__ == "__main__":
    main()
