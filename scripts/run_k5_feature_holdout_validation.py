import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "data" / "processed" / "wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled.csv"
REFERENCE = ROOT / "results" / "eoa_only_kmeans5" / "wallet_eoa_only_kmeans_clusters.csv"
OUT_DIR = ROOT / "results" / "k5_feature_holdout_validation"


FEATURE_GROUPS = {
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
}


def feature_columns(path: Path) -> list[str]:
    cols = pd.read_csv(path, nrows=1).columns.tolist()
    return [c for c in cols if c not in {"wallet", "cluster"}]


def load_population_sample(sample_size: int = 300_000, random_state: int = 492) -> pd.DataFrame:
    labels = pd.read_csv(REFERENCE, dtype={"wallet": str}).rename(columns={"cluster": "reference_cluster"})
    features = pd.read_csv(FEATURES, dtype={"wallet": str})
    df = features.drop(columns=["cluster"], errors="ignore").merge(labels, on="wallet", how="inner")

    if sample_size <= 0 or sample_size >= len(df):
        return df.reset_index(drop=True)

    n = min(sample_size, len(df))
    return df.sample(n=n, random_state=random_state).reset_index(drop=True)


def align_to_reference(reference: np.ndarray, candidate: np.ndarray, k: int = 5) -> tuple[np.ndarray, pd.DataFrame]:
    crosstab = pd.crosstab(reference, candidate)
    crosstab = crosstab.reindex(index=range(k), columns=range(k), fill_value=0)

    cost = -crosstab.to_numpy()
    row_ind, col_ind = linear_sum_assignment(cost)
    mapping = {int(col): int(row) for row, col in zip(row_ind, col_ind)}
    aligned = np.array([mapping[int(label)] for label in candidate], dtype=int)

    match_rows = []
    for ref_cluster in range(k):
        ref_mask = reference == ref_cluster
        recovered = aligned[ref_mask] == ref_cluster
        match_rows.append(
            {
                "reference_cluster": ref_cluster,
                "matched_candidate_cluster": next(
                    int(col) for row, col in zip(row_ind, col_ind) if int(row) == ref_cluster
                ),
                "reference_wallets": int(ref_mask.sum()),
                "recovered_wallets_after_matching": int(recovered.sum()),
                "recovery_rate": float(recovered.mean()) if ref_mask.any() else np.nan,
            }
        )

    return aligned, pd.DataFrame(match_rows)


def run_one(
    df: pd.DataFrame,
    scenario: str,
    removed_features: list[str],
    all_features: list[str],
    random_state: int,
    batch_size: int,
    n_init: int,
    max_iter: int,
) -> tuple[dict, pd.DataFrame]:
    retained = [c for c in all_features if c not in set(removed_features)]
    X = df[retained].to_numpy(dtype=np.float32, copy=True)
    reference = df["reference_cluster"].to_numpy(dtype=int)

    model = MiniBatchKMeans(
        n_clusters=5,
        random_state=random_state,
        batch_size=batch_size,
        n_init=n_init,
        max_iter=max_iter,
    )
    candidate = model.fit_predict(X)
    aligned, recovery = align_to_reference(reference, candidate)

    summary = {
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
    recovery.insert(0, "scenario", scenario)
    return summary, recovery


def write_report(
    summary: pd.DataFrame,
    recovery: pd.DataFrame,
    out_dir: Path,
    sample_size: int,
    random_state: int,
    batch_size: int,
    n_init: int,
    max_iter: int,
) -> None:
    run_scope = "full EOA population" if sample_size <= 0 else f"{sample_size:,}-wallet population-proportional sample"
    lines = [
        "# K5 Feature Holdout Validation",
        "",
        "## Purpose",
        "",
        "This analysis tests whether the Behavior K5 taxonomy is driven by one feature family alone.",
        f"For each holdout scenario, one behavioural feature group is removed, KMeans with K=5 is refit on the {run_scope}, and the resulting labels are aligned back to the reference Behavior K5 labels using Hungarian matching.",
        "The comparison uses ARI, NMI, exact agreement after matching, and per-role recovery rates.",
        "",
        "## Run Parameters",
        "",
        f"- Run scope: {run_scope}",
        f"- Random state: {random_state}",
        f"- MiniBatchKMeans batch size: {batch_size}",
        f"- MiniBatchKMeans n_init: {n_init}",
        f"- MiniBatchKMeans max_iter: {max_iter}",
        "",
        "## Summary",
        "",
        "| Scenario | Removed features | Retained features | ARI | NMI | Matched agreement | Mean recovery | Min recovery |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.removed_feature_count} | {row.retained_feature_count} | "
            f"{row.ari_vs_reference:.4f} | {row.nmi_vs_reference:.4f} | "
            f"{row.exact_agreement_after_matching:.4f} | "
            f"{row.mean_cluster_recovery_after_matching:.4f} | "
            f"{row.min_cluster_recovery_after_matching:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The holdout test is circularity-aware because it does not ask whether the original K5 clusters differ on the same features used to produce them.",
            "Instead, it asks whether a related five-role structure can still be recovered when one major behavioural feature family is removed.",
            "High agreement after a holdout suggests that the reference taxonomy is not dependent on that feature family alone.",
            "Low agreement identifies feature families that carry essential information for reproducing the K5 taxonomy.",
            "",
        ]
    )

    best = summary.sort_values("exact_agreement_after_matching", ascending=False).iloc[0]
    weakest = summary.sort_values("exact_agreement_after_matching", ascending=True).iloc[0]
    lines.extend(
        [
            f"The strongest holdout recovery is `{best['scenario']}` with matched agreement `{best['exact_agreement_after_matching']:.4f}`.",
            f"The weakest holdout recovery is `{weakest['scenario']}` with matched agreement `{weakest['exact_agreement_after_matching']:.4f}`.",
            "This means the paper should report the holdout validation as a robustness diagnostic rather than as proof that all feature groups are interchangeable.",
            "",
            "## Paper Wording",
            "",
            "To reduce circularity, we performed feature-family holdout validation.",
            "Each major feature family was removed in turn, KMeans with K=5 was refit, and the resulting partition was aligned to the reference Behavior K5 taxonomy.",
            "The results show which parts of the behavioural representation are necessary for recovering the taxonomy and whether the main roles persist when individual feature families are withheld.",
        ]
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "feature_holdout_summary.csv", index=False)
    recovery.to_csv(out_dir / "feature_holdout_cluster_recovery.csv", index=False)
    (out_dir / "feature_holdout_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run circularity-aware feature-family holdout validation for the EOA-only Behavior K5 taxonomy."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300_000,
        help="Number of wallets to sample. Use 0 to run on the full EOA population.",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory. Defaults to sample/full-specific results folder.",
    )
    parser.add_argument("--random-state", type=int, default=492)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--n-init", type=int, default=10)
    parser.add_argument("--max-iter", type=int, default=200)
    args = parser.parse_args()

    if args.out_dir:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = ROOT / out_dir
    elif args.sample_size <= 0:
        out_dir = ROOT / "results" / "k5_feature_holdout_validation_full"
    else:
        out_dir = OUT_DIR

    out_dir.mkdir(parents=True, exist_ok=True)
    all_features = feature_columns(FEATURES)
    df = load_population_sample(sample_size=args.sample_size, random_state=args.random_state)

    summaries = []
    recoveries = []
    baseline_summary, baseline_recovery = run_one(
        df,
        "all_features_resample_baseline",
        [],
        all_features,
        args.random_state,
        args.batch_size,
        args.n_init,
        args.max_iter,
    )
    summaries.append(baseline_summary)
    recoveries.append(baseline_recovery)

    for scenario, removed in FEATURE_GROUPS.items():
        missing = sorted(set(removed) - set(all_features))
        if missing:
            raise ValueError(f"{scenario} has missing features: {missing}")
        summary, recovery = run_one(
            df,
            scenario,
            removed,
            all_features,
            args.random_state,
            args.batch_size,
            args.n_init,
            args.max_iter,
        )
        summaries.append(summary)
        recoveries.append(recovery)

    summary_df = pd.DataFrame(summaries)
    recovery_df = pd.concat(recoveries, ignore_index=True)
    write_report(
        summary_df,
        recovery_df,
        out_dir,
        args.sample_size,
        args.random_state,
        args.batch_size,
        args.n_init,
        args.max_iter,
    )
    print(summary_df.to_string(index=False))
    print(f"\nSaved outputs to: {out_dir}")


if __name__ == "__main__":
    main()
