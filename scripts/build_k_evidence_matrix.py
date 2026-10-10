"""Build a paper-facing K4/K5/K6 evidence matrix.

The matrix combines the current result packages:

- internal clustering metrics,
- full-year monthly network-null validation,
- feature/role holdout validation,
- temporal persistence and two-step return validation.

The output is intended for paper integration, not as a new experiment.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results_v2" / "model_evidence_matrix"


def fmt(x: float, digits: int = 3) -> str:
    return f"{x:.{digits}f}"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    internal = pd.read_csv(ROOT / "results_v2/feature_role_checks/internal_metrics_k4_k5_k6.csv")
    network = pd.read_csv(ROOT / "results_v2/network_k4_k5_k6_B999/network_summary.csv")
    feature = pd.read_csv(ROOT / "results_v2/feature_role_checks/feature_holdout_summary_k4_k5_k6.csv")
    temporal = pd.read_csv(ROOT / "results_v2/temporal_k4_k5_k6/temporal_summary.csv")
    return internal, network, feature, temporal


def feature_summary(feature: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = feature[feature["scenario"] != "all_features_resample_baseline"].copy()
    for k, group in usable.groupby("k"):
        weakest = group.sort_values("exact_agreement_after_matching", ascending=True).iloc[0]
        persistence = group[group["scenario"] == "temporal_persistence_holdout"].iloc[0]
        rows.append(
            {
                "k": int(k),
                "feature_holdout_mean_agreement": float(group["exact_agreement_after_matching"].mean()),
                "feature_holdout_worst_agreement": float(weakest["exact_agreement_after_matching"]),
                "feature_holdout_weakest_family": weakest["scenario"],
                "persistence_holdout_agreement": float(persistence["exact_agreement_after_matching"]),
                "persistence_holdout_ari": float(persistence["ari_vs_reference"]),
            }
        )
    return pd.DataFrame(rows)


def make_matrix() -> pd.DataFrame:
    internal, network, feature, temporal = load_inputs()
    feature_rollup = feature_summary(feature)
    df = (
        internal.merge(network, on="k", how="inner")
        .merge(feature_rollup, on="k", how="inner")
        .merge(temporal, on="k", how="inner")
    )

    rows = []
    for row in df.sort_values("k").itertuples(index=False):
        if row.k == 4:
            interpretation = (
                "Conservative alternative. Strongest network evidence and strongest feature-holdout robustness, "
                "with good temporal persistence, but fewer behavioural roles."
            )
        elif row.k == 5:
            interpretation = (
                "Main descriptive taxonomy. Best seed stability and richer role vocabulary, but weaker network "
                "same-role evidence than K4/K6 and weaker feature-holdout recovery than K4."
            )
        else:
            interpretation = (
                "Fine-grained alternative. Network evidence is strong and activity holdout recovery is good, "
                "but seed stability is weakest and one role is fragile under a volatility/concentration holdout."
            )

        rows.append(
            {
                "k": int(row.k),
                "cluster_size_range": f"{fmt(row.min_cluster_share * 100, 1)}%-{fmt(row.max_cluster_share * 100, 1)}%",
                "silhouette_mean": row.silhouette_mean,
                "seed_stability_ari": row.seed_stability_ari,
                "network_holm_sig_months": f"{int(row.significant_months_holm)}/{int(row.months)}",
                "network_mean_observed_minus_null": row.mean_observed_minus_null,
                "feature_holdout_mean_agreement": row.feature_holdout_mean_agreement,
                "feature_holdout_worst": f"{fmt(row.feature_holdout_worst_agreement)} ({row.feature_holdout_weakest_family})",
                "persistence_holdout_agreement": row.persistence_holdout_agreement,
                "self_transition_observed_vs_expected": (
                    f"{fmt(row.observed_self_transition)} vs {fmt(row.expected_self_transition)}"
                ),
                "temporal_kappa": row.cohen_kappa,
                "two_step_return_observed_vs_null": f"{fmt(row.observed_return)} vs {fmt(row.weighted_null_return)}",
                "two_step_holm_sig_triples": (
                    f"{int(row.two_step_significant_triples_holm)}/{int(row.total_triples)}"
                ),
                "paper_interpretation": interpretation,
            }
        )
    return pd.DataFrame(rows)


def write_outputs(matrix: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(OUT_DIR / "k4_k5_k6_evidence_matrix.csv", index=False)

    display = matrix.copy()
    numeric_cols = [
        "silhouette_mean",
        "seed_stability_ari",
        "network_mean_observed_minus_null",
        "feature_holdout_mean_agreement",
        "persistence_holdout_agreement",
        "temporal_kappa",
    ]
    for col in numeric_cols:
        display[col] = display[col].map(lambda x: fmt(float(x)))

    lines = [
        "# K4/K5/K6 Evidence Matrix",
        "",
        "This table combines the current internal, network, feature-holdout, and temporal validation outputs.",
        "It is a paper-integration table, not a new experiment.",
        "",
        "Important caveat: temporal evidence is conditional on the legacy monthly assignment/scaling procedure.",
        "The temporal package reports a monthly window mismatch and a mixed-population scaler provenance issue, so temporal claims should be worded as conditional evidence rather than final causal proof.",
        "",
        display.to_markdown(index=False),
        "",
        "## Paper-Facing Reading",
        "",
        "- K4 is the strongest conservative model: it has the clearest network-null support and strongest feature-holdout robustness.",
        "- K5 is still defensible as the main descriptive taxonomy: it has the best seed stability and a richer behavioural vocabulary.",
        "- K6 adds finer detail, but it is less stable and more fragile in feature-holdout recovery.",
        "- The paper should avoid saying that K5 is statistically best across all tests. A safer claim is that K5 is selected for interpretability, while K4 is the stronger conservative alternative.",
        "",
        "## Suggested Model-Selection Wording",
        "",
        "Across candidate resolutions, K4, K5, and K6 emphasize different trade-offs.",
        "K4 provides the strongest conservative validation profile, with all twelve monthly network-null tests significant after Holm correction and the strongest average feature-holdout recovery.",
        "K5 provides the most stable KMeans solution across seeds and a richer behavioural vocabulary, which makes it useful as the main descriptive taxonomy.",
        "K6 provides finer-grained structure and strong network evidence, but its lower seed stability and fragile holdout recovery indicate that the extra resolution should be interpreted cautiously.",
        "Therefore, this paper reports K5 as the primary descriptive taxonomy while treating K4 as a conservative robustness reference and K6 as a fine-grained sensitivity check.",
    ]
    (OUT_DIR / "k4_k5_k6_evidence_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    latex_cols = [
        "k",
        "silhouette_mean",
        "seed_stability_ari",
        "network_holm_sig_months",
        "feature_holdout_mean_agreement",
        "persistence_holdout_agreement",
        "temporal_kappa",
        "two_step_holm_sig_triples",
    ]
    latex = display[latex_cols].to_latex(index=False, escape=True)
    (OUT_DIR / "k4_k5_k6_evidence_matrix_table.tex").write_text(latex, encoding="utf-8")


def main() -> None:
    matrix = make_matrix()
    write_outputs(matrix)
    print(matrix.to_string(index=False))
    print(f"Saved evidence matrix to {OUT_DIR}")


if __name__ == "__main__":
    main()
