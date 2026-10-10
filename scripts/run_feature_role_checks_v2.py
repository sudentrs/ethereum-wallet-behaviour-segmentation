"""Feature/role interpretation checks for the paper revision.

This script collects feature-side diagnostics for the EOA-only K4/K5/K6
taxonomies:

- feature-family holdout validation, including temporal-persistence holdout,
- K4/K5/K6 internal metrics for model-selection discussion,
- robust-scaled feature profile heatmaps for each candidate k,
- raw role medians for cautious role descriptions,
- formula documentation for the time-domain "burstiness" field.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results_v2" / "feature_role_checks"
SCALED_FEATURES = (
    ROOT
    / "wallet_eoa_only_kmeans6_features_robust_scaled"
    / "wallet_eoa_only_kmeans6_features_robust_scaled.csv"
)
RAW_FEATURES = ROOT.parent / "dataverse_files" / "wallet_kmeans6_expanded_daily_features.csv"
K_VALUES = [4, 5, 6]
RANDOM_STATE = 492


FEATURE_GROUPS = {
    "all_features_resample_baseline": [],
    "activity_holdout": [
        "active_days_observed",
        "activity_span_days",
        "activity_density",
        "total_tx",
        "avg_daily_tx_count",
        "max_daily_tx_count",
        "std_daily_tx_count",
        "tx_count_cv",
    ],
    "value_flow_holdout": [
        "total_in_sum",
        "total_out_sum",
        "total_net_flow_sum",
        "total_flow_sum",
        "avg_daily_total_in",
        "avg_daily_total_out",
        "avg_daily_net_flow",
        "avg_daily_total_flow",
        "max_daily_total_in",
        "max_daily_total_out",
        "max_daily_total_flow",
        "std_daily_total_in",
        "std_daily_total_out",
        "std_daily_net_flow",
        "std_daily_total_flow",
    ],
    "directionality_holdout": [
        "total_net_flow_sum",
        "avg_daily_net_flow",
        "in_active_days",
        "out_active_days",
        "both_active_days",
        "in_active_day_ratio",
        "out_active_day_ratio",
        "both_active_day_ratio",
        "in_out_day_balance",
    ],
    "volatility_concentration_holdout": [
        "std_daily_tx_count",
        "std_daily_total_in",
        "std_daily_total_out",
        "std_daily_net_flow",
        "std_daily_total_flow",
        "tx_count_cv",
        "total_flow_cv",
        "tx_concentration_ratio",
        "flow_concentration_ratio",
    ],
    "temporal_persistence_holdout": [
        "active_days_observed",
        "activity_span_days",
        "activity_density",
        "in_active_days",
        "out_active_days",
        "both_active_days",
        "in_active_day_ratio",
        "out_active_day_ratio",
        "both_active_day_ratio",
    ],
}


RAW_MEDIAN_COLS = [
    "active_days_observed",
    "activity_span_days",
    "activity_density",
    "total_tx",
    "tx_per_active_day",
    "total_in_sum",
    "total_out_sum",
    "total_net_flow_sum",
    "total_flow_sum",
    "avg_daily_tx_count",
    "max_daily_tx_count",
]


def clean_wallet(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def label_path(k: int) -> Path:
    return ROOT / f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv"


def load_labels(k: int) -> pd.DataFrame:
    labels = pd.read_csv(label_path(k), dtype={"wallet": "string"})
    labels["wallet"] = clean_wallet(labels["wallet"])
    labels["cluster"] = labels["cluster"].astype(int)
    return labels.drop_duplicates("wallet")


def feature_columns(path: Path) -> list[str]:
    cols = pd.read_csv(path, nrows=1).columns.tolist()
    return [c for c in cols if c not in {"wallet", "cluster", "old_cluster"}]


def load_scaled_features() -> pd.DataFrame:
    print("Loading scaled EOA features...", flush=True)
    features = pd.read_csv(SCALED_FEATURES, dtype={"wallet": "string"})
    features["wallet"] = clean_wallet(features["wallet"])
    return features.drop(columns=["cluster", "old_cluster"], errors="ignore")


def align_to_reference(reference: np.ndarray, candidate: np.ndarray, k: int) -> tuple[np.ndarray, pd.DataFrame]:
    crosstab = pd.crosstab(reference, candidate)
    crosstab = crosstab.reindex(index=range(k), columns=range(k), fill_value=0)
    row_ind, col_ind = linear_sum_assignment(-crosstab.to_numpy())
    mapping = {int(col): int(row) for row, col in zip(row_ind, col_ind)}
    aligned = np.array([mapping[int(label)] for label in candidate], dtype=int)

    rows = []
    for ref_cluster in range(k):
        ref_mask = reference == ref_cluster
        matched_candidate = next(int(col) for row, col in zip(row_ind, col_ind) if int(row) == ref_cluster)
        recovered = aligned[ref_mask] == ref_cluster
        rows.append(
            {
                "k": k,
                "reference_cluster": ref_cluster,
                "matched_candidate_cluster": matched_candidate,
                "reference_wallets": int(ref_mask.sum()),
                "recovered_wallets_after_matching": int(recovered.sum()),
                "recovery_rate": float(recovered.mean()) if ref_mask.any() else np.nan,
            }
        )
    return aligned, pd.DataFrame(rows)


def run_one_holdout(
    df: pd.DataFrame,
    k: int,
    scenario: str,
    removed_features: list[str],
    all_features: list[str],
) -> tuple[dict, pd.DataFrame]:
    retained = [c for c in all_features if c not in set(removed_features)]
    X = df[retained].to_numpy(dtype=np.float32, copy=True)
    reference = df["reference_cluster"].to_numpy(dtype=int)

    model = MiniBatchKMeans(
        n_clusters=k,
        random_state=RANDOM_STATE,
        batch_size=8192,
        n_init=10,
        max_iter=200,
    )
    candidate = model.fit_predict(X)
    aligned, recovery = align_to_reference(reference, candidate, k=k)
    recovery.insert(1, "scenario", scenario)

    summary = {
        "k": k,
        "scenario": scenario,
        "sample_wallets": int(len(df)),
        "removed_feature_count": int(len(removed_features)),
        "retained_feature_count": int(len(retained)),
        "ari_vs_reference": float(adjusted_rand_score(reference, candidate)),
        "nmi_vs_reference": float(normalized_mutual_info_score(reference, candidate)),
        "exact_agreement_after_matching": float((aligned == reference).mean()),
        "mean_cluster_recovery_after_matching": float(recovery["recovery_rate"].mean()),
        "min_cluster_recovery_after_matching": float(recovery["recovery_rate"].min()),
        "removed_features": "; ".join(removed_features),
    }
    return summary, recovery


def run_feature_holdouts(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_features = feature_columns(SCALED_FEATURES)
    summaries = []
    recoveries = []
    missing_by_scenario = {
        scenario: sorted(set(removed) - set(all_features))
        for scenario, removed in FEATURE_GROUPS.items()
        if sorted(set(removed) - set(all_features))
    }
    if missing_by_scenario:
        raise ValueError(f"Missing holdout features: {missing_by_scenario}")

    for k in K_VALUES:
        print(f"Running feature holdouts for K{k}...", flush=True)
        labels = load_labels(k).rename(columns={"cluster": "reference_cluster"})
        df = features.merge(labels, on="wallet", how="inner")
        for scenario, removed in FEATURE_GROUPS.items():
            summary, recovery = run_one_holdout(df, k, scenario, removed, all_features)
            summaries.append(summary)
            recoveries.append(recovery)
    return pd.DataFrame(summaries), pd.concat(recoveries, ignore_index=True)


def package_internal_metrics() -> pd.DataFrame:
    sensitivity = pd.read_csv(ROOT / "results/eoa_only_kmeans6/k_sensitivity_full/k_sensitivity_summary.csv")
    sensitivity = sensitivity[sensitivity["k"].isin(K_VALUES)].copy()
    rows = []
    for row in sensitivity.itertuples(index=False):
        sizes = pd.read_csv(ROOT / f"results/eoa_only_kmeans{int(row.k)}/cluster_sizes.csv")
        rows.append(
            {
                "k": int(row.k),
                "min_cluster_share": float(sizes["wallet_share"].min()),
                "max_cluster_share": float(sizes["wallet_share"].max()),
                "seed_stability_ari": float(row.stability_ari_mean),
                "seed_stability_nmi": float(row.stability_nmi_mean),
                "silhouette_mean": float(row.silhouette_mean),
                "silhouette_std": float(row.silhouette_std),
                "davies_bouldin_mean": float(row.davies_bouldin_mean),
            }
        )
    return pd.DataFrame(rows)


def write_profile_heatmap(k: int) -> Path:
    profile = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/cluster_feature_medians_robust_scaled.csv")
    profile = profile.set_index("cluster")
    fig, ax = plt.subplots(figsize=(12.5, 3.8), constrained_layout=True)
    values = profile.to_numpy(dtype=float)
    im = ax.imshow(np.clip(values, -3, 3), cmap="RdBu_r", vmin=-3, vmax=3, aspect="auto")
    ax.set_yticks(range(len(profile.index)), [f"C{c}" for c in profile.index])
    ax.set_xticks(range(len(profile.columns)))
    ax.set_xticklabels(profile.columns, rotation=90, fontsize=7)
    ax.set_ylabel(f"Behaviour K{k} role")
    ax.set_title(f"Behaviour K{k} robust-scaled feature medians")
    fig.colorbar(im, ax=ax, label="Median scaled value")
    out = OUT_DIR / f"k{k}_profile_heatmap.pdf"
    fig.savefig(out)
    fig.savefig(OUT_DIR / f"k{k}_profile_heatmap.png", dpi=220)
    plt.close(fig)
    return out


def load_raw_features_for_medians() -> pd.DataFrame:
    usecols = [
        "wallet",
        "active_days_observed",
        "activity_span_days",
        "activity_density",
        "total_tx",
        "total_in_sum",
        "total_out_sum",
        "total_net_flow_sum",
        "total_flow_sum",
        "avg_daily_tx_count",
        "max_daily_tx_count",
    ]
    print("Loading raw features for role medians...", flush=True)
    raw = pd.read_csv(RAW_FEATURES, usecols=usecols, dtype={"wallet": "string"})
    raw["wallet"] = clean_wallet(raw["wallet"])
    return raw


def compute_raw_medians(k: int, raw: pd.DataFrame) -> pd.DataFrame:
    labels = load_labels(k)
    df = raw.merge(labels, on="wallet", how="inner")
    df["tx_per_active_day"] = df["total_tx"] / df["active_days_observed"].replace(0, np.nan)
    medians = df.groupby("cluster")[RAW_MEDIAN_COLS].median().reset_index()
    medians.insert(0, "k", k)
    medians["wallets"] = df.groupby("cluster").size().reindex(medians["cluster"]).to_numpy()
    return medians


def write_burstiness_note() -> None:
    note = [
        "# Burstiness Formula Check",
        "",
        "The time-domain signal script does not compute the standard Goh-Barabasi burstiness coefficient.",
        "In `src/validation/build_full_eoa_temporal_signal_streaming.py`, the reported transaction burstiness field is named `tx_burstiness_cv`.",
        "It is computed as:",
        "",
        "`std_tx_active / mean_tx_active`",
        "",
        "where `std_tx_active` and `mean_tx_active` are calculated from daily transaction counts on active days only.",
        "",
        "This is a coefficient of variation, not the standard burstiness coefficient `B = (sigma - mu) / (sigma + mu)`.",
        "Therefore values above 1, such as TD4 = 1.016, are possible and are not mathematically invalid under this definition.",
        "",
        "Paper wording should use `transaction-count coefficient of variation on active days` or `tx burstiness CV`.",
        "Avoid saying that the value is the standard burstiness coefficient.",
    ]
    (OUT_DIR / "burstiness_formula_check.md").write_text("\n".join(note) + "\n", encoding="utf-8")


def write_summary(holdouts: pd.DataFrame, internal: pd.DataFrame) -> None:
    compact_holdouts = holdouts[
        [
            "k",
            "scenario",
            "ari_vs_reference",
            "nmi_vs_reference",
            "exact_agreement_after_matching",
            "mean_cluster_recovery_after_matching",
            "min_cluster_recovery_after_matching",
        ]
    ].copy()
    persistence = compact_holdouts[compact_holdouts["scenario"] == "temporal_persistence_holdout"].copy()
    best_by_k = (
        compact_holdouts[compact_holdouts["scenario"] != "all_features_resample_baseline"]
        .sort_values(["k", "exact_agreement_after_matching"], ascending=[True, False])
        .groupby("k")
        .head(1)
    )
    weakest_by_k = (
        compact_holdouts[compact_holdouts["scenario"] != "all_features_resample_baseline"]
        .sort_values(["k", "exact_agreement_after_matching"], ascending=[True, True])
        .groupby("k")
        .head(1)
    )

    lines = [
        "# Feature and Role Checks V2",
        "",
        "## Outputs",
        "",
        "- `feature_holdout_summary_k4_k5_k6.csv`: comparable feature-family holdout validation for K4, K5, and K6.",
        "- `feature_holdout_cluster_recovery_k4_k5_k6.csv`: per-role recovery rates after Hungarian matching.",
        "- `internal_metrics_k4_k5_k6.csv`: K4/K5/K6 silhouette, Davies-Bouldin, seed stability, and size balance for Table III.",
        "- `k4_profile_heatmap.pdf/png`, `k5_profile_heatmap.pdf/png`, `k6_profile_heatmap.pdf/png`: robust-scaled feature median heatmaps.",
        "- `k4_raw_role_medians.csv`, `k5_raw_role_medians.csv`, `k6_raw_role_medians.csv`: raw medians for role interpretation.",
        "- `raw_role_medians_k4_k5_k6.csv`: combined raw median table.",
        "- `burstiness_formula_check.md`: formula note for replacing misleading burstiness wording.",
        "",
        "## Internal Metrics",
        "",
        internal.to_markdown(index=False),
        "",
        "## Feature Holdout Comparison",
        "",
        compact_holdouts.to_markdown(index=False),
        "",
        "## Temporal Persistence Holdout",
        "",
        persistence.to_markdown(index=False),
        "",
        "## Strongest Holdout Recovery Per K",
        "",
        best_by_k.to_markdown(index=False),
        "",
        "## Weakest Holdout Recovery Per K",
        "",
        weakest_by_k.to_markdown(index=False),
        "",
        "## Role-Wording Notes",
        "",
        "Use the raw median tables to describe each role cautiously.",
        "For K5, C2 remains a concentrated high-intensity role over few active days rather than a persistent dense role.",
        "For K5, C4 remains the most persistent/high-active-day K5 role, but the median active-day count is still far from continuous full-year activity.",
        "",
        "## Burstiness Wording",
        "",
        "`tx_burstiness_cv` is a coefficient of variation on active-day transaction counts. It can exceed 1. Use this name/formula in the paper rather than the standard burstiness coefficient.",
    ]
    (OUT_DIR / "feature_role_checks_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    features = load_scaled_features()
    holdouts, recovery = run_feature_holdouts(features)
    holdouts.to_csv(OUT_DIR / "feature_holdout_summary_k4_k5_k6.csv", index=False)
    recovery.to_csv(OUT_DIR / "feature_holdout_cluster_recovery_k4_k5_k6.csv", index=False)

    # Preserve the original K5-specific filenames used by the current draft.
    k5_holdouts = holdouts[holdouts["k"] == 5].drop(columns=["k"])
    k5_recovery = recovery[recovery["k"] == 5].drop(columns=["k"])
    k5_holdouts[k5_holdouts["scenario"] == "temporal_persistence_holdout"].to_csv(
        OUT_DIR / "persistence_holdout_summary.csv", index=False
    )
    k5_recovery[k5_recovery["scenario"] == "temporal_persistence_holdout"].to_csv(
        OUT_DIR / "persistence_holdout_cluster_recovery.csv", index=False
    )
    k5_holdouts.to_csv(OUT_DIR / "feature_holdout_summary_with_persistence.csv", index=False)

    internal = package_internal_metrics()
    internal.to_csv(OUT_DIR / "internal_metrics_k4_k5_k6.csv", index=False)

    heatmap_paths = [write_profile_heatmap(k) for k in K_VALUES]

    raw = load_raw_features_for_medians()
    median_tables = []
    for k in K_VALUES:
        medians = compute_raw_medians(k, raw)
        medians.to_csv(OUT_DIR / f"k{k}_raw_role_medians.csv", index=False)
        median_tables.append(medians)
    all_medians = pd.concat(median_tables, ignore_index=True)
    all_medians.to_csv(OUT_DIR / "raw_role_medians_k4_k5_k6.csv", index=False)

    write_burstiness_note()
    write_summary(holdouts, internal)

    print(holdouts.to_string(index=False))
    print(internal.to_string(index=False))
    print(all_medians.to_string(index=False))
    print("Saved heatmaps:")
    for path in heatmap_paths:
        print(f"- {path}")
    print(f"Saved feature/role checks to {OUT_DIR}")


if __name__ == "__main__":
    main()
