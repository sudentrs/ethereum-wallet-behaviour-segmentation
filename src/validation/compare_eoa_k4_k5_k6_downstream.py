from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def read_cluster_size_summary(k: int) -> dict:
    sizes = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/cluster_sizes.csv")
    return {
        "k": k,
        "cluster_count": len(sizes),
        "min_cluster_share": sizes["wallet_share"].min(),
        "max_cluster_share": sizes["wallet_share"].max(),
        "smallest_cluster_wallets": int(sizes.loc[sizes["wallet_share"].idxmin(), "wallet_count"]),
        "largest_cluster_wallets": int(sizes.loc[sizes["wallet_share"].idxmax(), "wallet_count"]),
    }


def read_k_sensitivity(k: int) -> dict:
    path = ROOT / "results/eoa_only_kmeans6/k_sensitivity_full/k_sensitivity_summary.csv"
    row = pd.read_csv(path).set_index("k").loc[k]
    return {
        "full_sensitivity_silhouette": row["silhouette_mean"],
        "seed_stability_ari": row["stability_ari_mean"],
        "seed_stability_nmi": row["stability_nmi_mean"],
        "davies_bouldin": row["davies_bouldin_mean"],
    }


def read_single_run(k: int) -> dict:
    path = ROOT / f"results/eoa_only_kmeans{k}/kmeans_summary.csv"
    row = pd.read_csv(path).iloc[0]
    return {
        "single_run_inertia": row["inertia"],
        "single_run_silhouette": row["silhouette"],
    }


def read_network(k: int) -> dict:
    row = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/network_validation/network_validation_summary.csv").iloc[0]
    return {
        "network_coverage_ratio": row["coverage_ratio"],
        "network_self_loop_ratio": row["self_loop_ratio_all_labeled_tx"],
        "network_observed_same_cluster_sample": row["observed_sample_same_cluster_ratio"],
        "network_random_null_mean": row["null_mean"],
        "network_random_null_p": row["p_value_upper"],
        "network_label_modularity_sample": row["sample_wallet_label_modularity"],
        "network_assortativity_sample": row["sample_wallet_attribute_assortativity"],
    }


def read_temporal(k: int) -> dict:
    base = ROOT / f"results/eoa_only_kmeans{k}/temporal_validation"
    transition = pd.read_csv(base / "monthly_transition_summary.csv")
    state = pd.read_csv(base / "state_transition_stability.csv")
    two_step = pd.read_csv(base / "two_step_return_analysis.csv")
    return {
        "temporal_self_transition_mean": transition["self_transition_rate"].mean(),
        "temporal_self_transition_min": transition["self_transition_rate"].min(),
        "temporal_self_transition_max": transition["self_transition_rate"].max(),
        "state_self_transition_min": state["self_transition_probability"].min(),
        "state_self_transition_max": state["self_transition_probability"].max(),
        "two_step_return_mean": two_step["two_step_return_rate_after_leaving"].mean(),
        "two_step_return_min": two_step["two_step_return_rate_after_leaving"].min(),
        "two_step_return_max": two_step["two_step_return_rate_after_leaving"].max(),
    }


def verdict(row: pd.Series) -> str:
    if row["k"] == 4:
        return "Strong conservative baseline: best network-null result, acceptable stability, but less expressive."
    if row["k"] == 5:
        return "Best richer taxonomy balance: strong seed stability and temporal behaviour, but network-null evidence is mixed."
    if row["k"] == 6:
        return "Exploratory fine-grained taxonomy: more roles and borderline network-null support, but weaker seed stability."
    return ""


def fmt(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value:.4f}"


def write_report(summary: pd.DataFrame, out_dir: Path) -> None:
    k4 = summary[summary["k"] == 4].iloc[0]
    k5 = summary[summary["k"] == 5].iloc[0]
    k6 = summary[summary["k"] == 6].iloc[0]
    lines = [
        "# EOA-Only K4/K5/K6 Downstream Validation Comparison",
        "",
        "## Purpose",
        "",
        "This report compares the realistic post-contract-removal role counts: `K=4`, `K=5`, and `K=6`.",
        "",
        "The goal is to decide whether `K=5` remains defensible after running the same downstream network and temporal checks for the neighbouring alternatives.",
        "",
        "## Summary Table",
        "",
        summary[
            [
                "k",
                "min_cluster_share",
                "max_cluster_share",
                "full_sensitivity_silhouette",
                "seed_stability_ari",
                "network_observed_same_cluster_sample",
                "network_random_null_mean",
                "network_random_null_p",
                "temporal_self_transition_mean",
                "two_step_return_mean",
                "verdict",
            ]
        ].to_markdown(index=False),
        "",
        "## What Changed After Downstream Validation",
        "",
        "Before downstream validation, `K=5` looked like the best richer taxonomy because it balanced interpretability, cluster size, and seed stability better than `K=6`.",
        "",
        "After downstream validation, the result is more nuanced.",
        "",
        f"`K=4` has the strongest transaction-network null result. Its observed same-cluster ratio is `{fmt(k4['network_observed_same_cluster_sample'])}` compared with a null mean of `{fmt(k4['network_random_null_mean'])}`, with p-value `{fmt(k4['network_random_null_p'])}`.",
        "",
        f"`K=5` remains strong on seed stability and temporal behaviour, but its network-null test is not supportive. Its observed same-cluster ratio is `{fmt(k5['network_observed_same_cluster_sample'])}` compared with a null mean of `{fmt(k5['network_random_null_mean'])}`, with p-value `{fmt(k5['network_random_null_p'])}`.",
        "",
        f"`K=6` has borderline network-null support with p-value `{fmt(k6['network_random_null_p'])}`, but its seed stability is much weaker than `K=5` in the full K-sensitivity table.",
        "",
        "## Interpretation By Candidate",
        "",
        "### K=4",
        "",
        "K4 is the strongest conservative option. It passes the downstream network-null test clearly and has no tiny clusters. The tradeoff is that it merges behaviours that K5 separates, so it is less useful if the research goal is a richer behavioural role vocabulary.",
        "",
        "### K=5",
        "",
        "K5 is still defensible as the preferred richer role taxonomy. It has better seed stability than K6 and preserves five interpretable roles without creating very small clusters. Its temporal validation is also meaningful: wallets show moderate month-to-month persistence and a clear two-step return pattern.",
        "",
        "The weakness is network validation. K5 role-to-role flows are structured, but the sampled same-cluster null test does not show stronger within-role concentration than randomized labels. Therefore, K5 should not be described as strongly network-validated.",
        "",
        "### K=6",
        "",
        "K6 gives the most fine-grained role vocabulary among these three options. Its network-null result is borderline supportive, but its seed stability is weaker and its role taxonomy is more sensitive to initialization. This makes K6 useful as an exploratory or appendix comparison, not the safest main taxonomy.",
        "",
        "## Recommended Claim",
        "",
        "The most academically honest conclusion is:",
        "",
        "> EOA-only wallet behaviour supports a stable coarse structure and several defensible role resolutions. `K=4` is the strongest conservative network-aligned taxonomy. `K=5` is the preferred richer behavioural taxonomy because it balances stability, interpretability, cluster size, and temporal persistence. `K=6` provides additional granularity but is less stable and should be treated as exploratory unless further validation is added.",
        "",
        "## Paper-Facing Decision",
        "",
        "Use `K=5` if the paper's main goal is an interpretable behavioural role taxonomy.",
        "",
        "Use `K=4` as a conservative robustness comparison, especially when discussing transaction-network evidence.",
        "",
        "Use `K=6` only as a fine-grained sensitivity comparison.",
        "",
        "Do not claim that one K is the universal true number of Ethereum wallet roles.",
    ]
    (out_dir / "eoa_k4_k5_k6_downstream_comparison.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    out_dir = ROOT / "results/eoa_k4_k5_k6_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for k in [4, 5, 6]:
        row = {
            **read_cluster_size_summary(k),
            **read_k_sensitivity(k),
            **read_single_run(k),
            **read_network(k),
            **read_temporal(k),
        }
        rows.append(row)
    summary = pd.DataFrame(rows)
    summary["network_null_supported"] = summary["network_random_null_p"] <= 0.05
    summary["verdict"] = summary.apply(verdict, axis=1)
    summary.to_csv(out_dir / "eoa_k4_k5_k6_downstream_summary.csv", index=False)
    write_report(summary, out_dir)
    print(summary.to_string(index=False))
    print(f"Saved K4/K5/K6 downstream comparison to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
