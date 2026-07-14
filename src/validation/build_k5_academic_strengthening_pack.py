import argparse
import sys
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

PROJECT_SRC = Path(__file__).resolve().parents[1]
FEATURE_SRC = PROJECT_SRC / "features"
if str(FEATURE_SRC) not in sys.path:
    sys.path.insert(0, str(FEATURE_SRC))

from build_full_kmeans6_expanded_features import aggregate_daily_features, derive_features, read_labels


MONTHS_2022 = [
    "202201",
    "202202",
    "202203",
    "202204",
    "202205",
    "202206",
    "202207",
    "202208",
    "202209",
    "202210",
    "202211",
    "202212",
]


def numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    banned = {"wallet", "cluster", "old_cluster", "first_active_date", "last_active_date"}
    return [col for col in df.columns if col not in banned and pd.api.types.is_numeric_dtype(df[col])]


def clean_wallet(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def load_feature_sample(
    features_path: Path,
    labels: pd.DataFrame,
    sample_per_cluster: int,
    random_state: int,
    chunksize: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    sampled_wallets = []
    for cluster, sub in labels.groupby("cluster"):
        n = min(sample_per_cluster, len(sub))
        idx = rng.choice(sub.index.to_numpy(), size=n, replace=False)
        sampled_wallets.append(labels.loc[idx, ["wallet", "cluster"]])
    sample_labels = pd.concat(sampled_wallets, ignore_index=True)
    wallet_set = set(sample_labels["wallet"])

    parts = []
    for chunk in pd.read_csv(features_path, dtype={"wallet": str}, chunksize=chunksize):
        chunk["wallet"] = clean_wallet(chunk["wallet"])
        chunk = chunk[chunk["wallet"].isin(wallet_set)].copy()
        if not chunk.empty:
            parts.append(chunk)

    if not parts:
        raise RuntimeError("No sampled wallets found in feature table.")

    features = pd.concat(parts, ignore_index=True)
    if "cluster" in features.columns:
        features = features.drop(columns=["cluster"])
    if "old_cluster" in features.columns:
        features = features.drop(columns=["old_cluster"])
    features = features.merge(sample_labels, on="wallet", how="inner")
    return features


def contingency_match(reference: np.ndarray, candidate: np.ndarray) -> tuple[dict[int, int], pd.DataFrame]:
    ref_labels = sorted(np.unique(reference))
    cand_labels = sorted(np.unique(candidate))
    table = pd.crosstab(pd.Series(reference, name="reference"), pd.Series(candidate, name="candidate"))
    table = table.reindex(index=ref_labels, columns=cand_labels, fill_value=0)
    row_ind, col_ind = linear_sum_assignment(-table.to_numpy())
    mapping = {cand_labels[c]: ref_labels[r] for r, c in zip(row_ind, col_ind)}
    return mapping, table


def build_consensus_stability(
    features: pd.DataFrame,
    feature_cols: list[str],
    out_dir: Path,
    k: int,
    seeds: list[int],
    pair_sample_size: int,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    X = (
        features[feature_cols]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .to_numpy(dtype=np.float32)
    )
    reference = features["cluster"].to_numpy(dtype=int)
    rng = np.random.default_rng(random_state)

    run_rows = []
    aligned_runs = []
    cluster_recovery_rows = []
    for seed in seeds:
        model = MiniBatchKMeans(
            n_clusters=k,
            random_state=seed,
            batch_size=8192,
            n_init=10,
            max_iter=200,
        )
        candidate = model.fit_predict(X)
        mapping, table = contingency_match(reference, candidate)
        aligned = np.array([mapping.get(c, -1) for c in candidate], dtype=int)
        aligned_runs.append(aligned)

        run_rows.append(
            {
                "seed": seed,
                "ari_vs_reference": adjusted_rand_score(reference, aligned),
                "nmi_vs_reference": normalized_mutual_info_score(reference, aligned),
                "exact_label_agreement_after_matching": float(np.mean(reference == aligned)),
            }
        )

        for ref_cluster in sorted(np.unique(reference)):
            mask = reference == ref_cluster
            cluster_recovery_rows.append(
                {
                    "seed": seed,
                    "cluster": ref_cluster,
                    "sample_wallets": int(mask.sum()),
                    "matched_recovery_rate": float(np.mean(aligned[mask] == ref_cluster)),
                }
            )

    run_summary = pd.DataFrame(run_rows)
    cluster_recovery = pd.DataFrame(cluster_recovery_rows)
    cluster_recovery_summary = (
        cluster_recovery.groupby("cluster")
        .agg(
            matched_recovery_mean=("matched_recovery_rate", "mean"),
            matched_recovery_min=("matched_recovery_rate", "min"),
            matched_recovery_max=("matched_recovery_rate", "max"),
            matched_recovery_std=("matched_recovery_rate", "std"),
            sample_wallets=("sample_wallets", "max"),
        )
        .reset_index()
    )

    n = len(reference)
    pairs_i = rng.integers(0, n, size=pair_sample_size)
    pairs_j = rng.integers(0, n, size=pair_sample_size)
    keep = pairs_i != pairs_j
    pairs_i = pairs_i[keep]
    pairs_j = pairs_j[keep]

    ref_same = reference[pairs_i] == reference[pairs_j]
    co_counts = np.zeros(len(pairs_i), dtype=np.int16)
    for aligned in aligned_runs:
        co_counts += (aligned[pairs_i] == aligned[pairs_j]).astype(np.int16)
    consensus = co_counts / len(aligned_runs)

    pair_rows = []
    for ref_pair_type, mask in [
        ("same_reference_cluster", ref_same),
        ("different_reference_cluster", ~ref_same),
    ]:
        vals = consensus[mask]
        pair_rows.append(
            {
                "pair_type": ref_pair_type,
                "sampled_pairs": int(mask.sum()),
                "mean_consensus": float(np.mean(vals)),
                "median_consensus": float(np.median(vals)),
                "share_consensus_ge_0_8": float(np.mean(vals >= 0.8)),
                "share_consensus_le_0_2": float(np.mean(vals <= 0.2)),
            }
        )

    for cluster in sorted(np.unique(reference)):
        mask = ref_same & (reference[pairs_i] == cluster)
        if mask.any():
            vals = consensus[mask]
            pair_rows.append(
                {
                    "pair_type": f"within_C{cluster}",
                    "sampled_pairs": int(mask.sum()),
                    "mean_consensus": float(np.mean(vals)),
                    "median_consensus": float(np.median(vals)),
                    "share_consensus_ge_0_8": float(np.mean(vals >= 0.8)),
                    "share_consensus_le_0_2": float(np.mean(vals <= 0.2)),
                }
            )

    pair_consensus = pd.DataFrame(pair_rows)

    run_summary.to_csv(out_dir / "consensus_seed_run_summary.csv", index=False)
    cluster_recovery.to_csv(out_dir / "per_seed_cluster_recovery.csv", index=False)
    cluster_recovery_summary.to_csv(out_dir / "per_cluster_consensus_recovery_summary.csv", index=False)
    pair_consensus.to_csv(out_dir / "sampled_pair_comembership_consensus.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    plot_df = pair_consensus[pair_consensus["pair_type"].str.startswith("within_C")]
    ax.bar(plot_df["pair_type"], plot_df["mean_consensus"], color="#287c74")
    ax.axhline(pair_consensus.loc[pair_consensus["pair_type"] == "different_reference_cluster", "mean_consensus"].iloc[0], color="#b33a1c", linestyle="--", label="different-cluster baseline")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Mean co-membership consensus")
    ax.set_title("K5 Cluster Co-Membership Stability")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "consensus_comembership_by_cluster.png", dpi=220)
    plt.close(fig)

    return run_summary, cluster_recovery_summary, pair_consensus


def build_trajectory_types(
    states_path: Path,
    cluster_file: Path,
    out_dir: Path,
    chunksize: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = read_labels(cluster_file)
    wallets = labels["wallet"].to_numpy()
    wallet_to_idx = {wallet: i for i, wallet in enumerate(wallets)}
    n = len(wallets)
    k = int(labels["cluster"].max()) + 1

    months_observed = np.zeros(n, dtype=np.int16)
    first_state = np.full(n, -1, dtype=np.int8)
    last_state = np.full(n, -1, dtype=np.int8)
    prev2_state = np.full(n, -1, dtype=np.int8)
    prev1_state = np.full(n, -1, dtype=np.int8)
    switch_count = np.zeros(n, dtype=np.int16)
    return_count = np.zeros(n, dtype=np.int16)
    state_counts = np.zeros((n, k), dtype=np.int16)

    usecols = ["wallet", "month", "monthly_state"]
    for chunk in pd.read_csv(states_path, usecols=usecols, dtype={"wallet": str, "month": str}, chunksize=chunksize):
        chunk["wallet"] = clean_wallet(chunk["wallet"])
        chunk["monthly_state"] = pd.to_numeric(chunk["monthly_state"], errors="coerce").fillna(-1).astype(np.int8)
        for wallet, state in zip(chunk["wallet"].to_numpy(), chunk["monthly_state"].to_numpy()):
            idx = wallet_to_idx.get(wallet)
            if idx is None or state < 0 or state >= k:
                continue
            if months_observed[idx] == 0:
                first_state[idx] = state
            else:
                if last_state[idx] != state:
                    switch_count[idx] += 1
                if months_observed[idx] >= 2 and prev2_state[idx] != prev1_state[idx] and state == prev2_state[idx]:
                    return_count[idx] += 1
            prev2_state[idx] = prev1_state[idx]
            prev1_state[idx] = state
            last_state[idx] = state
            state_counts[idx, state] += 1
            months_observed[idx] += 1

    dominant_state = np.argmax(state_counts, axis=1).astype(np.int8)
    dominant_count = state_counts[np.arange(n), dominant_state]
    dominant_share = np.divide(
        dominant_count,
        months_observed,
        out=np.zeros(n, dtype=float),
        where=months_observed > 0,
    )

    trajectory_type = np.full(n, "multi_step_mover", dtype=object)
    trajectory_type[months_observed < 2] = "insufficient_observation"
    trajectory_type[(months_observed >= 2) & (switch_count == 0)] = "persistent"
    trajectory_type[(months_observed >= 2) & (switch_count > 0) & (return_count > 0)] = "returner"
    trajectory_type[(months_observed >= 2) & (switch_count == 1) & (return_count == 0)] = "one_time_switcher"
    trajectory_type[
        (months_observed >= 2)
        & (switch_count > 1)
        & (return_count == 0)
        & (dominant_share >= 0.7)
    ] = "mostly_stable_with_noise"
    trajectory_type[
        (months_observed >= 2)
        & (switch_count >= np.maximum(3, months_observed // 2))
        & (return_count == 0)
        & (dominant_share < 0.7)
    ] = "volatile_switcher"

    wallet_trajectory = pd.DataFrame(
        {
            "wallet": wallets,
            "months_observed": months_observed,
            "start_state": first_state,
            "end_state": last_state,
            "dominant_state": dominant_state,
            "dominant_state_share": dominant_share,
            "switch_count": switch_count,
            "two_step_return_count": return_count,
            "trajectory_type": trajectory_type,
        }
    )
    wallet_trajectory = wallet_trajectory[wallet_trajectory["months_observed"] > 0].copy()
    summary = (
        wallet_trajectory.groupby("trajectory_type")
        .agg(
            wallet_count=("wallet", "count"),
            mean_months_observed=("months_observed", "mean"),
            mean_switch_count=("switch_count", "mean"),
            mean_two_step_return_count=("two_step_return_count", "mean"),
        )
        .reset_index()
    )
    summary["wallet_share"] = summary["wallet_count"] / len(wallet_trajectory)
    summary = summary.sort_values("wallet_count", ascending=False)

    by_start = (
        wallet_trajectory.groupby(["start_state", "trajectory_type"])
        .size()
        .reset_index(name="wallet_count")
        .sort_values(["start_state", "wallet_count"], ascending=[True, False])
    )
    by_start["share_within_start_state"] = by_start["wallet_count"] / by_start.groupby("start_state")["wallet_count"].transform("sum")

    wallet_trajectory.to_csv(out_dir / "wallet_trajectory_types.csv", index=False)
    summary.to_csv(out_dir / "trajectory_type_summary.csv", index=False)
    by_start.to_csv(out_dir / "trajectory_type_by_start_state.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(summary["trajectory_type"], summary["wallet_share"], color="#466a9f")
    ax.set_ylabel("Wallet share")
    ax.set_title("K5 Monthly Wallet Trajectory Types")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(out_dir / "trajectory_type_shares.png", dpi=220)
    plt.close(fig)

    return summary, by_start


def load_scaling_stats(path: Path) -> dict:
    stats = pd.read_csv(path)
    return stats.set_index("feature").to_dict(orient="index")


def transform_with_stats(name: str, series: pd.Series, stats: dict) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    meta = stats[name]
    transform_type = meta["transform_type"]
    if transform_type == "log1p":
        transformed = np.log1p(s)
    elif transform_type == "signed_log1p":
        transformed = np.sign(s) * np.log1p(np.abs(s))
    elif transform_type == "raw":
        transformed = s
    else:
        raise ValueError(f"Unknown transform_type for {name}: {transform_type}")

    iqr = meta["iqr"]
    if pd.isna(iqr) or iqr == 0:
        return transformed - meta["median"]
    return (transformed - meta["median"]) / iqr


def scale_monthly_features(month_features: pd.DataFrame, stats: dict, feature_cols: list[str]) -> pd.DataFrame:
    out = month_features[["wallet"]].copy()
    for col in feature_cols:
        if col in month_features.columns and col in stats:
            out[col] = transform_with_stats(col, month_features[col], stats).astype("float32")
    return out


def build_centroid_drift(
    data_dir: Path,
    labels: pd.DataFrame,
    assignments_path: Path,
    centroids_path: Path,
    scaling_stats_path: Path,
    out_dir: Path,
    chunksize: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    centroids = pd.read_csv(centroids_path, index_col=0)
    centroids.index = centroids.index.astype(int)
    stats = load_scaling_stats(scaling_stats_path)
    feature_cols = [col for col in centroids.columns if col in stats]

    states = pd.read_csv(
        assignments_path,
        usecols=["wallet", "month", "monthly_state"],
        dtype={"wallet": str, "month": str},
    )
    states["wallet"] = clean_wallet(states["wallet"])
    states["monthly_state"] = states["monthly_state"].astype(int)

    drift_rows = []
    profile_parts = []
    for month in MONTHS_2022:
        daily_file = data_dir / f"wallet_daily_clean_{month}.csv"
        if not daily_file.exists():
            daily_file = data_dir / f"wallet_daily_{month}.csv"
        if not daily_file.exists():
            raise FileNotFoundError(f"Missing monthly daily file for {month}")

        print(f"centroid_drift month={month} daily_file={daily_file}", flush=True)
        agg, total_rows, kept_rows = aggregate_daily_features(daily_file, labels, chunksize)
        month_features = derive_features(agg)
        month_scaled = scale_monthly_features(month_features, stats, feature_cols)
        month_states = states[states["month"] == month][["wallet", "monthly_state"]]
        merged = month_scaled.merge(month_states, on="wallet", how="inner")

        monthly_profiles = merged.groupby("monthly_state")[feature_cols].median().sort_index()
        monthly_profiles["month"] = month
        monthly_profiles["monthly_state"] = monthly_profiles.index
        profile_parts.append(monthly_profiles.reset_index(drop=True))

        for state, row in monthly_profiles[feature_cols].iterrows():
            centroid = centroids.loc[int(state), feature_cols]
            diffs = row - centroid
            abs_diffs = diffs.abs().sort_values(ascending=False)
            drift_rows.append(
                {
                    "month": month,
                    "cluster": int(state),
                    "active_wallets_in_state": int((merged["monthly_state"] == state).sum()),
                    "centroid_l2_distance": float(np.sqrt(np.sum(np.square(diffs.to_numpy(dtype=float))))),
                    "centroid_l1_mean_abs_distance": float(abs_diffs.mean()),
                    "top_drift_features": "; ".join(f"{idx}={val:.3f}" for idx, val in abs_diffs.head(5).items()),
                    "daily_rows_read": total_rows,
                    "daily_rows_matching_cluster_wallets": kept_rows,
                }
            )

    drift = pd.DataFrame(drift_rows)
    profiles = pd.concat(profile_parts, ignore_index=True)
    summary = (
        drift.groupby("cluster")
        .agg(
            mean_l2_drift=("centroid_l2_distance", "mean"),
            max_l2_drift=("centroid_l2_distance", "max"),
            min_l2_drift=("centroid_l2_distance", "min"),
            mean_l1_abs_drift=("centroid_l1_mean_abs_distance", "mean"),
            max_drift_month=("month", lambda s: drift.loc[s.index, "centroid_l2_distance"].idxmax()),
        )
        .reset_index()
    )
    summary["max_drift_month"] = summary["max_drift_month"].map(drift["month"])

    drift.to_csv(out_dir / "monthly_centroid_drift.csv", index=False)
    profiles.to_csv(out_dir / "monthly_state_feature_median_profiles.csv", index=False)
    summary.to_csv(out_dir / "centroid_drift_summary_by_cluster.csv", index=False)

    pivot = drift.pivot(index="month", columns="cluster", values="centroid_l2_distance")
    fig, ax = plt.subplots(figsize=(9, 5))
    for cluster in pivot.columns:
        ax.plot(pivot.index, pivot[cluster], marker="o", label=f"C{cluster}")
    ax.set_ylabel("L2 distance from full-year centroid")
    ax.set_title("K5 Monthly Centroid Drift")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(ncol=3)
    fig.tight_layout()
    fig.savefig(out_dir / "monthly_centroid_drift.png", dpi=220)
    plt.close(fig)

    return drift, summary


def build_per_cluster_and_role_tables(
    out_dir: Path,
    role_labels_path: Path,
    temporal_stability_path: Path,
    network_centrality_path: Path,
    cluster_recovery_summary: pd.DataFrame,
    trajectory_by_start: pd.DataFrame,
    centroid_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    roles = pd.read_csv(role_labels_path)
    temporal = pd.read_csv(temporal_stability_path).rename(columns={"from_state": "cluster"})
    network = pd.read_csv(network_centrality_path)

    dominant_trajectory = (
        trajectory_by_start.sort_values(["start_state", "wallet_count"], ascending=[True, False])
        .groupby("start_state")
        .head(1)
        .rename(
            columns={
                "start_state": "cluster",
                "trajectory_type": "dominant_trajectory_type",
                "share_within_start_state": "dominant_trajectory_share",
            }
        )[["cluster", "dominant_trajectory_type", "dominant_trajectory_share"]]
    )

    table = (
        roles.merge(temporal, on="cluster", how="left")
        .merge(network, on="cluster", how="left")
        .merge(cluster_recovery_summary, on="cluster", how="left")
        .merge(centroid_summary, on="cluster", how="left")
        .merge(dominant_trajectory, on="cluster", how="left")
    )

    def reliability(row: pd.Series) -> str:
        score = 0
        score += row.get("matched_recovery_mean", 0) >= 0.7 and row.get("matched_recovery_min", 0) >= 0.5
        score += row.get("self_transition_probability", 0) >= 0.45
        score += row.get("mean_l2_drift", np.inf) <= table["mean_l2_drift"].median()
        if score >= 3:
            return "strong"
        if score == 2:
            return "moderate"
        return "fragile"

    def caution(row: pd.Series) -> str:
        notes = []
        if row.get("wallet_share", 1) < 0.08:
            notes.append("small role")
        if row.get("self_transition_probability", 1) < 0.4:
            notes.append("low temporal persistence")
        if row.get("matched_recovery_mean", 1) < 0.6:
            notes.append("lower seed/subsample recovery")
        elif row.get("matched_recovery_min", 1) < 0.4:
            notes.append("seed-sensitive in at least one rerun")
        if row.get("mean_l2_drift", 0) > table["mean_l2_drift"].median():
            notes.append("higher monthly centroid drift")
        return "; ".join(notes) if notes else "no major caution under tested checks"

    table["role_reliability_summary"] = table.apply(reliability, axis=1)
    table["interpretation_caution"] = table.apply(caution, axis=1)

    per_cluster = table[
        [
            "cluster",
            "behavior_label",
            "wallet_count",
            "wallet_share",
            "matched_recovery_mean",
            "matched_recovery_min",
            "self_transition_probability",
            "transition_entropy_bits",
            "mean_l2_drift",
            "max_l2_drift",
            "dominant_trajectory_type",
            "dominant_trajectory_share",
            "net_external_in_minus_out",
            "role_reliability_summary",
            "interpretation_caution",
        ]
    ].copy()

    final_role_table = table[
        [
            "cluster",
            "behavior_label",
            "wallet_share",
            "top_high_features",
            "top_low_features",
            "self_transition_probability",
            "top_destinations",
            "net_external_in_minus_out",
            "matched_recovery_mean",
            "mean_l2_drift",
            "dominant_trajectory_type",
            "role_reliability_summary",
            "interpretation_caution",
        ]
    ].copy()

    per_cluster.to_csv(out_dir / "per_cluster_stability_table.csv", index=False)
    final_role_table.to_csv(out_dir / "final_k5_role_interpretation_table.csv", index=False)
    return per_cluster, final_role_table


def write_report(
    out_dir: Path,
    run_summary: pd.DataFrame,
    pair_consensus: pd.DataFrame,
    trajectory_summary: pd.DataFrame,
    centroid_summary: pd.DataFrame,
    per_cluster: pd.DataFrame,
    final_role_table: pd.DataFrame,
) -> None:
    lines = [
        "# K5 Academic Strengthening Pack",
        "",
        "## Purpose",
        "",
        "This pack adds the remaining paper-strengthening analyses for the EOA-only K5 role taxonomy: per-cluster stability, consensus/co-membership stability, wallet trajectory types, centroid drift, and a consolidated role table.",
        "",
        "## Consensus And Co-Membership Stability",
        "",
        "KMeans was rerun on a stratified wallet sample using multiple random seeds. Candidate clusters were aligned back to the reference K5 labels with Hungarian matching, then ARI, NMI, exact matched agreement, per-cluster recovery, and sampled pair co-membership consensus were computed.",
        "",
        run_summary.describe().to_markdown(),
        "",
        "### Pair Co-Membership Consensus",
        "",
        pair_consensus.to_markdown(index=False),
        "",
        "Interpretation: high within-cluster consensus means wallets assigned to the same reference role tend to remain together across reruns. A low different-cluster consensus baseline means the model is not simply putting most wallets together regardless of role.",
        "",
        "## Wallet Trajectory Types",
        "",
        trajectory_summary.to_markdown(index=False),
        "",
        "Interpretation: this converts monthly state sequences into readable behavioural patterns. It complements the two-step return test by showing whether wallets are persistent, returners, one-time switchers, or more volatile movers.",
        "",
        "## Monthly Centroid Drift",
        "",
        centroid_summary.to_markdown(index=False),
        "",
        "Interpretation: centroid drift checks whether each monthly state has the same feature meaning as its full-year prototype. Higher drift means the role is more context-sensitive and should be described cautiously.",
        "",
        "## Per-Cluster Stability Table",
        "",
        per_cluster.to_markdown(index=False),
        "",
        "## Final K5 Role Interpretation Table",
        "",
        final_role_table.to_markdown(index=False),
        "",
        "## Paper-Ready Claim",
        "",
        "The K5 taxonomy is best described as a behaviour-state taxonomy rather than a transaction-community partition. Its strongest support comes from feature-space separation, seed/subsample recovery, monthly persistence, and structured temporal trajectories. Network evidence should remain calibrated because K5 role-to-role flows are structured, but same-role transaction concentration was not stronger than the shuffled-label null test.",
    ]
    (out_dir / "k5_academic_strengthening_report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the K5 academic-strengthening analysis pack.")
    parser.add_argument("--features", default="wallet_eoa_only_kmeans6_features_robust_scaled/wallet_eoa_only_kmeans6_features_robust_scaled.csv")
    parser.add_argument("--cluster-file", default="results/eoa_only_kmeans5/wallet_eoa_only_kmeans_clusters.csv")
    parser.add_argument("--role-labels", default="results/eoa_only_kmeans5/cluster_descriptions/eoa_only_cluster_behavior_labels.csv")
    parser.add_argument("--centroids", default="results/eoa_only_kmeans5/cluster_feature_medians_robust_scaled.csv")
    parser.add_argument("--scaling-stats", default="../dataverse_files/wallet_kmeans6_expanded_daily_features_robust_scaled_scaling_stats.csv")
    parser.add_argument("--daily-data-dir", default="../dataverse_files")
    parser.add_argument("--temporal-states", default="results/eoa_only_kmeans5/temporal_validation/wallet_monthly_behavior_states.csv")
    parser.add_argument("--temporal-stability", default="results/eoa_only_kmeans5/temporal_validation/state_transition_stability.csv")
    parser.add_argument("--network-centrality", default="results/eoa_only_kmeans5/network_validation/cluster_network_centrality.csv")
    parser.add_argument("--out-dir", default="results/k5_academic_strengthening")
    parser.add_argument("--sample-per-cluster", type=int, default=5000)
    parser.add_argument("--pair-sample-size", type=int, default=250000)
    parser.add_argument("--seeds", default="101,202,303,404,505,606,707,808")
    parser.add_argument("--random-state", type=int, default=492)
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    labels = read_labels(Path(args.cluster_file))
    seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]

    consensus_files = [
        out_dir / "consensus_seed_run_summary.csv",
        out_dir / "per_cluster_consensus_recovery_summary.csv",
        out_dir / "sampled_pair_comembership_consensus.csv",
    ]
    if all(path.exists() for path in consensus_files):
        run_summary = pd.read_csv(consensus_files[0])
        cluster_recovery_summary = pd.read_csv(consensus_files[1])
        pair_consensus = pd.read_csv(consensus_files[2])
        print("Loaded existing consensus outputs.", flush=True)
    else:
        sample = load_feature_sample(
            Path(args.features),
            labels,
            args.sample_per_cluster,
            args.random_state,
            args.chunksize,
        )
        feature_cols = numeric_feature_columns(sample)
        run_summary, cluster_recovery_summary, pair_consensus = build_consensus_stability(
            sample,
            feature_cols,
            out_dir,
            k=5,
            seeds=seeds,
            pair_sample_size=args.pair_sample_size,
            random_state=args.random_state,
        )

    trajectory_files = [
        out_dir / "trajectory_type_summary.csv",
        out_dir / "trajectory_type_by_start_state.csv",
    ]
    if all(path.exists() for path in trajectory_files):
        trajectory_summary = pd.read_csv(trajectory_files[0])
        trajectory_by_start = pd.read_csv(trajectory_files[1])
        print("Loaded existing trajectory outputs.", flush=True)
    else:
        trajectory_summary, trajectory_by_start = build_trajectory_types(
            Path(args.temporal_states),
            Path(args.cluster_file),
            out_dir,
            chunksize=args.chunksize,
        )

    centroid_files = [
        out_dir / "monthly_centroid_drift.csv",
        out_dir / "centroid_drift_summary_by_cluster.csv",
    ]
    if all(path.exists() for path in centroid_files):
        centroid_summary = pd.read_csv(centroid_files[1])
        print("Loaded existing centroid drift outputs.", flush=True)
    else:
        _, centroid_summary = build_centroid_drift(
            Path(args.daily_data_dir),
            labels,
            Path(args.temporal_states),
            Path(args.centroids),
            Path(args.scaling_stats),
            out_dir,
            chunksize=args.chunksize,
        )

    per_cluster, final_role_table = build_per_cluster_and_role_tables(
        out_dir,
        Path(args.role_labels),
        Path(args.temporal_stability),
        Path(args.network_centrality),
        cluster_recovery_summary,
        trajectory_by_start,
        centroid_summary,
    )

    write_report(
        out_dir,
        run_summary,
        pair_consensus,
        trajectory_summary,
        centroid_summary,
        per_cluster,
        final_role_table,
    )

    print(f"Saved K5 academic-strengthening pack to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
