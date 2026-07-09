from pathlib import Path
import json
import math
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.preprocessing import RobustScaler


warnings.filterwarnings("ignore")


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "paper_process_outputs"
OUT.mkdir(exist_ok=True)

RNG = np.random.default_rng(492)


def max_overlap_score(a, b):
    table = pd.crosstab(a, b)
    cost = -table.to_numpy()
    row_ind, col_ind = linear_sum_assignment(cost)
    matched = int(table.to_numpy()[row_ind, col_ind].sum())
    total = int(table.to_numpy().sum())
    score = matched / total if total else np.nan
    pairs = []
    for r, c in zip(row_ind, col_ind):
        pairs.append(
            {
                "cluster_a": table.index[r],
                "cluster_b": table.columns[c],
                "matched_wallets": int(table.iloc[r, c]),
                "cluster_a_size": int(table.iloc[r, :].sum()),
                "cluster_b_size": int(table.iloc[:, c].sum()),
                "share_of_cluster_a": float(table.iloc[r, c] / table.iloc[r, :].sum()),
                "share_of_cluster_b": float(table.iloc[r, c] / table.iloc[:, c].sum()),
            }
        )
    return score, table, pd.DataFrame(pairs)


def correspondence_permutation_test(n_perm=1000):
    labels_path = ROOT / "clustering" / "202209" / "merged_cluster_labels_202209.csv"
    df = pd.read_csv(labels_path, usecols=["wallet", "cluster_1", "cluster_2"])
    df = df.dropna(subset=["cluster_1", "cluster_2"]).copy()
    df["cluster_1"] = df["cluster_1"].astype(int)
    df["cluster_2"] = df["cluster_2"].astype(int)

    observed_score, table, pairs = max_overlap_score(df["cluster_1"], df["cluster_2"])
    ari = adjusted_rand_score(df["cluster_1"], df["cluster_2"])
    nmi = normalized_mutual_info_score(df["cluster_1"], df["cluster_2"])

    null_scores = np.empty(n_perm, dtype=float)
    b = df["cluster_2"].to_numpy(copy=True)
    a = df["cluster_1"].to_numpy(copy=False)
    for i in range(n_perm):
        permuted = RNG.permutation(b)
        null_scores[i], _, _ = max_overlap_score(a, permuted)

    p_value = (1 + np.sum(null_scores >= observed_score)) / (n_perm + 1)
    z_score = (observed_score - null_scores.mean()) / null_scores.std(ddof=1)

    summary = pd.DataFrame(
        [
            {
                "n_wallets": len(df),
                "cluster_a": "cluster_1",
                "cluster_b": "cluster_2",
                "observed_max_bipartite_overlap": observed_score,
                "observed_matched_wallets": int(round(observed_score * len(df))),
                "adjusted_rand_index": ari,
                "normalized_mutual_information": nmi,
                "permutations": n_perm,
                "null_mean": float(null_scores.mean()),
                "null_std": float(null_scores.std(ddof=1)),
                "null_95pct_lower": float(np.quantile(null_scores, 0.025)),
                "null_95pct_upper": float(np.quantile(null_scores, 0.975)),
                "z_score": float(z_score),
                "empirical_right_tail_p_value": float(p_value),
            }
        ]
    )

    table.to_csv(OUT / "cross_dataset_cluster_crosstab_counts.csv")
    pairs.to_csv(OUT / "cross_dataset_bipartite_matching_pairs.csv", index=False)
    pd.DataFrame({"null_correspondence_score": null_scores}).to_csv(
        OUT / "cross_dataset_correspondence_permutation_null.csv", index=False
    )
    summary.to_csv(OUT / "cross_dataset_correspondence_permutation_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.hist(null_scores, bins=40, color="#9db4c8", edgecolor="white")
    ax.axvline(observed_score, color="#b23a48", linewidth=2.5, label=f"Observed = {observed_score:.3f}")
    ax.set_title("Cross-dataset cluster correspondence vs randomized labels")
    ax.set_xlabel("Maximum bipartite overlap score")
    ax.set_ylabel("Permutation count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "cross_dataset_correspondence_permutation_null.png", dpi=220)
    plt.close(fig)

    return summary.iloc[0].to_dict()


def distance_metric_consensus():
    path = ROOT / "clustering" / "202209" / "distance_comparison_results_202209_corrected" / "all_metric_matches_combined_202209.csv"
    df = pd.read_csv(path)
    matched = df[df["status"] == "matched"].copy()
    matched["cluster_1"] = matched["cluster_1"].astype(int)
    matched["cluster_2"] = matched["cluster_2"].astype(int)

    consensus = (
        matched.groupby(["cluster_1", "cluster_2"])
        .agg(metric_count=("metric", "nunique"), metrics=("metric", lambda s: "; ".join(sorted(s.unique()))), mean_distance=("distance", "mean"))
        .reset_index()
        .sort_values(["metric_count", "cluster_1"], ascending=[False, True])
    )
    consensus["paper_rule_status"] = np.where(consensus["metric_count"] >= 3, "core_correspondence", "metric_specific_match")
    consensus.to_csv(OUT / "distance_metric_consensus_matches.csv", index=False)

    method = """# Formal Cluster Correspondence Rule

Cluster correspondence is defined in two layers.

First, for each distance metric, construct a cluster-to-cluster distance matrix between the source clustering and the target clustering.

Second, solve a maximum bipartite matching problem on that matrix, using the Hungarian algorithm, so each source cluster is matched to at most one target cluster.

For label-overlap validation, correspondence is measured as the share of wallets recovered by the best bipartite alignment between the two labelings.

The paper-ready statistic is:

`Correspondence = matched wallets under optimal one-to-one cluster alignment / total overlapping wallets`.

A pair is treated as a core correspondence when it appears under at least three of the four distance metrics: cosine, weighted Euclidean, Mahalanobis, and Wasserstein.

The statistical significance of the label-overlap correspondence is tested by randomly permuting one clustering's labels while preserving cluster sizes, recomputing the optimal bipartite overlap, and comparing the observed score to this null distribution.
"""
    (OUT / "formal_cluster_correspondence_definition.md").write_text(method, encoding="utf-8")
    return consensus


def temporal_stability_summary():
    trans = pd.read_csv(ROOT / "dataverse_files" / "cluster_transition_analysis_expanded" / "monthly_transition_summary.csv")
    state = pd.read_csv(ROOT / "dataverse_files" / "cluster_transition_analysis_expanded" / "state_transition_stability.csv")
    overall = pd.read_csv(ROOT / "dataverse_files" / "cluster_transition_analysis_expanded" / "overall_transition_probability_matrix.csv", index_col=0)
    trans["month_transition"] = trans["from_month"].astype(str) + " -> " + trans["to_month"].astype(str)

    paper = pd.DataFrame(
        [
            {
                "month_transition_count": len(trans),
                "total_consecutive_wallet_month_pairs": int(trans["wallets_in_both_months"].sum()),
                "mean_monthly_self_transition_rate": float(trans["self_transition_rate"].mean()),
                "min_monthly_self_transition_rate": float(trans["self_transition_rate"].min()),
                "max_monthly_self_transition_rate": float(trans["self_transition_rate"].max()),
                "most_stable_state": f"C{int(state.sort_values('self_transition_probability', ascending=False).iloc[0]['from_state'])}",
                "most_stable_state_probability": float(state["self_transition_probability"].max()),
                "least_stable_state": f"C{int(state.sort_values('self_transition_probability').iloc[0]['from_state'])}",
                "least_stable_state_probability": float(state["self_transition_probability"].min()),
            }
        ]
    )
    paper.to_csv(OUT / "paper_ready_temporal_stability_summary.csv", index=False)
    trans.to_csv(OUT / "paper_ready_monthly_retention_rates.csv", index=False)
    state.to_csv(OUT / "paper_ready_state_retention_rates.csv", index=False)
    overall.to_csv(OUT / "paper_ready_transition_probability_matrix.csv")

    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.plot(trans["month_transition"], trans["self_transition_rate"], marker="o", color="#2f6f73")
    ax.set_ylim(0, max(0.6, trans["self_transition_rate"].max() + 0.05))
    ax.set_ylabel("Self-transition rate")
    ax.set_xlabel("Month transition")
    ax.set_title("Individual wallet monthly retention rate")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(OUT / "paper_ready_monthly_retention_rates.png", dpi=220)
    plt.close(fig)
    return paper.iloc[0].to_dict()


def cross_feature_spearman(sample_mod=20):
    old_path = ROOT / "dataverse_files" / "wallet_kmeans_clusters.csv"
    new_path = ROOT / "dataverse_files" / "wallet_kmeans6_expanded_daily_features_robust_scaled.csv"

    old_features = [
        "active_days",
        "activity_span",
        "activity_density",
        "total_tx",
        "avg_tx_per_day",
        "avg_tx_size",
        "net_flow",
        "in_out_ratio",
        "burstiness",
        "flow_volatility",
        "tx_size_volatility",
        "directionality",
    ]
    new_features = [
        "active_days_observed",
        "activity_span_days",
        "activity_density",
        "total_tx",
        "total_in_sum",
        "total_out_sum",
        "total_net_flow_sum",
        "total_flow_sum",
        "avg_daily_tx_count",
        "avg_daily_total_in",
        "avg_daily_total_out",
        "avg_daily_net_flow",
        "avg_daily_total_flow",
        "max_daily_tx_count",
        "max_daily_total_in",
        "max_daily_total_out",
        "max_daily_total_flow",
        "std_daily_tx_count",
        "std_daily_total_in",
        "std_daily_total_out",
        "std_daily_net_flow",
        "std_daily_total_flow",
        "in_active_days",
        "out_active_days",
        "both_active_days",
        "in_active_day_ratio",
        "out_active_day_ratio",
        "both_active_day_ratio",
        "in_out_day_balance",
        "tx_count_cv",
        "total_flow_cv",
        "tx_concentration_ratio",
        "flow_concentration_ratio",
    ]

    old_parts = []
    for chunk in pd.read_csv(old_path, usecols=["wallet"] + old_features, chunksize=250_000):
        wallet_hash = pd.util.hash_pandas_object(chunk["wallet"].astype(str), index=False)
        old_parts.append(chunk[wallet_hash % sample_mod == 0])
    old = pd.concat(old_parts, ignore_index=True)
    old["wallet"] = old["wallet"].astype(str)
    old = old.rename(columns={c: f"old_{c}" for c in old_features})
    wanted = set(old["wallet"].tolist())

    new_parts = []
    for chunk in pd.read_csv(new_path, usecols=["wallet"] + new_features, chunksize=250_000):
        chunk["wallet"] = chunk["wallet"].astype(str)
        sub = chunk[chunk["wallet"].isin(wanted)]
        if not sub.empty:
            new_parts.append(sub)
    new = pd.concat(new_parts, ignore_index=True)
    new = new.rename(columns={c: f"new_{c}" for c in new_features})

    merged = old.merge(new, on="wallet")
    old_prefixed = [f"old_{c}" for c in old_features]
    new_prefixed = [f"new_{c}" for c in new_features]
    for c in old_prefixed + new_prefixed:
        if c in merged:
            merged[c] = pd.to_numeric(merged[c], errors="coerce")

    corr = pd.DataFrame(index=old_prefixed, columns=new_prefixed, dtype=float)
    for old_f in old_prefixed:
        for new_f in new_prefixed:
            corr.loc[old_f, new_f] = merged[old_f].corr(merged[new_f], method="spearman")

    corr.to_csv(OUT / "cross_feature_set_spearman_correlation_matrix.csv")

    max_abs = (
        corr.abs()
        .stack()
        .reset_index()
        .rename(columns={"level_0": "feature_set_a", "level_1": "feature_set_b", 0: "abs_spearman"})
        .sort_values("abs_spearman", ascending=False)
    )
    max_abs.to_csv(OUT / "cross_feature_set_top_absolute_correlations.csv", index=False)

    fig, ax = plt.subplots(figsize=(12, 5.5))
    im = ax.imshow(corr.astype(float), aspect="auto", cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_yticks(np.arange(len(old_prefixed)))
    ax.set_yticklabels(old_prefixed, fontsize=8)
    ax.set_xticks(np.arange(len(new_prefixed)))
    ax.set_xticklabels(new_prefixed, fontsize=7, rotation=60, ha="right")
    ax.set_title(f"Spearman correlation between original and expanded feature sets (n={len(merged):,})")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    fig.tight_layout()
    fig.savefig(OUT / "cross_feature_set_spearman_heatmap.png", dpi=220)
    plt.close(fig)

    summary = {
        "sample_mod": sample_mod,
        "sampled_wallets": int(len(merged)),
        "mean_abs_spearman": float(corr.abs().stack().mean()),
        "median_abs_spearman": float(corr.abs().stack().median()),
        "max_abs_spearman": float(corr.abs().stack().max()),
        "share_abs_corr_ge_0_8": float((corr.abs().stack() >= 0.8).mean()),
        "share_abs_corr_ge_0_6": float((corr.abs().stack() >= 0.6).mean()),
    }
    pd.DataFrame([summary]).to_csv(OUT / "cross_feature_set_spearman_summary.csv", index=False)
    return summary


def observation_density_experiment(repeats=5):
    interval_path = ROOT / "clustering" / "202209" / "202209_interval_clustered_common_202209.csv"
    ref_path = ROOT / "clustering" / "202209" / "merged_cluster_labels_202209.csv"
    features = [
        "tx_count",
        "sent_tx_count",
        "received_tx_count",
        "unique_recipients",
        "unique_senders",
        "sent_amount",
        "received_amount",
        "max_value",
        "active_days",
        "tokens_used",
    ]

    df = pd.read_csv(interval_path, usecols=["wallet"] + features)
    ref = pd.read_csv(ref_path, usecols=["wallet", "cluster_1", "cluster_2"])
    df = df.merge(ref, on="wallet", how="inner")

    fractions = [0.10, 0.25, 0.50, 0.75, 1.00]
    rows = []
    for frac in fractions:
        for rep in range(repeats):
            if frac >= 1.0:
                sub = df.copy()
            else:
                sub = df.sample(frac=frac, random_state=492 + rep + int(frac * 1000))

            X = sub[features].replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy(dtype=float)
            X = np.log1p(np.clip(X, a_min=0, a_max=None))
            X = RobustScaler().fit_transform(X)
            km = MiniBatchKMeans(n_clusters=5, random_state=492 + rep, batch_size=8192, n_init=10, max_iter=200)
            labels = km.fit_predict(X)
            overlap_c1, _, _ = max_overlap_score(labels, sub["cluster_1"].astype(int))
            overlap_c2, _, _ = max_overlap_score(labels, sub["cluster_2"].astype(int))
            sil = np.nan
            if len(sub) > 10_000:
                idx = RNG.choice(len(sub), size=10_000, replace=False)
                sil = silhouette_score(X[idx], labels[idx])
            elif len(sub) > 20:
                sil = silhouette_score(X, labels)
            rows.append(
                {
                    "fraction": frac,
                    "repeat": rep + 1,
                    "n_wallets": len(sub),
                    "correspondence_to_cluster_1": overlap_c1,
                    "correspondence_to_cluster_2": overlap_c2,
                    "silhouette_sample": sil,
                    "inertia": float(km.inertia_),
                }
            )

    result = pd.DataFrame(rows)
    result.to_csv(OUT / "minimum_observation_experiment_runs.csv", index=False)
    summary = (
        result.groupby("fraction")
        .agg(
            n_wallets_mean=("n_wallets", "mean"),
            correspondence_to_cluster_1_mean=("correspondence_to_cluster_1", "mean"),
            correspondence_to_cluster_1_std=("correspondence_to_cluster_1", "std"),
            correspondence_to_cluster_2_mean=("correspondence_to_cluster_2", "mean"),
            correspondence_to_cluster_2_std=("correspondence_to_cluster_2", "std"),
            silhouette_mean=("silhouette_sample", "mean"),
            silhouette_std=("silhouette_sample", "std"),
        )
        .reset_index()
    )
    summary.to_csv(OUT / "minimum_observation_experiment_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.errorbar(
        summary["fraction"] * 100,
        summary["correspondence_to_cluster_1_mean"],
        yerr=summary["correspondence_to_cluster_1_std"].fillna(0),
        marker="o",
        label="vs cluster_1",
        color="#2f6f73",
    )
    ax.errorbar(
        summary["fraction"] * 100,
        summary["correspondence_to_cluster_2_mean"],
        yerr=summary["correspondence_to_cluster_2_std"].fillna(0),
        marker="s",
        label="vs cluster_2",
        color="#b56b45",
    )
    ax.set_xlabel("Sparse interval data retained (%)")
    ax.set_ylabel("Best bipartite label-overlap correspondence")
    ax.set_title("Minimum observation experiment")
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "minimum_observation_correspondence_curve.png", dpi=220)
    plt.close(fig)
    return summary


def write_master_summary(results):
    lines = [
        "# Paper Process Remaining Analyses Summary",
        "",
        "## Completed in this run",
        "",
        "1. Cross-dataset cluster correspondence permutation test.",
        "2. Formal cluster correspondence definition and metric consensus table.",
        "3. Paper-ready individual temporal stability summaries from existing transition outputs.",
        "4. Cross-feature-set Spearman correlation analysis on overlapping sampled wallets.",
        "5. Minimum observation experiment using sparse interval features and repeated subsampling.",
        "",
        "## Key result pointers",
        "",
        f"- Cross-dataset observed correspondence: `{results['correspondence']['observed_max_bipartite_overlap']:.4f}`.",
        f"- Cross-dataset permutation p-value: `{results['correspondence']['empirical_right_tail_p_value']:.6f}`.",
        f"- Temporal mean monthly self-transition: `{results['temporal']['mean_monthly_self_transition_rate']:.4f}`.",
        f"- Feature-set sampled wallets: `{results['feature_corr']['sampled_wallets']:,}`.",
        f"- Feature-set median absolute Spearman correlation: `{results['feature_corr']['median_abs_spearman']:.4f}`.",
        "",
        "## Notes for paper wording",
        "",
        "The graph-label permutation test already existed before this run and should be described separately from the cross-dataset correspondence permutation test.",
        "The minimum-observation experiment here is a practical subsampling test over the sparse interval feature table, using correspondence to the existing reference labels as the recovery criterion.",
    ]
    (OUT / "paper_process_remaining_analyses_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    results = {}
    results["correspondence"] = correspondence_permutation_test()
    distance_metric_consensus()
    results["temporal"] = temporal_stability_summary()
    results["feature_corr"] = cross_feature_spearman()
    observation_density_experiment()
    write_master_summary(results)
    (OUT / "paper_process_remaining_analyses_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"Outputs written to: {OUT}")


if __name__ == "__main__":
    main()
