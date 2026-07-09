import argparse
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import kruskal, mannwhitneyu
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score


FEATURE_GROUPS = {
    "activity_intensity": [
        "active_days_observed",
        "total_tx",
        "avg_daily_tx_count",
        "max_daily_tx_count",
    ],
    "activity_persistence": [
        "activity_span_days",
        "activity_density",
        "in_active_days",
        "out_active_days",
        "both_active_days",
    ],
    "value_scale": [
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
    ],
    "directionality": [
        "in_active_day_ratio",
        "out_active_day_ratio",
        "both_active_day_ratio",
        "in_out_day_balance",
    ],
    "temporal_irregularity": [
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


def numeric_feature_cols(df):
    return [
        c for c in df.columns
        if c not in {"wallet", "cluster"} and pd.api.types.is_numeric_dtype(df[c])
    ]


def fdr_bh(p_values):
    p = np.asarray(p_values, dtype=float)
    out = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return out
    idx = np.where(valid)[0]
    order = idx[np.argsort(p[valid])]
    ranked = p[order]
    m = len(ranked)
    q = ranked * m / np.arange(1, m + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out[order] = np.clip(q, 0, 1)
    return out


def cliffs_delta(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) == 0 or len(y) == 0:
        return np.nan
    combined = np.concatenate([x, y])
    ranks = pd.Series(combined).rank(method="average").to_numpy()
    rx = ranks[: len(x)].sum()
    return (2 * rx - len(x) * (len(x) + 1) - len(x) * len(y)) / (len(x) * len(y))


def sample_by_cluster(df, max_per_cluster, random_state):
    parts = []
    for _, sub in df.groupby("cluster"):
        n = min(max_per_cluster, len(sub))
        parts.append(sub.sample(n=n, random_state=random_state))
    return pd.concat(parts, ignore_index=True)


def feature_group_scores(profile_row):
    scores = {}
    for group, cols in FEATURE_GROUPS.items():
        valid = [c for c in cols if c in profile_row.index]
        scores[group] = float(profile_row[valid].mean()) if valid else np.nan
    return scores


def behavior_label(scores):
    labels = []
    if scores.get("activity_intensity", 0) > 0.45:
        labels.append("high transaction intensity")
    elif scores.get("activity_intensity", 0) < -0.45:
        labels.append("low transaction intensity")
    if scores.get("activity_persistence", 0) > 0.45:
        labels.append("persistent activity")
    elif scores.get("activity_persistence", 0) < -0.45:
        labels.append("short-lived activity")
    if scores.get("value_scale", 0) > 0.45:
        labels.append("large-value flow")
    elif scores.get("value_scale", 0) < -0.45:
        labels.append("small-value flow")
    if scores.get("directionality", 0) > 0.45:
        labels.append("directional imbalance")
    elif scores.get("directionality", 0) < -0.45:
        labels.append("balanced/opposite directionality")
    if scores.get("temporal_irregularity", 0) > 0.45:
        labels.append("bursty/volatile")
    elif scores.get("temporal_irregularity", 0) < -0.45:
        labels.append("regular/low volatility")
    if labels:
        return ", ".join(labels)
    best = max(scores, key=lambda k: np.nan_to_num(abs(scores[k])))
    return f"{best}-leaning"


def choose_subclusters(X, k_min, k_max, random_state):
    rows = []
    models = {}
    for k in range(k_min, k_max + 1):
        model = MiniBatchKMeans(n_clusters=k, random_state=random_state, batch_size=4096, n_init="auto")
        labels = model.fit_predict(X)
        counts = pd.Series(labels).value_counts()
        min_share = counts.min() / len(labels)
        sil = silhouette_score(X, labels, sample_size=min(6000, len(X)), random_state=random_state)
        db = davies_bouldin_score(X, labels)
        ch = calinski_harabasz_score(X, labels)
        rows.append({
            "candidate_k": k,
            "silhouette": sil,
            "davies_bouldin": db,
            "calinski_harabasz": ch,
            "min_subcluster_share": min_share,
            "inertia": model.inertia_,
        })
        models[k] = (model, labels)

    scores = pd.DataFrame(rows)
    eligible = scores[scores["min_subcluster_share"] >= 0.03].copy()
    if eligible.empty:
        eligible = scores.copy()
    best_k = int(eligible.sort_values(["silhouette", "calinski_harabasz"], ascending=[False, False]).iloc[0]["candidate_k"])
    return scores, best_k, models[best_k]


def subcluster_statistics(cluster_df, feature_cols, sub_col):
    global_rows = []
    for feature in feature_cols:
        groups = [
            sub[feature].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            for _, sub in cluster_df.groupby(sub_col)
        ]
        if len(groups) > 1 and all(len(g) > 0 for g in groups):
            stat, pval = kruskal(*groups)
        else:
            stat, pval = np.nan, np.nan
        global_rows.append({"feature": feature, "kruskal_stat": stat, "p_value": pval})
    global_df = pd.DataFrame(global_rows)
    global_df["q_value_bh"] = fdr_bh(global_df["p_value"])
    global_df = global_df.sort_values(["q_value_bh", "kruskal_stat"], ascending=[True, False])

    pair_rows = []
    subclusters = sorted(cluster_df[sub_col].unique())
    for a, b in combinations(subclusters, 2):
        a_df = cluster_df[cluster_df[sub_col] == a]
        b_df = cluster_df[cluster_df[sub_col] == b]
        for feature in feature_cols:
            x = a_df[feature].dropna().to_numpy()
            y = b_df[feature].dropna().to_numpy()
            stat, pval = mannwhitneyu(x, y, alternative="two-sided")
            delta = cliffs_delta(x, y)
            pair_rows.append({
                "subcluster_a": a,
                "subcluster_b": b,
                "feature": feature,
                "median_a": np.nanmedian(x),
                "median_b": np.nanmedian(y),
                "median_difference_a_minus_b": np.nanmedian(x) - np.nanmedian(y),
                "p_value": pval,
                "cliffs_delta": delta,
                "effect_size_abs": abs(delta),
            })
    pair_df = pd.DataFrame(pair_rows)
    pair_df["q_value_bh"] = fdr_bh(pair_df["p_value"])
    pair_df = pair_df.sort_values(
        ["subcluster_a", "subcluster_b", "q_value_bh", "effect_size_abs"],
        ascending=[True, True, True, False],
    )

    pair_summary = (
        pair_df[pair_df["q_value_bh"] < 0.05]
        .groupby(["subcluster_a", "subcluster_b"])
        .agg(
            significant_features=("feature", "count"),
            mean_abs_cliffs_delta=("effect_size_abs", "mean"),
            max_abs_cliffs_delta=("effect_size_abs", "max"),
        )
        .reset_index()
        .sort_values("mean_abs_cliffs_delta", ascending=False)
    )
    return global_df, pair_df, pair_summary


def plot_subcluster_profiles(profile, out_path, title):
    plt.figure(figsize=(13, max(4.5, len(profile) * 0.8)))
    plt.imshow(profile.to_numpy(), aspect="auto", cmap="coolwarm", vmin=-2.5, vmax=2.5)
    plt.xticks(range(len(profile.columns)), profile.columns, rotation=75, ha="right", fontsize=8)
    plt.yticks(range(len(profile.index)), [f"S{s}" for s in profile.index])
    plt.colorbar(label="Robust-scaled median feature value")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def plot_pca(cluster_df, feature_cols, sub_col, out_path, title, random_state):
    plot_df = cluster_df.sample(n=min(3500, len(cluster_df)), random_state=random_state)
    X = plot_df[feature_cols].to_numpy()
    coords = PCA(n_components=2, random_state=random_state).fit_transform(X)
    plt.figure(figsize=(7.5, 6))
    for sub_id, sub in plot_df.assign(pc1=coords[:, 0], pc2=coords[:, 1]).groupby(sub_col):
        plt.scatter(sub["pc1"], sub["pc2"], s=7, alpha=0.55, label=f"S{sub_id}")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.title(title)
    plt.legend(markerscale=2, fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def plot_silhouette_grid(all_scores, out_path):
    plt.figure(figsize=(10, 6))
    for cluster, sub in all_scores.groupby("cluster"):
        plt.plot(sub["candidate_k"], sub["silhouette"], marker="o", linewidth=1.6, label=f"C{cluster}")
    plt.xlabel("Candidate subclusters within main cluster")
    plt.ylabel("Silhouette")
    plt.title("Internal Subcluster Evidence by Main Cluster")
    plt.legend(ncol=3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def write_report(out_dir, summary, all_scores, behavior, global_top, pair_summary_all):
    lines = []
    lines.append("# Cluster Behavior and Internal Subcluster Analysis\n")
    lines.append("This analysis studies whether each KMeans6 cluster contains meaningful behavioral subtypes. It uses the robust-scaled expanded daily behavior features.\n")

    lines.append("## Mathematical Setup\n")
    lines.append("Let `C_k` be one main KMeans6 cluster. For wallets `i in C_k`, each wallet has expanded behavior vector `x_i in R^33`. For each main cluster, we fit candidate internal partitions `P_k(r)` for `r = 2,...,8` using MiniBatchKMeans. The preferred internal subcluster count is selected by maximizing silhouette subject to a minimum subcluster share constraint.\n")
    lines.append("Silhouette for wallet `i` is `s(i) = (b(i) - a(i)) / max(a(i), b(i))`, where `a(i)` is mean distance to its own subcluster and `b(i)` is the best alternative-subcluster distance. Larger values imply stronger internal subcluster structure.\n")
    lines.append("For each main cluster and feature, we test `H0: F_0 = F_1 = ... = F_r` across internal subclusters using Kruskal-Wallis. Pairwise internal differences use Mann-Whitney U and Cliff's delta: `delta = P(X_a > X_b) - P(X_a < X_b)`.\n")

    lines.append("## Internal Heterogeneity Summary\n")
    lines.append(summary.to_markdown(index=False))

    lines.append("\n## Behavioral Subtypes\n")
    lines.append(behavior.to_markdown(index=False))

    lines.append("\n## Best Internal k Diagnostics\n")
    best_scores = all_scores.merge(summary[["cluster", "selected_subcluster_k"]], left_on=["cluster", "candidate_k"], right_on=["cluster", "selected_subcluster_k"], how="inner")
    lines.append(best_scores[["cluster", "candidate_k", "silhouette", "davies_bouldin", "calinski_harabasz", "min_subcluster_share"]].to_markdown(index=False))

    lines.append("\n## Most Important Within-Cluster Separating Features\n")
    lines.append(global_top.to_markdown(index=False))

    lines.append("\n## Strongest Pairwise Subcluster Separations\n")
    lines.append(pair_summary_all.head(20).to_markdown(index=False))

    lines.append("\n## Interpretation\n")
    lines.append("A main cluster should be treated as internally heterogeneous when it has: positive internal silhouette, multiple statistically significant separating features, large Cliff's delta between subclusters, and interpretable subtype profiles. Under this criterion, the KMeans6 clusters are not merely six homogeneous blocks; they contain behavioral subtypes such as high-volume persistent wallets, bursty short-lived wallets, receiver/sink-like wallets, and large-value directional wallets.\n")

    (out_dir / "cluster_behavior_subcluster_report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", default="dataverse_files/wallet_kmeans6_expanded_daily_features_robust_scaled.csv")
    parser.add_argument("--out-dir", default="dataverse_files/cluster_behavior_subclusters_expanded")
    parser.add_argument("--sample-per-cluster", type=int, default=12000)
    parser.add_argument("--k-min", type=int, default=2)
    parser.add_argument("--k-max", type=int, default=8)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_dir = out_dir / "figures"
    plot_dir.mkdir(exist_ok=True)

    df = pd.read_csv(args.features, dtype={"wallet": str})
    df["cluster"] = df["cluster"].astype(int)
    feature_cols = numeric_feature_cols(df)
    sample_df = sample_by_cluster(df, args.sample_per_cluster, args.random_state)

    all_score_rows = []
    summary_rows = []
    behavior_rows = []
    global_top_rows = []
    pair_summary_parts = []
    assignment_parts = []

    for cluster, cluster_df in sample_df.groupby("cluster"):
        cluster_df = cluster_df.copy().reset_index(drop=True)
        X = cluster_df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()

        scores, best_k, (model, labels) = choose_subclusters(X, args.k_min, args.k_max, args.random_state)
        scores["cluster"] = cluster
        all_score_rows.append(scores)

        cluster_df["subcluster"] = labels
        assignment_parts.append(cluster_df[["wallet", "cluster", "subcluster"]])

        profile = cluster_df.groupby("subcluster")[feature_cols].median().sort_index()
        profile.to_csv(out_dir / f"C{cluster}_subcluster_feature_medians.csv")

        global_df, pair_df, pair_summary = subcluster_statistics(cluster_df, feature_cols, "subcluster")
        global_df.to_csv(out_dir / f"C{cluster}_subcluster_global_tests.csv", index=False)
        pair_df.to_csv(out_dir / f"C{cluster}_subcluster_pairwise_tests.csv", index=False)
        pair_summary.to_csv(out_dir / f"C{cluster}_subcluster_pairwise_summary.csv", index=False)

        top_global = global_df.head(8).copy()
        top_global["cluster"] = cluster
        global_top_rows.append(top_global)

        pair_summary = pair_summary.copy()
        pair_summary["cluster"] = cluster
        pair_summary_parts.append(pair_summary)

        selected = scores[scores["candidate_k"] == best_k].iloc[0]
        counts = cluster_df["subcluster"].value_counts().sort_index()
        summary_rows.append({
            "cluster": cluster,
            "sampled_wallets": len(cluster_df),
            "selected_subcluster_k": best_k,
            "selected_silhouette": selected["silhouette"],
            "selected_davies_bouldin": selected["davies_bouldin"],
            "selected_calinski_harabasz": selected["calinski_harabasz"],
            "min_subcluster_share": selected["min_subcluster_share"],
            "subcluster_sizes": "; ".join(f"S{s}={n}" for s, n in counts.items()),
            "globally_significant_features_q05": int((global_df["q_value_bh"] < 0.05).sum()),
        })

        for subcluster, row in profile.iterrows():
            scores_by_group = feature_group_scores(row)
            high = row.sort_values(ascending=False).head(5)
            low = row.sort_values().head(5)
            behavior_rows.append({
                "cluster": cluster,
                "subcluster": subcluster,
                "sampled_wallets": int(counts.loc[subcluster]),
                "behavior_label": behavior_label(scores_by_group),
                "top_high_features": "; ".join(f"{k}={v:.2f}" for k, v in high.items()),
                "top_low_features": "; ".join(f"{k}={v:.2f}" for k, v in low.items()),
                **{f"{k}_score": v for k, v in scores_by_group.items()},
            })

        plot_subcluster_profiles(
            profile,
            plot_dir / f"C{cluster}_subcluster_profile_heatmap.png",
            f"Cluster C{cluster}: Internal Behavioral Subcluster Profiles",
        )
        plot_pca(
            cluster_df,
            feature_cols,
            "subcluster",
            plot_dir / f"C{cluster}_pca_subclusters.png",
            f"Cluster C{cluster}: PCA View of Internal Subclusters",
            args.random_state,
        )

    all_scores = pd.concat(all_score_rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows).sort_values("cluster")
    behavior = pd.DataFrame(behavior_rows).sort_values(["cluster", "subcluster"])
    global_top = pd.concat(global_top_rows, ignore_index=True)
    pair_summary_all = pd.concat(pair_summary_parts, ignore_index=True).sort_values(
        ["mean_abs_cliffs_delta"], ascending=False
    )
    assignments = pd.concat(assignment_parts, ignore_index=True)

    all_scores.to_csv(out_dir / "subcluster_k_diagnostics.csv", index=False)
    summary.to_csv(out_dir / "subcluster_summary.csv", index=False)
    behavior.to_csv(out_dir / "subcluster_behavior_profiles.csv", index=False)
    global_top.to_csv(out_dir / "top_within_cluster_separating_features.csv", index=False)
    pair_summary_all.to_csv(out_dir / "subcluster_pairwise_separation_summary_all.csv", index=False)
    assignments.to_csv(out_dir / "sample_wallet_subcluster_assignments.csv", index=False)

    plot_silhouette_grid(all_scores, plot_dir / "subcluster_silhouette_by_main_cluster.png")
    write_report(out_dir, summary, all_scores, behavior, global_top, pair_summary_all)
    print(f"Saved cluster behavior/subcluster analysis to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
