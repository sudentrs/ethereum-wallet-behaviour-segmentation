import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


def load_labels(path: str, cluster_col: str, label_name: str) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=["wallet", cluster_col], dtype={"wallet": str})
    df["wallet"] = df["wallet"].astype("string").str.strip().str.lower()
    df[cluster_col] = df[cluster_col].astype(int)
    return df.rename(columns={cluster_col: label_name}).drop_duplicates("wallet")


def hungarian_matches(crosstab: pd.DataFrame, left_name: str, right_name: str) -> pd.DataFrame:
    cost = -crosstab.to_numpy()
    row_ind, col_ind = linear_sum_assignment(cost)
    total = int(crosstab.to_numpy().sum())
    rows = []
    for r, c in zip(row_ind, col_ind):
        matched = int(crosstab.iloc[r, c])
        left_total = int(crosstab.iloc[r, :].sum())
        right_total = int(crosstab.iloc[:, c].sum())
        rows.append(
            {
                left_name: int(crosstab.index[r]),
                right_name: int(crosstab.columns[c]),
                "matched_wallets": matched,
                f"share_of_{left_name}": matched / left_total if left_total else 0,
                f"share_of_{right_name}": matched / right_total if right_total else 0,
                "share_of_all_wallets": matched / total if total else 0,
            }
        )
    return pd.DataFrame(rows).sort_values(left_name)


def plot_heatmap(matrix: pd.DataFrame, out_path: Path, title: str, fmt: str = ".2f") -> None:
    data = matrix.to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(8, 5.6))
    im = ax.imshow(data, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_yticks(range(len(matrix.index)))
    ax.set_xticklabels([f"K6-C{c}" for c in matrix.columns])
    ax.set_yticklabels([f"K5-C{i}" for i in matrix.index])
    ax.set_xlabel("EOA-only k=6 cluster")
    ax.set_ylabel("EOA-only k=5 cluster")
    ax.set_title(title)
    max_val = np.nanmax(data) if data.size else 0
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            color = "white" if max_val and val < max_val * 0.65 else "black"
            ax.text(j, i, format(val, fmt), ha="center", va="center", color=color, fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.85)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_cluster_sizes(k5_sizes: pd.DataFrame, k6_sizes: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, sizes, title in [
        (axes[0], k5_sizes, "EOA-only k=5"),
        (axes[1], k6_sizes, "EOA-only k=6"),
    ]:
        sizes = sizes.sort_values("cluster")
        ax.bar([f"C{c}" for c in sizes["cluster"]], sizes["wallet_share"], color="#4c78a8")
        ax.set_title(title)
        ax.set_xlabel("Cluster")
        ax.set_ylim(0, max(k5_sizes["wallet_share"].max(), k6_sizes["wallet_share"].max()) * 1.15)
        for idx, row in sizes.iterrows():
            ax.text(
                f"C{int(row['cluster'])}",
                row["wallet_share"] + 0.005,
                f"{row['wallet_share']:.1%}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    axes[0].set_ylabel("Wallet share")
    fig.suptitle("Cluster Size Balance After Contract Removal")
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_profile_heatmap(profile_path: str, out_path: Path, title: str) -> None:
    profiles = pd.read_csv(profile_path).set_index("cluster")
    fig, ax = plt.subplots(figsize=(13, 4.8))
    data = profiles.to_numpy(dtype=float)
    im = ax.imshow(data, cmap="coolwarm", aspect="auto", vmin=-2.5, vmax=2.5)
    ax.set_yticks(range(len(profiles.index)))
    ax.set_yticklabels([f"C{int(c)}" for c in profiles.index])
    ax.set_xticks(range(len(profiles.columns)))
    ax.set_xticklabels(profiles.columns, rotation=70, ha="right", fontsize=7)
    ax.set_title(title)
    ax.set_ylabel("Cluster")
    fig.colorbar(im, ax=ax, shrink=0.85, label="Median robust-scaled feature value")
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_k_sensitivity(path: str, out_path: Path) -> None:
    summary = pd.read_csv(path).sort_values("k")
    fig, ax1 = plt.subplots(figsize=(8.5, 4.8))
    ax1.plot(summary["k"], summary["silhouette_mean"], marker="o", label="Silhouette", color="#4c78a8")
    ax1.set_xlabel("k")
    ax1.set_ylabel("Silhouette mean", color="#4c78a8")
    ax1.tick_params(axis="y", labelcolor="#4c78a8")
    ax2 = ax1.twinx()
    ax2.plot(summary["k"], summary["stability_ari_mean"], marker="s", label="ARI stability", color="#f58518")
    ax2.set_ylabel("Seed stability ARI mean", color="#f58518")
    ax2.tick_params(axis="y", labelcolor="#f58518")
    ax1.axvline(5, color="#54a24b", linestyle="--", linewidth=1)
    ax1.axvline(6, color="#e45756", linestyle="--", linewidth=1)
    ax1.set_title("EOA-Only K Sensitivity: k=5 vs k=6")
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare EOA-only k=5 and k=6 clustering outputs.")
    parser.add_argument("--k5-labels", required=True)
    parser.add_argument("--k6-features", required=True, help="Feature CSV containing wallet and k=6 cluster column.")
    parser.add_argument("--k5-sizes", required=True)
    parser.add_argument("--k6-sizes", required=True)
    parser.add_argument("--k5-profiles", required=True)
    parser.add_argument("--k6-profiles", required=True)
    parser.add_argument("--k-sensitivity-summary", required=True)
    parser.add_argument("--out-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(exist_ok=True)

    k5 = load_labels(args.k5_labels, "cluster", "k5_cluster")
    k6 = load_labels(args.k6_features, "cluster", "k6_cluster")
    overlap = k5.merge(k6, on="wallet", how="inner")

    crosstab = pd.crosstab(overlap["k5_cluster"], overlap["k6_cluster"])
    row_share = crosstab.div(crosstab.sum(axis=1), axis=0)
    col_share = crosstab.div(crosstab.sum(axis=0), axis=1)
    matches = hungarian_matches(crosstab, "k5_cluster", "k6_cluster")
    ari = adjusted_rand_score(overlap["k5_cluster"], overlap["k6_cluster"])
    nmi = normalized_mutual_info_score(overlap["k5_cluster"], overlap["k6_cluster"])
    matched = int(matches["matched_wallets"].sum())

    summary = pd.DataFrame(
        [
            {
                "overlapping_wallets": len(overlap),
                "hungarian_matched_wallets": matched,
                "hungarian_matched_share": matched / len(overlap),
                "adjusted_rand_index": ari,
                "normalized_mutual_information": nmi,
            }
        ]
    )

    crosstab.to_csv(out_dir / "k5_to_k6_crosstab_counts.csv")
    row_share.to_csv(out_dir / "k5_to_k6_crosstab_row_share.csv")
    col_share.to_csv(out_dir / "k5_to_k6_crosstab_col_share.csv")
    matches.to_csv(out_dir / "k5_to_k6_hungarian_matches.csv", index=False)
    summary.to_csv(out_dir / "k5_vs_k6_comparison_summary.csv", index=False)

    plot_heatmap(row_share, fig_dir / "k5_to_k6_row_share_heatmap.png", "K5 to K6 Row-Share Correspondence")
    plot_cluster_sizes(pd.read_csv(args.k5_sizes), pd.read_csv(args.k6_sizes), fig_dir / "k5_k6_cluster_size_comparison.png")
    plot_profile_heatmap(args.k5_profiles, fig_dir / "k5_profile_heatmap.png", "EOA-Only K5 Cluster Profiles")
    plot_profile_heatmap(args.k6_profiles, fig_dir / "k6_profile_heatmap.png", "EOA-Only K6 Cluster Profiles")
    plot_k_sensitivity(args.k_sensitivity_summary, fig_dir / "k_sensitivity_k5_k6.png")

    lines = [
        "# EOA-Only K5 vs K6 Comparison",
        "",
        "This report compares the post-Gate-1 EOA-only `k=5` and `k=6` clusterings.",
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Hungarian Matches",
        "",
        matches.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "`k=5` and `k=6` are related but not identical. Use this comparison to identify whether the sixth cluster is a stable added role or a split of an existing broader role.",
        "",
        "The final paper should not select `k=6` only because it was used before Gate 1. Selection should combine interpretability, stability, transaction-graph validation, and temporal persistence.",
        "",
        "## Visual Outputs",
        "",
        "- `figures/k5_to_k6_row_share_heatmap.png`",
        "- `figures/k5_k6_cluster_size_comparison.png`",
        "- `figures/k5_profile_heatmap.png`",
        "- `figures/k6_profile_heatmap.png`",
        "- `figures/k_sensitivity_k5_k6.png`",
    ]
    (out_dir / "k5_vs_k6_comparison_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"Saved comparison outputs to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
