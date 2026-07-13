import argparse
from pathlib import Path

import pandas as pd


def normalize_address(value: object) -> str | None:
    text = str(value).strip().lower()
    if text.startswith("0x"):
        text = text[2:]
    if len(text) != 40:
        return None
    if any(ch not in "0123456789abcdef" for ch in text):
        return None
    return "0x" + text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter wallet feature rows to EOA-only rows using EOA/contract classifications."
    )
    parser.add_argument(
        "--features",
        required=True,
        help="Wallet-level feature CSV containing a wallet column.",
    )
    parser.add_argument(
        "--classifications",
        required=True,
        help="CSV containing wallet/address and account_type columns.",
    )
    parser.add_argument("--output", required=True, help="EOA-only feature CSV to write.")
    parser.add_argument(
        "--summary-output",
        default=None,
        help="Optional summary CSV. Defaults to <output stem>_summary.csv.",
    )
    parser.add_argument("--wallet-column", default="wallet")
    parser.add_argument("--account-type-column", default="account_type")
    parser.add_argument(
        "--chunksize",
        type=int,
        default=200_000,
        help="Feature rows to process at once. Lower this on low-RAM machines.",
    )
    parser.add_argument(
        "--allow-partial-coverage",
        action="store_true",
        help="Allow writing output even if some feature wallets have no classification.",
    )
    return parser.parse_args()


def classification_address_column(df: pd.DataFrame, wallet_column: str) -> str:
    if "address" in df.columns:
        return "address"
    if wallet_column in df.columns:
        return wallet_column
    raise ValueError(
        f"Classification file must contain either 'address' or '{wallet_column}'."
    )


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary_output = (
        Path(args.summary_output)
        if args.summary_output
        else output.with_name(output.stem + "_summary.csv")
    )

    header = pd.read_csv(args.classifications, nrows=0)
    cls_addr_col = "address" if "address" in header.columns else args.wallet_column
    usecols = [cls_addr_col, args.account_type_column]
    cls = pd.read_csv(args.classifications, usecols=usecols, dtype=str)
    if args.account_type_column not in cls.columns:
        raise ValueError(f"Missing classification column: {args.account_type_column}")
    cls_addr_col = classification_address_column(cls, args.wallet_column)
    cls["normalized_address"] = cls[cls_addr_col].map(normalize_address)
    cls = cls.dropna(subset=["normalized_address"]).copy()
    cls[args.account_type_column] = cls[args.account_type_column].str.strip().str.lower()
    cls = cls.drop_duplicates("normalized_address", keep="last")

    feature_header = pd.read_csv(args.features, nrows=0)
    if args.wallet_column not in feature_header.columns:
        raise ValueError(f"Missing feature wallet column: {args.wallet_column}")
    if output.exists():
        output.unlink()

    total_rows = 0
    classified_rows = 0
    missing_rows = 0
    eoa_rows = 0
    contract_rows = 0
    first_chunk = True

    cls_lookup = cls[["normalized_address", args.account_type_column]]
    feature_reader = pd.read_csv(
        args.features,
        dtype={args.wallet_column: str},
        chunksize=args.chunksize,
    )
    for chunk_id, features in enumerate(feature_reader, start=1):
        features["normalized_address"] = features[args.wallet_column].map(normalize_address)
        merged = features.merge(cls_lookup, on="normalized_address", how="left")

        missing = int(merged[args.account_type_column].isna().sum())
        eoa = merged[merged[args.account_type_column] == "eoa"].copy()
        contract = merged[merged[args.account_type_column] == "contract"]

        total_rows += len(merged)
        missing_rows += missing
        classified_rows += len(merged) - missing
        eoa_rows += len(eoa)
        contract_rows += len(contract)

        drop_cols = ["normalized_address", args.account_type_column]
        eoa.drop(columns=[c for c in drop_cols if c in eoa.columns]).to_csv(
            output,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
        )
        first_chunk = False

        print(
            f"chunk={chunk_id:03d} rows_read={total_rows:,} "
            f"eoa_written={eoa_rows:,} contracts_seen={contract_rows:,} "
            f"unclassified_seen={missing_rows:,}"
        )

    if missing_rows and not args.allow_partial_coverage:
        output.unlink(missing_ok=True)
        raise SystemExit(
            "Classification coverage is incomplete: "
            f"{missing_rows:,} of {total_rows:,} feature wallets are unclassified. "
            "Run full EOA/contract classification first, or pass "
            "--allow-partial-coverage only for exploratory checks."
        )

    summary = pd.DataFrame(
        [
            {
                "features_file": args.features,
                "classifications_file": args.classifications,
                "output_file": str(output),
                "feature_wallets": int(total_rows),
                "classified_wallets": int(classified_rows),
                "unclassified_wallets": int(missing_rows),
                "eoa_wallets": int(eoa_rows),
                "contract_wallets": int(contract_rows),
                "eoa_share_of_classified": float(
                    eoa_rows / max(eoa_rows + contract_rows, 1)
                ),
                "contract_share_of_classified": float(
                    contract_rows / max(eoa_rows + contract_rows, 1)
                ),
                "partial_coverage_allowed": bool(args.allow_partial_coverage),
                "chunksize": int(args.chunksize),
            }
        ]
    )
    summary.to_csv(summary_output, index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
