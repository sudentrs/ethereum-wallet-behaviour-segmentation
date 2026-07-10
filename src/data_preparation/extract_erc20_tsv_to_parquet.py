import argparse
from pathlib import Path

import pandas as pd


DTYPES = {
    "block_id": "string",
    "transaction_hash": "string",
    "time": "string",
    "token_address": "string",
    "sender": "string",
    "recipient": "string",
    "value": "string",
    "token_name": "string",
    "token_symbol": "string",
    "token_decimals": "string",
}


def process_chunk(df: pd.DataFrame) -> pd.DataFrame:
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df["token_decimals"] = pd.to_numeric(df["token_decimals"], errors="coerce")
    df["block_id"] = pd.to_numeric(df["block_id"], errors="coerce")
    df = df.dropna(subset=["time", "token_decimals", "block_id", "value"])

    df["token_decimals"] = df["token_decimals"].astype(int)
    df["block_id"] = df["block_id"].astype("int64")

    df["value_decimal"] = [
        int(value) / (10 ** decimals)
        for value, decimals in zip(df["value"], df["token_decimals"])
    ]

    return df[
        [
            "block_id",
            "time",
            "transaction_hash",
            "token_address",
            "token_symbol",
            "sender",
            "recipient",
            "value_decimal",
        ]
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean a raw monthly ERC-20 TSV file into parquet chunks."
    )
    parser.add_argument("--input-tsv", required=True, help="Path to a raw monthly TSV file.")
    parser.add_argument(
        "--output-dir",
        default="data/interim/erc20_parquet",
        help="Directory where cleaned parquet chunks will be written.",
    )
    parser.add_argument("--chunk-size", type=int, default=500_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_tsv = Path(args.input_tsv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for chunk_id, chunk in enumerate(
        pd.read_csv(
            input_tsv,
            sep="\t",
            chunksize=args.chunk_size,
            dtype=DTYPES,
            on_bad_lines="skip",
            low_memory=False,
        )
    ):
        clean_chunk = process_chunk(chunk)
        out_file = output_dir / f"part_{chunk_id:05d}.parquet"
        clean_chunk.to_parquet(out_file, index=False)
        print(f"Processed {len(clean_chunk):,} rows -> {out_file}")

    print("Processing completed successfully.")


if __name__ == "__main__":
    main()
