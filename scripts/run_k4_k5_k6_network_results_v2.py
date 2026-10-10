"""K4/K5/K6 full-month network validation for the paper fix pass.

This script follows the professor's requested replacement for the earlier
single-month / sampled-edge network test:

- process all twelve 2022 ERC-20 monthly TSV files,
- evaluate K4, K5, and K6 labels,
- keep all labelled sender-recipient edges,
- compare observed same-role transfer ratio to a shuffled-label null,
- report Holm-adjusted monthly p-values and Fisher combined p-values,
- build a full-year K5 observed/expected role-mixing matrix.

The default permutation count is intentionally small (B=99) for a quick
sanity run. Use --permutations 999 for final paper numbers.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run K4/K5/K6 monthly network null validation.")
    parser.add_argument("--raw-root", type=Path, default=ROOT.parent / "dataverse_files")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results_v2" / "network_k4_k5_k6")
    parser.add_argument("--months", nargs="*", default=[f"2022{m:02d}" for m in range(1, 13)])
    parser.add_argument("--permutations", type=int, default=99)
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--drop-self-transfers", action="store_true", default=True)
    return parser.parse_args()


def resolve_month_file(raw_root: Path, month: str) -> Path:
    candidates = [
        raw_root / f"{month}.tsv" / f"{month}.tsv",
        raw_root / f"{month}.tsv",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No TSV file found for {month} under {raw_root}")


def load_labels(k: int) -> pd.Series:
    path = ROOT / f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv"
    labels = pd.read_csv(path, dtype={"wallet": "string"})
    labels["wallet"] = labels["wallet"].str.strip().str.lower()
    return labels.drop_duplicates("wallet").set_index("wallet")["cluster"].astype(np.int16)


def holm_adjust(p_values: pd.Series) -> np.ndarray:
    p = p_values.to_numpy(dtype=float)
    m = len(p)
    order = np.argsort(p)
    adjusted_sorted = np.empty(m, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        value = (m - rank) * p[idx]
        running = max(running, value)
        adjusted_sorted[rank] = min(running, 1.0)
    out = np.empty(m, dtype=float)
    out[order] = adjusted_sorted
    return out


def fisher_combined_p(p_values: pd.Series) -> float:
    try:
        from scipy.stats import combine_pvalues

        return float(combine_pvalues(p_values.to_numpy(dtype=float), method="fisher")[1])
    except Exception:
        return float("nan")


def same_role_null(
    source_labels: np.ndarray,
    target_labels: np.ndarray,
    sender: pd.Series,
    recipient: pd.Series,
    rng: np.random.Generator,
    permutations: int,
) -> tuple[float, float, float, float]:
    observed = float(np.mean(source_labels == target_labels))

    endpoints = pd.concat([sender, recipient], ignore_index=True)
    unique_wallets = pd.Index(endpoints.unique())
    wallet_label_table = pd.concat(
        [
            pd.DataFrame({"wallet": sender.to_numpy(), "cluster": source_labels}),
            pd.DataFrame({"wallet": recipient.to_numpy(), "cluster": target_labels}),
        ],
        ignore_index=True,
    ).drop_duplicates("wallet")
    wallet_labels = (
        wallet_label_table.set_index("wallet").loc[unique_wallets, "cluster"].to_numpy(dtype=np.int16)
    )

    src_codes = unique_wallets.get_indexer(sender)
    dst_codes = unique_wallets.get_indexer(recipient)
    null = np.empty(permutations, dtype=np.float64)
    for i in range(permutations):
        shuffled = rng.permutation(wallet_labels)
        null[i] = np.mean(shuffled[src_codes] == shuffled[dst_codes])
    p_upper = float((1 + np.sum(null >= observed)) / (permutations + 1))
    return observed, float(null.mean()), float(null.std(ddof=1)), p_upper


def process_month(month: str, labels_by_k: dict[int, pd.Series], args: argparse.Namespace, rng: np.random.Generator):
    tsv_path = resolve_month_file(args.raw_root, month)
    print(f"Processing {month}: {tsv_path}", flush=True)

    month_edges: dict[int, dict[str, list]] = {
        k: {"sender": [], "recipient": [], "source": [], "target": []} for k in labels_by_k
    }
    adjacency_by_k = {
        k: pd.DataFrame(0, index=range(k), columns=range(k), dtype=np.int64) for k in labels_by_k
    }
    raw_rows = 0

    reader = pd.read_csv(
        tsv_path,
        sep="\t",
        usecols=["sender", "recipient"],
        dtype={"sender": "string", "recipient": "string"},
        chunksize=args.chunksize,
    )

    for chunk in reader:
        raw_rows += len(chunk)
        chunk["sender"] = chunk["sender"].str.strip().str.lower()
        chunk["recipient"] = chunk["recipient"].str.strip().str.lower()
        if args.drop_self_transfers:
            chunk = chunk[chunk["sender"] != chunk["recipient"]]
        if chunk.empty:
            continue

        for k, labels in labels_by_k.items():
            src = chunk["sender"].map(labels)
            dst = chunk["recipient"].map(labels)
            mask = src.notna() & dst.notna()
            if not mask.any():
                continue
            src_valid = src[mask].astype(np.int16).to_numpy()
            dst_valid = dst[mask].astype(np.int16).to_numpy()
            sender_valid = chunk.loc[mask, "sender"].copy()
            recipient_valid = chunk.loc[mask, "recipient"].copy()

            month_edges[k]["sender"].append(sender_valid)
            month_edges[k]["recipient"].append(recipient_valid)
            month_edges[k]["source"].append(src_valid)
            month_edges[k]["target"].append(dst_valid)

            pairs = pd.DataFrame({"source": src_valid, "target": dst_valid})
            counts = pairs.groupby(["source", "target"], observed=True).size()
            for (source, target), count in counts.items():
                adjacency_by_k[k].loc[int(source), int(target)] += int(count)

    rows = []
    for k in sorted(labels_by_k):
        if not month_edges[k]["source"]:
            raise ValueError(f"No labelled edges for K{k} in {month}")
        source_labels = np.concatenate(month_edges[k]["source"])
        target_labels = np.concatenate(month_edges[k]["target"])
        sender = pd.concat(month_edges[k]["sender"], ignore_index=True)
        recipient = pd.concat(month_edges[k]["recipient"], ignore_index=True)
        obs, null_mean, null_std, p = same_role_null(
            source_labels, target_labels, sender, recipient, rng, args.permutations
        )
        rows.append(
            {
                "month": month,
                "k": k,
                "raw_rows_read": raw_rows,
                "labelled_edges": len(source_labels),
                "coverage_ratio": len(source_labels) / raw_rows,
                "observed_same_role_ratio": obs,
                "null_mean": null_mean,
                "null_std": null_std,
                "observed_minus_null": obs - null_mean,
                "p_value_upper": p,
                "permutations": args.permutations,
            }
        )

    return rows, adjacency_by_k


def assortativity_from_mixing(matrix: pd.DataFrame) -> float:
    values = matrix.to_numpy(dtype=float)
    if values.sum() == 0:
        return float("nan")
    e = values / values.sum()
    expected_trace = float((e.sum(axis=1) * e.sum(axis=0)).sum())
    denom = 1 - expected_trace
    if denom == 0:
        return float("nan")
    return float((np.trace(e) - expected_trace) / denom)


def write_k5_mixing_figure(matrix: pd.DataFrame, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    expected = np.outer(matrix.sum(axis=1).to_numpy(), matrix.sum(axis=0).to_numpy()) / matrix.to_numpy().sum()
    ratio = np.log2(matrix.to_numpy(dtype=float) / expected)
    ratio[~np.isfinite(ratio)] = 0.0
    pd.DataFrame(ratio, index=matrix.index, columns=matrix.columns).to_csv(out_dir / "k5_full_year_log2_observed_expected_mixing.csv")

    fig, ax = plt.subplots(figsize=(5.2, 4.5))
    lim = float(np.nanmax(np.abs(ratio)))
    im = ax.imshow(ratio, cmap="RdBu_r", vmin=-lim, vmax=lim)
    for i in range(ratio.shape[0]):
        for j in range(ratio.shape[1]):
            ax.text(j, i, f"{ratio[i, j]:.2f}", ha="center", va="center", fontsize=8)
    names = [f"C{i}" for i in matrix.index]
    ax.set_xticks(range(len(names)), names)
    ax.set_yticks(range(len(names)), names)
    ax.set_xlabel("Recipient role")
    ax.set_ylabel("Sender role")
    ax.set_title("Behaviour K5 full-year role mixing")
    fig.colorbar(im, ax=ax, label="log2(observed / expected)")
    fig.tight_layout()
    fig.savefig(out_dir / "fig2_k5_full_year_observed_expected_mixing.pdf")
    fig.savefig(out_dir / "fig2_k5_full_year_observed_expected_mixing.png", dpi=220)
    plt.close(fig)


def write_monthly_figures(monthly: pd.DataFrame, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    k5 = monthly[monthly["k"] == 5].copy()
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot(k5["month"], k5["observed_same_role_ratio"], marker="o", label="Observed")
    ax.plot(k5["month"], k5["null_mean"], marker="o", label="Shuffled-label null mean")
    ax.set_ylabel("Same-role transfer ratio")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "fig3_k5_same_role_observed_vs_null.pdf")
    fig.savefig(out_dir / "fig3_k5_same_role_observed_vs_null.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot(k5["month"], k5["p_value_upper"], marker="o", label="p")
    ax.plot(k5["month"], k5["p_holm"], marker="s", label="Holm-adjusted p")
    ax.axhline(0.05, linestyle="--", color="red", linewidth=1, label="0.05")
    ax.set_ylabel("Upper-tail p-value")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "fig4_k5_network_p_values.pdf")
    fig.savefig(out_dir / "fig4_k5_network_p_values.png", dpi=220)
    plt.close(fig)


def write_report(monthly: pd.DataFrame, summary: pd.DataFrame, assortativity: float, out_dir: Path) -> None:
    lines = [
        "# Results V2 Network Validation: K4/K5/K6",
        "",
        "## What This Run Does",
        "",
        "This is the professor-requested replacement for the earlier sampled/single-month network test.",
        "It uses all labelled monthly sender-recipient edges, tests K4/K5/K6, applies Holm correction over the twelve monthly tests, and reports Fisher combined p-values.",
        "",
        "## K Summary",
        "",
        summary.to_markdown(index=False),
        "",
        f"Full-year K5 role assortativity from the pooled mixing matrix: `{assortativity:.4f}`.",
        "",
        "## Monthly Results",
        "",
        monthly.to_markdown(index=False),
    ]
    (out_dir / "network_results_v2_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    labels_by_k = {k: load_labels(k) for k in [4, 5, 6]}

    rows = []
    pooled_adjacency_by_k = {k: pd.DataFrame(0, index=range(k), columns=range(k), dtype=np.int64) for k in [4, 5, 6]}
    for month in args.months:
        month_rows, month_adjacency = process_month(month, labels_by_k, args, rng)
        rows.extend(month_rows)
        for k, adjacency in month_adjacency.items():
            adjacency.to_csv(args.out_dir / f"{month}_k{k}_adjacency_counts.csv")
            pooled_adjacency_by_k[k] = pooled_adjacency_by_k[k].add(adjacency, fill_value=0).astype(np.int64)

    monthly = pd.DataFrame(rows)
    monthly["p_holm"] = monthly.groupby("k", group_keys=False)["p_value_upper"].apply(
        lambda s: pd.Series(holm_adjust(s), index=s.index)
    )
    monthly.to_csv(args.out_dir / "network_monthly.csv", index=False)

    summary_rows = []
    for k, group in monthly.groupby("k"):
        summary_rows.append(
            {
                "k": int(k),
                "months": len(group),
                "significant_months_raw_p": int((group["p_value_upper"] < 0.05).sum()),
                "significant_months_holm": int((group["p_holm"] < 0.05).sum()),
                "mean_observed_minus_null": float(group["observed_minus_null"].mean()),
                "mean_observed_same_role_ratio": float(group["observed_same_role_ratio"].mean()),
                "mean_null_ratio": float(group["null_mean"].mean()),
                "fisher_combined_p": fisher_combined_p(group["p_value_upper"]),
                "permutations": int(group["permutations"].iloc[0]),
            }
        )
        pooled_adjacency_by_k[int(k)].to_csv(args.out_dir / f"k{k}_full_year_adjacency_counts.csv")

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(args.out_dir / "network_summary.csv", index=False)

    k5_assortativity = assortativity_from_mixing(pooled_adjacency_by_k[5])
    write_k5_mixing_figure(pooled_adjacency_by_k[5], args.out_dir)
    write_monthly_figures(monthly, args.out_dir)
    write_report(monthly, summary, k5_assortativity, args.out_dir)
    print(summary.to_string(index=False))
    print(f"K5 full-year assortativity: {k5_assortativity:.4f}")
    print(f"Saved network results to {args.out_dir}")


if __name__ == "__main__":
    main()
