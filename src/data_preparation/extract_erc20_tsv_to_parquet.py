import pandas as pd
from pathlib import Path

# ==========================
# CONFIGURATION
# ==========================

INPUT_TSV = "202211.tsv"                 # CHANGE PER RUN
OUTPUT_DIR = "processed/202211"          # CHANGE PER RUN
CHUNK_SIZE = 500_000

DTYPES = {
    "block_id": "string",               # safer: cast later
    "transaction_hash": "string",
    "time": "string",
    "token_address": "string",
    "sender": "string",
    "recipient": "string",
    "value": "string",
    "token_name": "string",
    "token_symbol": "string",
    "token_decimals": "string"           # MUST be string initially
}

# ==========================
# PROCESSING FUNCTION
# ==========================

def process_chunk(df: pd.DataFrame) -> pd.DataFrame:
    # Parse timestamp
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")

    # Coerce numeric fields safely
    df["token_decimals"] = pd.to_numeric(
        df["token_decimals"], errors="coerce"
    )

    df["block_id"] = pd.to_numeric(
        df["block_id"], errors="coerce"
    )

    # Drop malformed rows
    df = df.dropna(subset=["time", "token_decimals", "block_id"])

    df["token_decimals"] = df["token_decimals"].astype(int)
    df["block_id"] = df["block_id"].astype("int64")

    # Normalize ERC-20 values safely (Python int)
    df["value_decimal"] = [
        int(v) / (10 ** d)
        for v, d in zip(df["value"], df["token_decimals"])
    ]

    # Keep only needed columns
    df = df[
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

    return df

# ==========================
# MAIN PIPELINE
# ==========================

def main():
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    chunk_id = 0

    for chunk in pd.read_csv(
        INPUT_TSV,
        sep="\t",
        chunksize=CHUNK_SIZE,
        dtype=DTYPES,
        on_bad_lines="skip",
        low_memory=False
    ):
        clean_chunk = process_chunk(chunk)

        out_file = output_dir / f"part_{chunk_id:05d}.parquet"
        clean_chunk.to_parquet(out_file, index=False)

        print(f"Processed {len(clean_chunk):,} rows → {out_file.name}")
        chunk_id += 1

    print("Processing completed successfully.")

if __name__ == "__main__":
    main()
