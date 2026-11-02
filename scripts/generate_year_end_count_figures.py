"""Generate compact manuscript figures for the year-end code-free count/activity cohort."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annual-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    runs = pd.read_csv(args.annual_dir / "annual_fit_runs.csv")
    stability = pd.read_csv(args.annual_dir / "annual_seed_stability.csv")
    profiles = pd.read_csv(args.annual_dir / "profiles_k3" / "annual_exact_raw_profiles_seed492_k3.csv")

    reference = runs[runs["seed"] == 492].sort_values("k")
    fig, axes = plt.subplots(1, 2, figsize=(8.3, 3.15))
    axes[0].plot(reference["k"], reference["silhouette"], marker="o", color="#176b87")
    axes[0].set(xlabel="Number of clusters ($k$)", ylabel="Silhouette (5,000-wallet sample)")
    axes[0].set_xticks(reference["k"])
    axes[0].grid(axis="y", alpha=.25)
    spread = runs.groupby("k")[["min_cluster_share", "max_cluster_share"]].agg(["min", "max"])
    axes[1].fill_between(spread.index, spread[("min_cluster_share", "min")],
                         spread[("min_cluster_share", "max")], alpha=.2, color="#cf5c36",
                         label="smallest-cluster share across seeds")
    axes[1].plot(spread.index, spread[("max_cluster_share", "min")], color="#cf5c36", marker="o",
                 label="largest-cluster share (lower bound)")
    axes[1].set(xlabel="Number of clusters ($k$)", ylabel="Cluster share")
    axes[1].set_xticks(reference["k"])
    axes[1].set_ylim(0, 1)
    axes[1].grid(axis="y", alpha=.25)
    axes[1].legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(args.out_dir / "annual_model_resolution.pdf", bbox_inches="tight")
    fig.savefig(args.out_dir / "annual_model_resolution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    grouped = stability.groupby("k")[["ari", "nmi", "hungarian_agreement"]]
    summary = grouped.agg(["min", "max", "mean"])
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    x = np.arange(len(summary.index))
    for col, color, marker in [("ari", "#176b87", "o"), ("nmi", "#cf5c36", "s"),
                               ("hungarian_agreement", "#5d8a3c", "^")]:
        y = summary[(col, "mean")].to_numpy()
        lo = y - summary[(col, "min")].to_numpy()
        hi = summary[(col, "max")].to_numpy() - y
        ax.errorbar(x, y, yerr=np.vstack([lo, hi]), marker=marker, capsize=3,
                    color=color, label=col.replace("_", " ").title())
    ax.set(xticks=x, xticklabels=[str(k) for k in summary.index], ylim=(0, 1),
           xlabel="Number of clusters ($k$)", ylabel="Across-seed agreement")
    ax.grid(axis="y", alpha=.25)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(args.out_dir / "annual_seed_stability.pdf", bbox_inches="tight")
    fig.savefig(args.out_dir / "annual_seed_stability.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    selected = ["active_days_observed", "activity_span_days", "activity_density", "total_tx",
                "avg_daily_tx_count", "tx_concentration_ratio"]
    med = profiles[profiles["feature"].isin(selected)].pivot(index="feature", columns="cluster", values="median")
    med = med.loc[selected]
    display = np.log1p(med[[0, 1, 2]])
    fig, ax = plt.subplots(figsize=(7.0, 3.7))
    x = np.arange(len(display.index))
    width = .24
    labels = ["Sustained activity", "Distributed lower activity", "Short-span concentrated"]
    colors = ["#176b87", "#cf5c36", "#5d8a3c"]
    for j, (cluster, label, color) in enumerate(zip([0, 1, 2], labels, colors)):
        ax.bar(x + (j - 1) * width, display[cluster], width=width, label=label, color=color)
    ax.set(xticks=x, xticklabels=[name.replace("_", " ") for name in display.index],
           ylabel="log(1 + median feature value)")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(fontsize=7, frameon=False)
    ax.grid(axis="y", alpha=.25)
    fig.tight_layout()
    fig.savefig(args.out_dir / "k3_count_activity_profiles.pdf", bbox_inches="tight")
    fig.savefig(args.out_dir / "k3_count_activity_profiles.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
