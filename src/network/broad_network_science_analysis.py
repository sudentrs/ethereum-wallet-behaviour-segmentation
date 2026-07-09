import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from scipy.stats import kruskal, mannwhitneyu
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import MiniBatchKMeans


FEATURE_GROUPS = {
    "activity_intensity": [
        "active_days",
        "total_tx",
        "avg_tx_per_day",
        "active_days_observed",
        "avg_daily_tx_count",
        "max_daily_tx_count",
    ],
    "activity_persistence": [
        "activity_span",
        "activity_density",
        "activity_span_days",
        "in_active_days",
        "out_active_days",
        "both_active_days",
    ],
    "value_scale": [
        "avg_tx_size",
        "net_flow",
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
        "in_out_ratio",
        "directionality",
        "in_active_day_ratio",
        "out_active_day_ratio",
        "both_active_day_ratio",
        "in_out_day_balance",
    ],
    "temporal_irregularity": [
        "burstiness",
        "flow_volatility",
        "tx_size_volatility",
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


def clean_wallet(series):
    return series.astype("string").str.strip().str.lower()


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


def numeric_feature_cols(df):
    return [
        c for c in df.columns
        if c not in {"wallet", "cluster"} and pd.api.types.is_numeric_dtype(df[c])
    ]


def stratified_sample(df, label_col="cluster", n_per_cluster=5000, random_state=42):
    parts = []
    for _, sub in df.groupby(label_col):
        n = min(n_per_cluster, len(sub))
        parts.append(sub.sample(n=n, random_state=random_state))
    return pd.concat(parts, ignore_index=True)


def load_kmeans_clusters(path):
    df = pd.read_csv(path, dtype={"wallet": str})
    df["wallet"] = clean_wallet(df["wallet"])
    df["cluster"] = df["cluster"].astype(int)
    df = df.drop_duplicates("wallet")
    return df


def cluster_profiles(df, out_dir):
    feature_cols = numeric_feature_cols(df)
    sizes = df["cluster"].value_counts().sort_index().rename_axis("cluster").reset_index(name="wallet_count")
    medians = df.groupby("cluster")[feature_cols].median().sort_index()
    means = df.groupby("cluster")[feature_cols].mean().sort_index()
    medians.to_csv(out_dir / "cluster_feature_medians.csv")
    means.to_csv(out_dir / "cluster_feature_means.csv")
    sizes.to_csv(out_dir / "cluster_sizes.csv", index=False)

    rows = []
    for cluster, row in medians.iterrows():
        group_scores = {}
        for group, cols in FEATURE_GROUPS.items():
            valid = [c for c in cols if c in row.index]
            group_scores[group] = float(row[valid].mean()) if valid else np.nan

        high = row.sort_values(ascending=False).head(4)
        low = row.sort_values().head(4)
        descriptors = []
        if group_scores["activity_intensity"] > 0.5:
            descriptors.append("high transaction intensity")
        elif group_scores["activity_intensity"] < -0.5:
            descriptors.append("low transaction intensity")
        if group_scores["activity_persistence"] > 0.5:
            descriptors.append("persistent activity")
        elif group_scores["activity_persistence"] < -0.5:
            descriptors.append("short-lived activity")
        if group_scores["value_scale"] > 0.5:
            descriptors.append("large-value/net-inflow behavior")
        elif group_scores["value_scale"] < -0.5:
            descriptors.append("small-value/net-outflow behavior")
        if group_scores["directionality"] > 0.5:
            descriptors.append("directional receiver/sender imbalance")
        elif group_scores["directionality"] < -0.5:
            descriptors.append("balanced or opposite directionality")
        if group_scores["temporal_irregularity"] > 0.5:
            descriptors.append("bursty or volatile timing")
        elif group_scores["temporal_irregularity"] < -0.5:
            descriptors.append("regular/low volatility")
        if not descriptors:
            descriptors.append(max(group_scores, key=lambda k: np.nan_to_num(group_scores[k])))

        rows.append({
            "cluster": cluster,
            "behavior_interpretation": ", ".join(descriptors),
            "top_high_features": "; ".join(f"{k}={v:.2f}" for k, v in high.items()),
            "top_low_features": "; ".join(f"{k}={v:.2f}" for k, v in low.items()),
            **{f"{k}_score": v for k, v in group_scores.items()},
        })

    labels = pd.DataFrame(rows).merge(sizes, on="cluster", how="left")
    labels.to_csv(out_dir / "cluster_behavior_interpretation.csv", index=False)

    plt.figure(figsize=(11, 5.5))
    plt.imshow(medians.to_numpy(), aspect="auto")
    plt.xticks(range(len(feature_cols)), feature_cols, rotation=75, ha="right")
    plt.yticks(range(len(medians.index)), [f"C{c}" for c in medians.index])
    plt.colorbar(label="Feature value")
    plt.title("KMeans6 Cluster Feature Profiles")
    plt.tight_layout()
    plt.savefig(out_dir / "cluster_feature_profile_heatmap.png", dpi=220)
    plt.close()
    return labels, medians


def statistical_separation(sample_df, out_dir):
    feature_cols = numeric_feature_cols(sample_df)
    global_rows = []
    for feature in feature_cols:
        groups = [
            sub[feature].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            for _, sub in sample_df.groupby("cluster")
        ]
        stat, pval = kruskal(*groups)
        global_rows.append({"feature": feature, "kruskal_stat": stat, "p_value": pval})
    global_df = pd.DataFrame(global_rows)
    global_df["q_value_bh"] = fdr_bh(global_df["p_value"])
    global_df = global_df.sort_values(["q_value_bh", "kruskal_stat"], ascending=[True, False])
    global_df.to_csv(out_dir / "global_cluster_statistical_separation.csv", index=False)

    pair_rows = []
    clusters = sorted(sample_df["cluster"].unique())
    for c_a, c_b in combinations(clusters, 2):
        a = sample_df[sample_df["cluster"] == c_a]
        b = sample_df[sample_df["cluster"] == c_b]
        for feature in feature_cols:
            x = a[feature].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            y = b[feature].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            stat, pval = mannwhitneyu(x, y, alternative="two-sided")
            delta = cliffs_delta(x, y)
            pair_rows.append({
                "cluster_a": c_a,
                "cluster_b": c_b,
                "feature": feature,
                "median_a": np.nanmedian(x),
                "median_b": np.nanmedian(y),
                "median_difference_a_minus_b": np.nanmedian(x) - np.nanmedian(y),
                "p_value": pval,
                "q_value_bh": np.nan,
                "cliffs_delta": delta,
                "effect_size_abs": abs(delta),
            })
    pair_df = pd.DataFrame(pair_rows)
    pair_df["q_value_bh"] = fdr_bh(pair_df["p_value"])
    pair_df = pair_df.sort_values(
        ["cluster_a", "cluster_b", "q_value_bh", "effect_size_abs"],
        ascending=[True, True, True, False],
    )
    pair_df.to_csv(out_dir / "pairwise_cluster_statistical_separation.csv", index=False)

    pair_summary = (
        pair_df[pair_df["q_value_bh"] < 0.05]
        .groupby(["cluster_a", "cluster_b"])
        .agg(
            significant_features=("feature", "count"),
            mean_abs_cliffs_delta=("effect_size_abs", "mean"),
            max_abs_cliffs_delta=("effect_size_abs", "max"),
        )
        .reset_index()
        .sort_values(["mean_abs_cliffs_delta"], ascending=False)
    )
    pair_summary.to_csv(out_dir / "pairwise_cluster_separation_summary.csv", index=False)
    return global_df, pair_df, pair_summary


def feature_similarity_network(sample_df, out_dir, random_state):
    feature_cols = numeric_feature_cols(sample_df)
    X = sample_df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()
    wallets = sample_df["wallet"].tolist()
    labels = dict(zip(wallets, sample_df["cluster"].astype(int)))

    nbrs = NearestNeighbors(n_neighbors=min(11, len(sample_df)), metric="cosine")
    nbrs.fit(X)
    distances, indices = nbrs.kneighbors(X)

    neighbor_sets = {
        wallets[i]: set(wallets[j] for j in indices[i][1:])
        for i in range(len(wallets))
    }

    graph = nx.Graph()
    for wallet in wallets:
        graph.add_node(wallet, cluster=labels[wallet])

    for i, wallet in enumerate(wallets):
        for j_idx, dist in zip(indices[i][1:], distances[i][1:]):
            other = wallets[j_idx]
            if wallet in neighbor_sets[other] and not graph.has_edge(wallet, other):
                graph.add_edge(wallet, other, weight=max(1 - float(dist), 1e-6))

    graph.remove_nodes_from([n for n, degree in graph.degree() if degree == 0])
    total_edges = graph.number_of_edges()
    intra = sum(1 for u, v in graph.edges() if graph.nodes[u]["cluster"] == graph.nodes[v]["cluster"])

    communities_by_label = {}
    for node, data in graph.nodes(data=True):
        communities_by_label.setdefault(data["cluster"], set()).add(node)
    label_modularity = nx.algorithms.community.quality.modularity(
        graph, list(communities_by_label.values()), weight="weight"
    )
    assortativity = nx.attribute_assortativity_coefficient(graph, "cluster")

    detected = list(nx.algorithms.community.greedy_modularity_communities(graph, weight="weight"))
    detected_map = {}
    for i, community in enumerate(detected):
        for node in community:
            detected_map[node] = i
    ari = adjusted_rand_score(
        [graph.nodes[n]["cluster"] for n in graph.nodes()],
        [detected_map[n] for n in graph.nodes()],
    )

    rows = []
    for cluster, nodes in communities_by_label.items():
        sub_nodes = set(nodes)
        internal_edges = 0
        boundary_edges = 0
        volume = 0
        for node in sub_nodes:
            volume += graph.degree(node)
            for nbr in graph.neighbors(node):
                if nbr in sub_nodes:
                    internal_edges += 0.5
                else:
                    boundary_edges += 1
        rows.append({
            "cluster": cluster,
            "nodes": len(sub_nodes),
            "internal_edges": int(internal_edges),
            "boundary_edges": int(boundary_edges),
            "conductance": boundary_edges / volume if volume else np.nan,
        })
    cluster_net = pd.DataFrame(rows).sort_values("cluster")
    cluster_net.to_csv(out_dir / "feature_similarity_network_cluster_conductance.csv", index=False)

    summary = pd.DataFrame([{
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "intra_cluster_edge_ratio": intra / total_edges if total_edges else np.nan,
        "inter_cluster_edge_ratio": 1 - intra / total_edges if total_edges else np.nan,
        "cluster_label_modularity": label_modularity,
        "cluster_assortativity": assortativity,
        "detected_communities": len(detected),
        "ari_detected_communities_vs_kmeans6": ari,
    }])
    summary.to_csv(out_dir / "feature_similarity_network_summary.csv", index=False)
    return summary, cluster_net


def alternative_k(sample_df, out_dir, random_state):
    feature_cols = numeric_feature_cols(sample_df)
    X = sample_df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()
    existing = sample_df["cluster"].astype(int).to_numpy()
    rows = []
    for k in range(3, 11):
        model = MiniBatchKMeans(n_clusters=k, random_state=random_state, batch_size=4096, n_init="auto")
        pred = model.fit_predict(X)
        rows.append({
            "k": k,
            "silhouette": silhouette_score(X, pred, sample_size=min(10000, len(X)), random_state=random_state),
            "ari_vs_current_kmeans6": adjusted_rand_score(existing, pred),
            "inertia": model.inertia_,
        })
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "alternative_k_clusterability.csv", index=False)
    return out


def month_file(data_dir, month):
    path = data_dir / f"{month}.tsv" / f"{month}.tsv"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def transaction_network_by_month(cluster_df, data_dir, months, out_dir, chunksize):
    label_map = cluster_df.set_index("wallet")["cluster"].to_dict()
    clusters = sorted(cluster_df["cluster"].unique())
    monthly_rows = []
    daily_rows = []
    coverage_rows = []

    for month in months:
        path = month_file(data_dir, month)
        pair_counts = {(src, dst): 0 for src in clusters for dst in clusters}
        total_rows = 0
        covered_rows = 0
        usecols = ["time", "sender", "recipient", "value"]

        print(f"Processing raw transaction month {month}: {path}")
        for chunk in pd.read_csv(
            path,
            sep="\t",
            usecols=usecols,
            dtype={"sender": str, "recipient": str, "value": str},
            chunksize=chunksize,
        ):
            total_rows += len(chunk)
            chunk["sender"] = clean_wallet(chunk["sender"])
            chunk["recipient"] = clean_wallet(chunk["recipient"])
            chunk["source_cluster"] = chunk["sender"].map(label_map)
            chunk["target_cluster"] = chunk["recipient"].map(label_map)
            chunk = chunk.dropna(subset=["source_cluster", "target_cluster"]).copy()
            covered_rows += len(chunk)
            if chunk.empty:
                continue

            chunk["source_cluster"] = chunk["source_cluster"].astype(int)
            chunk["target_cluster"] = chunk["target_cluster"].astype(int)
            chunk["date"] = pd.to_datetime(chunk["time"], errors="coerce").dt.date
            chunk["value_numeric"] = pd.to_numeric(chunk["value"], errors="coerce").fillna(0.0)

            grouped = chunk.groupby(["source_cluster", "target_cluster"]).agg(
                tx_count=("value_numeric", "size"),
                total_value=("value_numeric", "sum"),
            ).reset_index()
            for row in grouped.itertuples(index=False):
                pair_counts[(int(row.source_cluster), int(row.target_cluster))] += int(row.tx_count)

            daily = chunk.groupby(["date", "source_cluster", "target_cluster"]).size().reset_index(name="tx_count")
            daily["month"] = month
            daily_rows.append(daily)

        month_matrix = pd.DataFrame(0, index=clusters, columns=clusters, dtype=np.int64)
        for (src, dst), count in pair_counts.items():
            month_matrix.loc[src, dst] = count

        graph = nx.from_pandas_adjacency(month_matrix, create_using=nx.DiGraph)
        total_edges_weight = month_matrix.to_numpy().sum()
        self_loop_weight = sum(month_matrix.loc[c, c] for c in clusters)

        coverage_rows.append({
            "month": month,
            "raw_rows_read": total_rows,
            "rows_with_both_cluster_labels": covered_rows,
            "coverage_ratio": covered_rows / total_rows if total_rows else np.nan,
        })
        for src in clusters:
            for dst in clusters:
                monthly_rows.append({
                    "month": month,
                    "source_cluster": src,
                    "target_cluster": dst,
                    "tx_count": int(month_matrix.loc[src, dst]),
                    "share_of_month_cluster_labeled_tx": month_matrix.loc[src, dst] / total_edges_weight if total_edges_weight else np.nan,
                    "is_self_loop": src == dst,
                })
        coverage_rows[-1].update({
            "total_cluster_labeled_tx": int(total_edges_weight),
            "self_loop_tx": int(self_loop_weight),
            "self_loop_ratio": self_loop_weight / total_edges_weight if total_edges_weight else np.nan,
            "reciprocity_binary": nx.reciprocity(graph) if graph.number_of_edges() else np.nan,
        })

    monthly = pd.DataFrame(monthly_rows)
    monthly.to_csv(out_dir / "monthly_cluster_to_cluster_edges.csv", index=False)
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(out_dir / "monthly_transaction_network_coverage.csv", index=False)

    if daily_rows:
        daily_all = pd.concat(daily_rows, ignore_index=True)
        daily_all = daily_all.groupby(["month", "date", "source_cluster", "target_cluster"], as_index=False)["tx_count"].sum()
        daily_all.to_csv(out_dir / "daily_cluster_to_cluster_edges.csv", index=False)
    else:
        daily_all = pd.DataFrame()

    centrality_rows = []
    for month, sub in monthly.groupby("month"):
        matrix = sub.pivot(index="source_cluster", columns="target_cluster", values="tx_count").fillna(0)
        graph = nx.from_pandas_adjacency(matrix, create_using=nx.DiGraph)
        for cluster in clusters:
            self_loop = matrix.loc[cluster, cluster]
            out_weight = graph.out_degree(cluster, weight="weight")
            in_weight = graph.in_degree(cluster, weight="weight")
            centrality_rows.append({
                "month": month,
                "cluster": cluster,
                "weighted_out_degree": out_weight,
                "weighted_in_degree": in_weight,
                "self_loop_tx": self_loop,
                "external_out_tx": out_weight - self_loop,
                "external_in_tx": in_weight - self_loop,
                "net_external_flow_tx": (in_weight - self_loop) - (out_weight - self_loop),
            })
    centrality = pd.DataFrame(centrality_rows)
    centrality.to_csv(out_dir / "monthly_cluster_network_centrality.csv", index=False)

    edge_dynamics = (
        monthly
        .groupby(["source_cluster", "target_cluster"])
        .agg(
            mean_monthly_tx=("tx_count", "mean"),
            std_monthly_tx=("tx_count", "std"),
            min_monthly_tx=("tx_count", "min"),
            max_monthly_tx=("tx_count", "max"),
            first_month_tx=("tx_count", "first"),
            last_month_tx=("tx_count", "last"),
        )
        .reset_index()
    )
    edge_dynamics["temporal_cv"] = edge_dynamics["std_monthly_tx"] / edge_dynamics["mean_monthly_tx"].replace(0, np.nan)
    edge_dynamics["last_minus_first_tx"] = edge_dynamics["last_month_tx"] - edge_dynamics["first_month_tx"]
    edge_dynamics["max_min_ratio"] = edge_dynamics["max_monthly_tx"] / edge_dynamics["min_monthly_tx"].replace(0, np.nan)
    edge_dynamics = edge_dynamics.sort_values(["temporal_cv", "mean_monthly_tx"], ascending=[False, False])
    edge_dynamics.to_csv(out_dir / "cluster_pair_temporal_edge_dynamics.csv", index=False)

    if not monthly.empty:
        avg_matrix = monthly.groupby(["source_cluster", "target_cluster"])["tx_count"].mean().reset_index()
        matrix = avg_matrix.pivot(index="source_cluster", columns="target_cluster", values="tx_count").fillna(0)
        plt.figure(figsize=(7, 5.8))
        plt.imshow(np.log1p(matrix.to_numpy()), aspect="auto")
        plt.xticks(range(len(matrix.columns)), [f"C{c}" for c in matrix.columns])
        plt.yticks(range(len(matrix.index)), [f"C{c}" for c in matrix.index])
        plt.xlabel("Target cluster")
        plt.ylabel("Source cluster")
        plt.title("Mean Monthly Cluster-to-Cluster Transactions")
        plt.colorbar(label="log(1 + mean tx)")
        plt.tight_layout()
        plt.savefig(out_dir / "mean_monthly_cluster_adjacency_heatmap.png", dpi=220)
        plt.close()

    return monthly, coverage, centrality, daily_all


def write_summary(out_dir, behavior, global_tests, pair_summary, feature_net, alt_k, coverage, centrality):
    strongest_pair_summary = pair_summary.head(10)
    best_alt = alt_k.sort_values("silhouette", ascending=False).head(5)
    lines = []
    lines.append("# Broad KMeans6 Network Science Analysis\n")
    lines.append("This analysis uses `dataverse_files/wallet_kmeans_clusters.csv` as the authoritative KMeans6 cluster file.\n")
    lines.append("## Behavioral Interpretation\n")
    lines.append(behavior.to_markdown(index=False))
    lines.append("\n## Feature-Space Network Structure\n")
    lines.append(feature_net.to_markdown(index=False))
    lines.append("\n## Alternative k Diagnostics\n")
    lines.append(best_alt.to_markdown(index=False))
    lines.append("\n## Strongest Pairwise Separations\n")
    lines.append(strongest_pair_summary.to_markdown(index=False))
    lines.append("\n## Most Globally Separating Features\n")
    lines.append(global_tests.head(12).to_markdown(index=False))
    if coverage is not None and not coverage.empty:
        lines.append("\n## Transaction Network Coverage and Self-Loop Structure\n")
        lines.append(coverage.to_markdown(index=False))
    if centrality is not None and not centrality.empty:
        top = centrality.sort_values(["month", "external_in_tx"], ascending=[True, False]).groupby("month").head(3)
        lines.append("\n## Top External In-Degree Clusters by Month\n")
        lines.append(top.to_markdown(index=False))
    (out_dir / "broad_network_science_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="dataverse_files")
    parser.add_argument("--cluster-file", default="dataverse_files/wallet_kmeans_clusters.csv")
    parser.add_argument("--out-dir", default="dataverse_files/network_science_kmeans6_full")
    parser.add_argument("--months", default="202205,202206,202209", help="Comma-separated months, or 'none' to skip raw TSV network.")
    parser.add_argument("--sample-per-cluster", type=int, default=5000)
    parser.add_argument("--chunksize", type=int, default=1000000)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cluster_df = load_kmeans_clusters(args.cluster_file)
    behavior, _ = cluster_profiles(cluster_df, out_dir)
    sample_df = stratified_sample(cluster_df, n_per_cluster=args.sample_per_cluster, random_state=args.random_state)

    global_tests, _, pair_summary = statistical_separation(sample_df, out_dir)
    feature_net, _ = feature_similarity_network(sample_df, out_dir, args.random_state)
    alt_k = alternative_k(sample_df, out_dir, args.random_state)

    coverage = pd.DataFrame()
    centrality = pd.DataFrame()
    if args.months.strip().lower() != "none":
        months = [m.strip() for m in args.months.split(",") if m.strip()]
        _, coverage, centrality, _ = transaction_network_by_month(
            cluster_df=cluster_df,
            data_dir=data_dir,
            months=months,
            out_dir=out_dir,
            chunksize=args.chunksize,
        )

    write_summary(out_dir, behavior, global_tests, pair_summary, feature_net, alt_k, coverage, centrality)
    print(f"Saved broad network science analysis to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
