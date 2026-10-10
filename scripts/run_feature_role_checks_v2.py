"""Feature/role interpretation checks for the paper revision.

This script collects the professor-requested feature-side fixes into one
results_v2 folder:

- add the missing temporal-persistence feature holdout for Behaviour K5,
- package K4/K5/K6 internal metrics for the revised Table III,
- export a K5 robust-scaled feature profile heatmap,
- compute raw K5 role medians for cautious C2/C4 wording,
- document the time-domain "burstiness" formula as coefficient of variation.
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
K5_LABELS = ROOT / "results" / "eoa_only_kmeans5" / "wallet_eoa_only_kmeans_clusters.csv"


PERSISTENCE_FEATURES = [
    "active_days_observed",
    "activity_span_days",
    "activity_density",
    "in_active_days",
    "out_active_days",
    "both_active_days",
    "in_active_day_ratio",
    "out_active_day_ratio",
    "both_active_day_ratio",
]


def clean_wallet(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def load_k5_labels() -> pd.DataFrame:
    labels = pd.read_csv(K5_LABELS, dtype={"wallet": "string"})
    labels["wallet"] = clean_wallet(labels["wallet"])
    labels["cluster"] = labels["cluster"].astype(int)
    return labels.drop_duplicates("wallet")


def feature_columns(path: Path) -> list[str]:
    cols = pd.read_csv(path, nrows=1).columns.tolist()
    return [c for c in cols if c not in {"wallet", "cluster", "old_cluster"}]


def align_to_reference(reference: np.ndarray, candidate: np.ndarray, k: int = 5) -> tuple[np.ndarray, pd.DataFrame]:
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
                "reference_cluster": ref_cluster,
                "matched_candidate_cluster": matched_candidate,
                "reference_wallets": int(ref_mask.sum()),
                "recovered_wallets_after_matching": int(recovered.sum()),
                "recovery_rate": float(recovered.mean()) if ref_mask.any() else np.nan,
            }
        )
    return aligned, pd.DataFrame(rows)


def run_persistence_holdout() -> tuple[pd.DataFrame, pd.DataFrame]:
    print("Loading scaled EOA features for persistence holdout...", flush=True)
    labels = load_k5_labels().rename(columns={"cluster": "reference_cluster"})
    features = pd.read_csv(SCALED_FEATURES, dtype={"wallet": "string"})
    features["wallet"] = clean_wallet(features["wallet"])
    features = features.drop(columns=["cluster", "old_cluster"], errors="ignore")
    df = features.merge(labels, on="wallet", how="inner")

    all_features = feature_columns(SCALED_FEATURES)
    missing = sorted(set(PERSISTENCE_FEATURES) - set(all_features))
    if missing:
        raise ValueError(f"Missing persistence features: {missing}")
    retained = [c for c in all_features if c not in set(PERSISTENCE_FEATURES)]

    X = df[retained].to_numpy(dtype=np.float32, copy=True)
    reference = df["reference_cluster"].to_numpy(dtype=int)
    model = MiniBatchKMeans(
        n_clusters=5,
        random_state=42,
        batch_size=8192,
        n_init=10,
        max_iter=200,
    )
    candidate = model.fit_predict(X)
    aligned, recovery = align_to_reference(reference, candidate)
    summary = pd.DataFrame(
        [
            {
                "scenario": "temporal_persistence_holdout",
                "sample_wallets": int(len(df)),
                "removed_feature_count": int(len(PERSISTENCE_FEATURES)),
                "retained_feature_count": int(len(retained)),
                "ari_vs_reference": float(adjusted_rand_score(reference, candidate)),
                "nmi_vs_reference": float(normalized_mutual_info_score(reference, candidate)),
                "exact_agreement_after_matching": float((aligned == reference).mean()),
                "mean_cluster_recovery_after_matching": float(recovery["recovery_rate"].mean()),
                "min_cluster_recovery_after_matching": float(recovery["recovery_rate"].min()),
                "removed_features": "; ".join(PERSISTENCE_FEATURES),
            }
        ]
    )
    recovery.insert(0, "scenario", "temporal_persistence_holdout")
    return summary, recovery


def package_internal_metrics() -> pd.DataFrame:
    sensitivity = pd.read_csv(ROOT / "results/eoa_only_kmeans6/k_sensitivity_full/k_sensitivity_summary.csv")
    sensitivity = sensitivity[sensitivity["k"].isin([4, 5, 6])].copy()
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


def write_profile_heatmap() -> Path:
    profile = pd.read_csv(ROOT / "results/eoa_only_kmeans5/cluster_feature_medians_robust_scaled.csv")
    profile = profile.set_index("cluster")
    fig, ax = plt.subplots(figsize=(12.5, 3.8), constrained_layout=True)
    values = profile.to_numpy(dtype=float)
    im = ax.imshow(np.clip(values, -3, 3), cmap="RdBu_r", vmin=-3, vmax=3, aspect="auto")
    ax.set_yticks(range(len(profile.index)), [f"C{c}" for c in profile.index])
    ax.set_xticks(range(len(profile.columns)))
    ax.set_xticklabels(profile.columns, rotation=90, fontsize=7)
    ax.set_ylabel("Behaviour K5 role")
    ax.set_title("Behaviour K5 robust-scaled feature medians")
    fig.colorbar(im, ax=ax, label="Median scaled value")
    out = OUT_DIR / "k5_profile_heatmap.pdf"
    fig.savefig(out)
    fig.savefig(OUT_DIR / "k5_profile_heatmap.png", dpi=220)
    plt.close(fig)
    return out


def compute_k5_raw_medians() -> pd.DataFrame:
    labels = load_k5_labels()
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
    print("Loading raw features for K5 role medians...", flush=True)
    raw = pd.read_csv(RAW_FEATURES, usecols=usecols, dtype={"wallet": "string"})
    raw["wallet"] = clean_wallet(raw["wallet"])
    df = raw.merge(labels, on="wallet", how="inner")
    df["tx_per_active_day"] = df["total_tx"] / df["active_days_observed"].replace(0, np.nan)
    median_cols = [
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
    medians = df.groupby("cluster")[median_cols].median().reset_index()
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


def write_summary(
    holdout: pd.DataFrame,
    internal: pd.DataFrame,
    medians: pd.DataFrame,
    combined_holdout: pd.DataFrame,
) -> None:
    c2 = medians[medians["cluster"] == 2].iloc[0]
    c4 = medians[medians["cluster"] == 4].iloc[0]
    lines = [
        "# Feature and Role Checks V2",
        "",
        "## Outputs",
        "",
        "- `persistence_holdout_summary.csv`: missing temporal-persistence holdout row for Table V.",
        "- `feature_holdout_summary_with_persistence.csv`: previous full holdout table plus the new persistence row.",
        "- `internal_metrics_k4_k5_k6.csv`: K4/K5/K6 silhouette, Davies-Bouldin, seed stability, and size balance for Table III.",
        "- `k5_profile_heatmap.pdf/png`: robust-scaled feature median heatmap for Behaviour K5.",
        "- `k5_raw_role_medians.csv`: raw median features for correcting C2/C4 role descriptions.",
        "- `burstiness_formula_check.md`: formula note for replacing the misleading burstiness wording.",
        "",
        "## Persistence Holdout Result",
        "",
        holdout.to_markdown(index=False),
        "",
        "## Combined Holdout Table",
        "",
        combined_holdout[
            [
                "scenario",
                "ari_vs_reference",
                "nmi_vs_reference",
                "exact_agreement_after_matching",
                "mean_cluster_recovery_after_matching",
                "min_cluster_recovery_after_matching",
            ]
        ].to_markdown(index=False),
        "",
        "## Internal Metrics",
        "",
        internal.to_markdown(index=False),
        "",
        "## C2/C4 Wording Check",
        "",
        f"C2 median active days: `{c2['active_days_observed']:.2f}`; median total transactions: `{c2['total_tx']:.2f}`; median transactions per active day: `{c2['tx_per_active_day']:.2f}`.",
        f"C4 median active days: `{c4['active_days_observed']:.2f}`; median total transactions: `{c4['total_tx']:.2f}`; median transactions per active day: `{c4['tx_per_active_day']:.2f}`.",
        "",
        "Interpretation: C2 should be described as concentrated high transaction intensity over few active days, not persistent dense activity across the year.",
        "C4 can be described as the most persistent/high-active-day K5 role, but not as continuously active across the full year.",
        "",
        "## Burstiness Wording",
        "",
        "`tx_burstiness_cv` is a coefficient of variation on active-day transaction counts. It can exceed 1. Use this name/formula in the paper rather than the standard burstiness coefficient.",
    ]
    (OUT_DIR / "feature_role_checks_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    holdout, recovery = run_persistence_holdout()
    holdout.to_csv(OUT_DIR / "persistence_holdout_summary.csv", index=False)
    recovery.to_csv(OUT_DIR / "persistence_holdout_cluster_recovery.csv", index=False)

    old_holdout_path = ROOT / "results/k5_feature_holdout_validation_full/feature_holdout_summary.csv"
    if old_holdout_path.exists():
        old_holdout = pd.read_csv(old_holdout_path)
        combined = pd.concat([old_holdout, holdout], ignore_index=True)
    else:
        combined = holdout.copy()
    combined.to_csv(OUT_DIR / "feature_holdout_summary_with_persistence.csv", index=False)

    internal = package_internal_metrics()
    internal.to_csv(OUT_DIR / "internal_metrics_k4_k5_k6.csv", index=False)

    heatmap_path = write_profile_heatmap()
    medians = compute_k5_raw_medians()
    medians.to_csv(OUT_DIR / "k5_raw_role_medians.csv", index=False)

    write_burstiness_note()
    write_summary(holdout, internal, medians, combined)

    print(holdout.to_string(index=False))
    print(internal.to_string(index=False))
    print(medians.to_string(index=False))
    print(f"Saved heatmap to {heatmap_path}")
    print(f"Saved feature/role checks to {OUT_DIR}")


if __name__ == "__main__":
    main()
