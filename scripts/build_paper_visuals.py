"""Collect and generate paper-ready visuals for the Ethereum wallet paper."""

from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results_v2" / "paper_visuals"


def copy_existing() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    mappings = {
        ROOT / "results_v2/network_k4_k5_k6_B999/fig2_k5_full_year_observed_expected_mixing": "fig2_k5_full_year_observed_expected_mixing",
        ROOT / "results_v2/network_k4_k5_k6_B999/fig3_k5_same_role_observed_vs_null": "fig3_k5_same_role_observed_vs_null",
        ROOT / "results_v2/network_k4_k5_k6_B999/fig4_k5_network_p_values": "fig4_k5_network_p_values",
        ROOT / "results_v2/feature_role_checks/k5_profile_heatmap": "fig_k5_profile_heatmap",
        ROOT / "results_v2/feature_role_checks/k4_profile_heatmap": "appendix_k4_profile_heatmap",
        ROOT / "results_v2/feature_role_checks/k6_profile_heatmap": "appendix_k6_profile_heatmap",
    }
    copied = []
    for src_stem, out_stem in mappings.items():
        for suffix in [".pdf", ".png"]:
            src = src_stem.with_suffix(suffix)
            if src.exists():
                dst = OUT / f"{out_stem}{suffix}"
                shutil.copy2(src, dst)
                copied.append(dst)
    return copied


def save_k5_transition_heatmap() -> list[Path]:
    transitions = pd.read_csv(ROOT / "results_v2/temporal_k4_k5_k6/transition_matrix.csv")
    k5 = transitions[transitions["k"] == 5]
    matrix = k5.pivot(index="from_state", columns="to_state", values="probability").sort_index().sort_index(axis=1)

    fig, ax = plt.subplots(figsize=(5.4, 4.6), constrained_layout=True)
    im = ax.imshow(matrix.to_numpy(), cmap="Blues", vmin=0, vmax=float(matrix.to_numpy().max()))
    states = [f"C{i}" for i in matrix.index]
    ax.set_xticks(range(len(states)), states)
    ax.set_yticks(range(len(states)), states)
    ax.set_xlabel("Next month state")
    ax.set_ylabel("Current month state")
    ax.set_title("Behaviour K5 monthly transition probabilities")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value * 100:.1f}%", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, label="Transition probability")

    paths = []
    for suffix in [".pdf", ".png"]:
        path = OUT / f"fig_k5_transition_matrix{suffix}"
        fig.savefig(path, dpi=220 if suffix == ".png" else None)
        paths.append(path)
    plt.close(fig)
    return paths


def save_k5_two_step_return_plot() -> list[Path]:
    two_step = pd.read_csv(ROOT / "results_v2/temporal_k4_k5_k6/table_viii_k5_inputs.csv")
    labels = [
        f"{str(row.month_start)[-2:]}-{str(row.month_middle)[-2:]}-{str(row.month_end)[-2:]}"
        for row in two_step.itertuples(index=False)
    ]
    x = np.arange(len(two_step))

    fig, ax = plt.subplots(figsize=(7.0, 3.6), constrained_layout=True)
    ax.plot(x, two_step["observed_return"], marker="o", label="Observed return")
    ax.plot(x, two_step["null_mean"], marker="s", label="Stratified null mean")
    ax.fill_between(x, two_step["null_q025"], two_step["null_q975"], alpha=0.18, label="Null 95% interval")
    ax.set_xticks(x, labels, rotation=45, ha="right")
    ax.set_ylabel("Two-step return rate")
    ax.set_title("Behaviour K5 two-step return vs stratified null")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.25)

    paths = []
    for suffix in [".pdf", ".png"]:
        path = OUT / f"fig_k5_two_step_return_vs_null{suffix}"
        fig.savefig(path, dpi=220 if suffix == ".png" else None)
        paths.append(path)
    plt.close(fig)
    return paths


def save_self_transition_comparison() -> list[Path]:
    temporal = pd.read_csv(ROOT / "results_v2/temporal_k4_k5_k6/temporal_summary.csv")
    x = np.arange(len(temporal))
    width = 0.36

    fig, ax = plt.subplots(figsize=(6.3, 3.5), constrained_layout=True)
    ax.bar(x - width / 2, temporal["observed_self_transition"], width, label="Observed")
    ax.bar(x + width / 2, temporal["expected_self_transition"], width, label="Chance")
    ax.set_xticks(x, [f"K{int(k)}" for k in temporal["k"]])
    ax.set_ylim(0, 0.6)
    ax.set_ylabel("Self-transition rate")
    ax.set_title("Observed vs chance self-transition")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    for i, row in enumerate(temporal.itertuples(index=False)):
        ax.text(i, row.observed_self_transition + 0.02, f"kappa={row.cohen_kappa:.3f}", ha="center", fontsize=8)

    paths = []
    for suffix in [".pdf", ".png"]:
        path = OUT / f"fig_k456_self_transition_vs_chance{suffix}"
        fig.savefig(path, dpi=220 if suffix == ".png" else None)
        paths.append(path)
    plt.close(fig)
    return paths


def write_manifest(paths: list[Path]) -> None:
    lines = [
        "# Paper Visuals",
        "",
        "Generated/copied paper-ready visuals for the Ethereum wallet segmentation paper.",
        "Use the PDF versions in Overleaf when possible.",
        "",
    ]
    for path in sorted(paths):
        lines.append(f"- `{path.name}`")
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    paths = []
    paths.extend(copy_existing())
    paths.extend(save_k5_transition_heatmap())
    paths.extend(save_k5_two_step_return_plot())
    paths.extend(save_self_transition_comparison())
    write_manifest(paths)
    for path in sorted(paths):
        print(path)


if __name__ == "__main__":
    main()
