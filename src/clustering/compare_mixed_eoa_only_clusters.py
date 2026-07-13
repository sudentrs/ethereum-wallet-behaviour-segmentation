import argparse
from pathlib import Path

import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


def clean_wallet(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def load_labels(path: str, wallet_col: str, cluster_col: str, label_name: str) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=[wallet_col, cluster_col], dtype={wallet_col: str})
    df = df.dropna(subset=[wallet_col, cluster_col]).copy()
    df[wallet_col] = clean_wallet(df[wallet_col])
    df[cluster_col] = df[cluster_col].astype(int)
    df = df.drop_duplicates(wallet_col)
    return df.rename(columns={wallet_col: "wallet", cluster_col: label_name})


def load_account_types(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=["wallet", "account_type"], dtype={"wallet": str})
    df["wallet"] = clean_wallet(df["wallet"])
    df["account_type"] = df["account_type"].astype("string").str.strip().str.lower()
    return df.drop_duplicates("wallet")


def best_overlap(crosstab: pd.DataFrame) -> pd.DataFrame:
    cost = -crosstab.to_numpy()
    row_ind, col_ind = linear_sum_assignment(cost)
    rows = []
    total = crosstab.to_numpy().sum()
    for row_idx, col_idx in zip(row_ind, col_ind):
        matched = int(crosstab.iloc[row_idx, col_idx])
        mixed_total = int(crosstab.iloc[row_idx, :].sum())
        eoa_total = int(crosstab.iloc[:, col_idx].sum())
        rows.append(
            {
                "mixed_cluster": int(crosstab.index[row_idx]),
                "eoa_only_cluster": int(crosstab.columns[col_idx]),
                "matched_wallets": matched,
                "share_of_mixed_cluster_eoas": matched / mixed_total if mixed_total else 0,
                "share_of_eoa_only_cluster": matched / eoa_total if eoa_total else 0,
                "share_of_all_overlapping_eoas": matched / total if total else 0,
            }
        )
    return pd.DataFrame(rows).sort_values("mixed_cluster")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare pre-Gate-1 mixed KMeans labels with post-Gate-1 EOA-only KMeans labels."
    )
    parser.add_argument("--mixed-labels", required=True)
    parser.add_argument("--eoa-labels", required=True)
    parser.add_argument("--classifications", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--wallet-column", default="wallet")
    parser.add_argument("--cluster-column", default="cluster")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mixed = load_labels(args.mixed_labels, args.wallet_column, args.cluster_column, "mixed_cluster")
    eoa = load_labels(args.eoa_labels, args.wallet_column, args.cluster_column, "eoa_only_cluster")
    account_types = load_account_types(args.classifications)

    mixed_with_type = mixed.merge(account_types, on="wallet", how="left")
    contamination = (
        mixed_with_type.groupby("mixed_cluster")
        .agg(
            mixed_wallets=("wallet", "nunique"),
            classified_wallets=("account_type", lambda s: int(s.notna().sum())),
            eoa_wallets=("account_type", lambda s: int((s == "eoa").sum())),
            contract_wallets=("account_type", lambda s: int((s == "contract").sum())),
        )
        .reset_index()
    )
    contamination["contract_share"] = (
        contamination["contract_wallets"] / contamination["classified_wallets"].replace(0, pd.NA)
    ).fillna(0)
    contamination["eoa_share"] = (
        contamination["eoa_wallets"] / contamination["classified_wallets"].replace(0, pd.NA)
    ).fillna(0)
    contamination.to_csv(out_dir / "mixed_cluster_eoa_contract_composition.csv", index=False)

    overlap = mixed.merge(eoa, on="wallet", how="inner")
    crosstab_counts = pd.crosstab(overlap["mixed_cluster"], overlap["eoa_only_cluster"])
    crosstab_counts.to_csv(out_dir / "mixed_to_eoa_only_crosstab_counts.csv")
    crosstab_row_share = crosstab_counts.div(crosstab_counts.sum(axis=1), axis=0)
    crosstab_row_share.to_csv(out_dir / "mixed_to_eoa_only_crosstab_row_share.csv")

    matches = best_overlap(crosstab_counts)
    matches.to_csv(out_dir / "mixed_to_eoa_only_hungarian_matches.csv", index=False)

    ari = adjusted_rand_score(overlap["mixed_cluster"], overlap["eoa_only_cluster"])
    nmi = normalized_mutual_info_score(overlap["mixed_cluster"], overlap["eoa_only_cluster"])
    matched_total = int(matches["matched_wallets"].sum())
    total_overlap = int(len(overlap))
    summary = pd.DataFrame(
        [
            {
                "mixed_wallets": int(mixed["wallet"].nunique()),
                "eoa_only_wallets": int(eoa["wallet"].nunique()),
                "overlapping_eoa_wallets": total_overlap,
                "matched_wallets_hungarian": matched_total,
                "matched_share_hungarian": matched_total / total_overlap if total_overlap else 0,
                "adjusted_rand_index": ari,
                "normalized_mutual_information": nmi,
            }
        ]
    )
    summary.to_csv(out_dir / "mixed_to_eoa_only_comparison_summary.csv", index=False)

    top_destinations = []
    for mixed_cluster, row in crosstab_row_share.iterrows():
        top = row.sort_values(ascending=False).head(3)
        top_destinations.append(
            {
                "mixed_cluster": int(mixed_cluster),
                "top_eoa_only_destinations": "; ".join(
                    f"C{int(cluster)}={share:.3f}" for cluster, share in top.items()
                ),
            }
        )
    top_destinations = pd.DataFrame(top_destinations)
    top_destinations.to_csv(out_dir / "mixed_cluster_top_eoa_only_destinations.csv", index=False)

    lines = [
        "# Mixed vs EOA-Only Cluster Comparison",
        "",
        "This report compares the pre-Gate-1 mixed-address KMeans6 labels with the post-Gate-1 EOA-only KMeans6 labels on overlapping EOA wallets.",
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Mixed Cluster EOA/Contract Composition",
        "",
        contamination.to_markdown(index=False),
        "",
        "## Hungarian Matches",
        "",
        matches.to_markdown(index=False),
        "",
        "## Top EOA-Only Destinations By Mixed Cluster",
        "",
        top_destinations.to_markdown(index=False),
        "",
        "## Interpretation Note",
        "",
        "Cluster IDs are not semantic identities across reruns. Use the Hungarian matches and row-share crosstab to discuss which mixed clusters are preserved, split, or reorganized after contract addresses are removed.",
    ]
    (out_dir / "mixed_to_eoa_only_comparison_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(summary.to_string(index=False))
    print(f"Saved comparison outputs to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
