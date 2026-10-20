"""Run month-by-month transaction-network null validation for EOA labels.

This script repeats the same-role transaction concentration test across
available monthly ERC-20 TSV files. It is intended to replace a single-month
network snapshot claim with a time-aware robustness check.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate cluster-label network homophily across monthly ERC-20 transfer files."
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path("results/eoa_only_kmeans5/wallet_eoa_only_kmeans_clusters.csv"),
        help="CSV with wallet and cluster columns.",
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("../dataverse_files"),
        help="Directory containing YYYYMM.tsv/YYYYMM.tsv monthly transfer files.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/eoa_only_kmeans5/network_validation_monthly"),
        help="Output directory for monthly validation tables.",
    )
    parser.add_argument(
        "--months",
        nargs="*",
        default=[f"2022{month:02d}" for month in range(1, 13)],
        help="Months to process, formatted as YYYYMM.",
    )
    parser.add_argument("--sample-edges", type=int, default=200_000)
    parser.add_argument("--permutations", type=int, default=100)
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=492)
    return parser.parse_args()


def resolve_month_file(raw_root: Path, month: str) -> Path:
    candidates = [
        raw_root / f"{month}.tsv" / f"{month}.tsv",
        raw_root / f"{month}.tsv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No TSV found for {month} under {raw_root}")


def load_labels(path: Path) -> pd.Series:
    labels = pd.read_csv(path, dtype={"wallet": "string"})
    if not {"wallet", "cluster"}.issubset(labels.columns):
        raise ValueError(f"{path} must contain wallet and cluster columns")
    labels["wallet"] = labels["wallet"].str.lower()
    return labels.set_index("wallet")["cluster"].astype("int16")


def update_sample(
    sample: pd.DataFrame,
    sender: pd.Series,
    recipient: pd.Series,
    src: np.ndarray,
    dst: np.ndarray,
    rng: np.random.Generator,
    sample_edges: int,
) -> pd.DataFrame:
    if len(src) == 0:
        return sample
    chunk_sample = pd.DataFrame(
        {
            "score": rng.random(len(src)),
            "sender": sender.astype("string").to_numpy(),
            "recipient": recipient.astype("string").to_numpy(),
            "source_cluster": src.astype(np.int16, copy=False),
            "target_cluster": dst.astype(np.int16, copy=False),
        }
    )
    if sample.empty:
        combined = chunk_sample
    else:
        combined = pd.concat([sample, chunk_sample], ignore_index=True)
    if len(combined) > sample_edges:
        combined = combined.nsmallest(sample_edges, "score")
    return combined.reset_index(drop=True)


def null_test(sample: pd.DataFrame, rng: np.random.Generator, permutations: int) -> tuple[float, float, float, float]:
    observed = float((sample["source_cluster"].to_numpy() == sample["target_cluster"].to_numpy()).mean())
    endpoints = pd.concat([sample["sender"], sample["recipient"]], ignore_index=True)
    unique_wallets = pd.Index(endpoints.unique())
    wallet_labels = (
        pd.concat(
            [
                sample[["sender", "source_cluster"]].rename(columns={"sender": "wallet", "source_cluster": "cluster"}),
                sample[["recipient", "target_cluster"]].rename(columns={"recipient": "wallet", "target_cluster": "cluster"}),
            ],
            ignore_index=True,
        )
        .drop_duplicates("wallet")
        .set_index("wallet")
        .loc[unique_wallets, "cluster"]
        .to_numpy(dtype=np.int16)
    )
    sender_codes = unique_wallets.get_indexer(sample["sender"])
    recipient_codes = unique_wallets.get_indexer(sample["recipient"])
    null_values = np.empty(permutations, dtype=float)
    for i in range(permutations):
        shuffled_labels = rng.permutation(wallet_labels)
        null_values[i] = np.mean(shuffled_labels[sender_codes] == shuffled_labels[recipient_codes])
    p_upper = float((np.sum(null_values >= observed) + 1) / (permutations + 1))
    return observed, float(null_values.mean()), float(null_values.std(ddof=1)), p_upper


def process_month(
    month: str,
    tsv_path: Path,
    labels: pd.Series,
    args: argparse.Namespace,
    rng: np.random.Generator,
) -> tuple[dict[str, object], pd.DataFrame]:
    k_values = sorted(int(v) for v in labels.unique())
    adjacency = pd.DataFrame(0, index=k_values, columns=k_values, dtype=np.int64)
    sample = pd.DataFrame(columns=["score", "sender", "recipient", "source_cluster", "target_cluster"])

    raw_rows = 0
    labelled_rows = 0
    exact_same = 0

    reader = pd.read_csv(
        tsv_path,
        sep="\t",
        usecols=["sender", "recipient"],
        dtype={"sender": "string", "recipient": "string"},
        chunksize=args.chunksize,
    )
    for chunk in reader:
        raw_rows += len(chunk)
        chunk["sender"] = chunk["sender"].str.lower()
        chunk["recipient"] = chunk["recipient"].str.lower()
        src = chunk["sender"].map(labels)
        dst = chunk["recipient"].map(labels)
        mask = src.notna() & dst.notna()
        if not mask.any():
            continue

        src_valid = src[mask].astype("int16").to_numpy()
        dst_valid = dst[mask].astype("int16").to_numpy()
        labelled_rows += len(src_valid)
        exact_same += int(np.sum(src_valid == dst_valid))

        pairs = pd.DataFrame({"source_cluster": src_valid, "target_cluster": dst_valid})
        counts = pairs.groupby(["source_cluster", "target_cluster"], observed=True).size()
        for (source_cluster, target_cluster), count in counts.items():
            adjacency.loc[int(source_cluster), int(target_cluster)] += int(count)

        sample = update_sample(
            sample,
            chunk.loc[mask, "sender"],
            chunk.loc[mask, "recipient"],
            src_valid,
            dst_valid,
            rng,
            args.sample_edges,
        )

    if labelled_rows == 0:
        raise ValueError(f"No labelled edges found for {month}")

    observed_sample, null_mean, null_std, p_upper = null_test(sample, rng, args.permutations)
    summary = {
        "month": month,
        "raw_rows_read": raw_rows,
        "rows_with_both_cluster_labels": labelled_rows,
        "coverage_ratio": labelled_rows / raw_rows,
        "exact_same_cluster_edges": exact_same,
        "exact_same_cluster_ratio": exact_same / labelled_rows,
        "sample_edges": len(sample),
        "observed_sample_same_cluster_ratio": observed_sample,
        "null_mean": null_mean,
        "null_std": null_std,
        "p_value_upper": p_upper,
    }
    return summary, adjacency


def write_report(summary: pd.DataFrame, out_dir: Path, label_name: str) -> None:
    supportive = int((summary["p_value_upper"] < 0.05).sum())
    months = len(summary)
    lines = [
        f"# Monthly Network Null Validation ({label_name})",
        "",
        "## Purpose",
        "",
        "This report repeats the same-role transaction concentration test across monthly ERC-20 transfer snapshots.",
        "The null model keeps sampled transaction edges fixed and randomly permutes cluster labels across the unique wallets appearing in those sampled edges.",
        "",
        "## Summary",
        "",
        f"- Months processed: `{months}`.",
        f"- Months with upper-tail p-value below 0.05: `{supportive}`.",
        f"- Mean observed same-cluster ratio: `{summary['observed_sample_same_cluster_ratio'].mean():.4f}`.",
        f"- Mean null same-cluster ratio: `{summary['null_mean'].mean():.4f}`.",
        f"- Mean observed-minus-null difference: `{(summary['observed_sample_same_cluster_ratio'] - summary['null_mean']).mean():.4f}`.",
        "",
        "## Monthly Results",
        "",
        summary.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "A low upper-tail p-value means the observed same-cluster transaction ratio is higher than expected under shuffled labels.",
        "A non-significant p-value means same-labelled wallets do not transact with one another more often than the shuffled-label baseline for that month.",
        "This test evaluates network homophily only; it does not test whether feature-space roles are interpretable or temporally persistent.",
    ]
    (out_dir / "monthly_network_null_validation_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_figures(summary: pd.DataFrame, out_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    figures = out_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    months = summary["month"].astype(str).tolist()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(months, summary["observed_sample_same_cluster_ratio"], marker="o", label="Observed")
    ax.plot(months, summary["null_mean"], marker="o", label="Shuffled-label null mean")
    ax.set_xlabel("Month")
    ax.set_ylabel("Same-cluster transaction ratio")
    ax.set_title("Monthly K5 same-cluster transaction concentration")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "monthly_observed_vs_null_same_cluster_ratio.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(months, summary["p_value_upper"], marker="o", color="#7a3db8")
    ax.axhline(0.05, color="#b03a2e", linestyle="--", linewidth=1, label="0.05 threshold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Upper-tail p-value")
    ax.set_title("Monthly shuffled-label null-test p-values")
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(0, 1.05)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "monthly_network_null_p_values.png", dpi=200)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    labels = load_labels(args.labels)
    rng = np.random.default_rng(args.seed)

    summaries = []
    for month in args.months:
        tsv_path = resolve_month_file(args.raw_root, month)
        print(f"Processing {month}: {tsv_path}", flush=True)
        summary, adjacency = process_month(month, tsv_path, labels, args, rng)
        summaries.append(summary)
        adjacency.to_csv(args.out_dir / f"{month}_cluster_adjacency_tx_counts.csv")

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(args.out_dir / "monthly_network_validation_summary.csv", index=False)
    write_report(summary_df, args.out_dir, args.labels.parent.name)
    write_figures(summary_df, args.out_dir)


if __name__ == "__main__":
    main()
