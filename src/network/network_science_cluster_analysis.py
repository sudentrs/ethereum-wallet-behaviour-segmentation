import argparse
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from scipy.stats import kruskal, mannwhitneyu
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.neighbors import NearestNeighbors


FEATURE_GROUPS = {
    "activity": [
        "active_days_observed",
        "activity_span_days",
        "activity_density",
        "total_tx",
        "avg_daily_tx_count",
        "max_daily_tx_count",
        "tx_count_cv",
        "tx_concentration_ratio",
    ],
    "flow_size": [
        "total_in_sum",
        "total_out_sum",
        "total_net_flow_sum",
        "total_flow_sum",
        "avg_daily_total_in",
        "avg_daily_total_out",
        "avg_daily_net_flow",
        "avg_daily_total_flow",
        "max_daily_total_flow",
        "flow_concentration_ratio",
    ],
    "direction": [
        "in_active_days",
        "out_active_days",
        "both_active_days",
        "in_active_day_ratio",
        "out_active_day_ratio",
        "both_active_day_ratio",
        "in_out_day_balance",
    ],
    "volatility": [
        "std_daily_tx_count",
        "std_daily_total_in",
        "std_daily_total_out",
        "std_daily_net_flow",
        "std_daily_total_flow",
        "total_flow_cv",
    ],
}


def clean_wallet(s):
    return s.astype("string").str.strip().str.lower()


def month_paths(base_dir, month):
    month_dir = base_dir / "clustering" / month
    suffix = f"_{month}"

    def first_existing(names):
        for name in names:
            path = month_dir / name
            if path.exists():
                return path
        raise FileNotFoundError(f"None of these files exist in {month_dir}: {names}")

    return {
        "month_dir": month_dir,
        "labels": first_existing([f"merged_cluster_labels{suffix}.csv", "merged_cluster_labels.csv"]),
        "features": first_existing([
            f"wallet_evaluation_features_with_labels_chunked{suffix}.csv",
            "wallet_evaluation_features_with_labels_chunked.csv",
        ]),
        "scaled": first_existing([
            f"wallet_evaluation_features_robust_scaled_chunked{suffix}.csv",
            "wallet_evaluation_features_robust_scaled_chunked.csv",
        ]),
        "raw_tsv": first_existing([
            str(Path("..") / ".." / "dataverse_files" / f"{month}.tsv" / f"{month}.tsv"),
            str(Path("..") / ".." / month / f"{month}.tsv"),
        ]),
    }


def numeric_feature_columns(df, label_col):
    banned = {"wallet", label_col, "cluster_2", "cluster_1"}
    return [
        c for c in df.columns
        if c not in banned and pd.api.types.is_numeric_dtype(df[c])
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
    rx = ranks[:len(x)].sum()
    greater_minus_less = 2 * rx - len(x) * (len(x) + 1) - len(x) * len(y)
    return greater_minus_less / (len(x) * len(y))


def load_feature_sample(path, label_col, sample_per_cluster, random_state):
    df = pd.read_csv(path, dtype={"wallet": str})
    df["wallet"] = clean_wallet(df["wallet"])
    df = df.dropna(subset=[label_col]).copy()
    df[label_col] = df[label_col].astype(int)

    parts = []
    for _, sub in df.groupby(label_col):
        n = min(sample_per_cluster, len(sub))
        parts.append(sub.sample(n=n, random_state=random_state))
    sampled = pd.concat(parts, ignore_index=True)
    return df, sampled


def describe_clusters(scaled_df, label_col, out_dir):
    feature_cols = numeric_feature_columns(scaled_df, label_col)
    profiles = scaled_df.groupby(label_col)[feature_cols].median().sort_index()
    profiles.to_csv(out_dir / "cluster_profile_medians_scaled.csv")

    rows = []
    for cluster_id, row in profiles.iterrows():
        ordered = row.sort_values(ascending=False)
        high = ordered.head(5)
        low = ordered.tail(5).sort_values()

        group_scores = {}
        for group, cols in FEATURE_GROUPS.items():
            valid = [c for c in cols if c in row.index]
            group_scores[group] = float(row[valid].mean()) if valid else np.nan

        dominant = sorted(group_scores.items(), key=lambda item: np.nan_to_num(item[1]), reverse=True)
        label_bits = []
        if group_scores.get("activity", 0) > 0.35:
            label_bits.append("high activity")
        elif group_scores.get("activity", 0) < -0.35:
            label_bits.append("low activity")
        if group_scores.get("flow_size", 0) > 0.35:
            label_bits.append("large value flow")
        if group_scores.get("direction", 0) > 0.35:
            label_bits.append("directional/inflow-outflow imbalance")
        if group_scores.get("volatility", 0) > 0.35:
            label_bits.append("bursty/volatile")
        if not label_bits:
            label_bits.append(f"{dominant[0][0]}-leaning")

        rows.append({
            "cluster": cluster_id,
            "behavior_label": ", ".join(label_bits),
            "top_high_features": "; ".join(f"{k}={v:.2f}" for k, v in high.items()),
            "top_low_features": "; ".join(f"{k}={v:.2f}" for k, v in low.items()),
            **{f"{k}_score": v for k, v in group_scores.items()},
        })

    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "cluster_behavior_labels.csv", index=False)
    return profiles, out


def statistical_tests(sampled_df, label_col, out_dir):
    feature_cols = numeric_feature_columns(sampled_df, label_col)
    global_rows = []
    pair_rows = []

    for feature in feature_cols:
        groups = [
            sub[feature].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            for _, sub in sampled_df.groupby(label_col)
        ]
        if sum(len(g) > 0 for g in groups) > 1:
            stat, pval = kruskal(*groups)
        else:
            stat, pval = np.nan, np.nan
        global_rows.append({"feature": feature, "kruskal_stat": stat, "p_value": pval})

    global_df = pd.DataFrame(global_rows)
    global_df["q_value_bh"] = fdr_bh(global_df["p_value"])
    global_df = global_df.sort_values(["q_value_bh", "p_value"])
    global_df.to_csv(out_dir / "cluster_global_statistical_tests.csv", index=False)

    clusters = sorted(sampled_df[label_col].dropna().astype(int).unique())
    for c_a, c_b in combinations(clusters, 2):
        a_df = sampled_df[sampled_df[label_col] == c_a]
        b_df = sampled_df[sampled_df[label_col] == c_b]
        for feature in feature_cols:
            x = a_df[feature].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            y = b_df[feature].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            if len(x) == 0 or len(y) == 0:
                stat, pval, delta = np.nan, np.nan, np.nan
            else:
                stat, pval = mannwhitneyu(x, y, alternative="two-sided")
                delta = cliffs_delta(x, y)
            pair_rows.append({
                "cluster_a": c_a,
                "cluster_b": c_b,
                "feature": feature,
                "median_a": np.nanmedian(x) if len(x) else np.nan,
                "median_b": np.nanmedian(y) if len(y) else np.nan,
                "median_difference_a_minus_b": (np.nanmedian(x) - np.nanmedian(y)) if len(x) and len(y) else np.nan,
                "mannwhitney_u": stat,
                "p_value": pval,
                "cliffs_delta": delta,
                "effect_size_abs": abs(delta) if pd.notna(delta) else np.nan,
            })

    pair_df = pd.DataFrame(pair_rows)
    pair_df["q_value_bh"] = fdr_bh(pair_df["p_value"])
    pair_df = pair_df.sort_values(["cluster_a", "cluster_b", "q_value_bh", "effect_size_abs"], ascending=[True, True, True, False])
    pair_df.to_csv(out_dir / "cluster_pairwise_statistical_tests.csv", index=False)
    return global_df, pair_df


def alternative_clusterability(sampled_scaled_df, label_col, out_dir, random_state):
    feature_cols = numeric_feature_columns(sampled_scaled_df, label_col)
    X = sampled_scaled_df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()
    existing = sampled_scaled_df[label_col].astype(int).to_numpy()

    rows = []
    for k in range(3, 11):
        km = MiniBatchKMeans(n_clusters=k, random_state=random_state, batch_size=4096, n_init="auto")
        pred = km.fit_predict(X)
        sil = silhouette_score(X, pred, sample_size=min(10000, len(X)), random_state=random_state)
        ari = adjusted_rand_score(existing, pred)
        rows.append({"k": k, "silhouette": sil, "ari_vs_kmeans6": ari, "inertia": km.inertia_})

    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "alternative_k_clusterability.csv", index=False)

    plt.figure(figsize=(8, 4.8))
    plt.plot(out["k"], out["silhouette"], marker="o", label="Silhouette")
    plt.plot(out["k"], out["ari_vs_kmeans6"], marker="s", label="ARI vs current KMeans6")
    plt.axvline(6, color="black", linestyle="--", linewidth=1, label="Current k=6")
    plt.xlabel("Number of clusters")
    plt.ylabel("Score")
    plt.title("Alternative Clusterability Check")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "alternative_k_clusterability.png", dpi=220)
    plt.close()
    return out


def knn_network_quality(sampled_scaled_df, label_col, out_dir, random_state):
    feature_cols = numeric_feature_columns(sampled_scaled_df, label_col)
    X = sampled_scaled_df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()
    wallets = sampled_scaled_df["wallet"].tolist()
    labels = dict(zip(sampled_scaled_df["wallet"], sampled_scaled_df[label_col].astype(int)))

    n_neighbors = min(11, len(wallets))
    nbrs = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
    nbrs.fit(X)
    distances, indices = nbrs.kneighbors(X)

    neighbor_sets = {}
    for i, wallet in enumerate(wallets):
        neighbor_sets[wallet] = set(wallets[j] for j in indices[i][1:])

    graph = nx.Graph()
    for wallet in wallets:
        graph.add_node(wallet, cluster=labels[wallet])

    for i, wallet in enumerate(wallets):
        for j_idx, dist in zip(indices[i][1:], distances[i][1:]):
            other = wallets[j_idx]
            if wallet in neighbor_sets[other] and not graph.has_edge(wallet, other):
                graph.add_edge(wallet, other, weight=max(1 - float(dist), 1e-6))

    singletons = [n for n, d in graph.degree() if d == 0]
    graph.remove_nodes_from(singletons)

    intra = sum(1 for u, v in graph.edges() if graph.nodes[u]["cluster"] == graph.nodes[v]["cluster"])
    total = graph.number_of_edges()
    communities = {}
    for node, data in graph.nodes(data=True):
        communities.setdefault(data["cluster"], set()).add(node)

    modularity = nx.algorithms.community.quality.modularity(
        graph, list(communities.values()), weight="weight"
    ) if len(communities) > 1 and total > 0 else np.nan

    detected = list(nx.algorithms.community.greedy_modularity_communities(graph, weight="weight")) if total else []
    node_to_detected = {}
    for i, comm in enumerate(detected):
        for node in comm:
            node_to_detected[node] = i
    ari = adjusted_rand_score(
        [graph.nodes[n]["cluster"] for n in graph.nodes()],
        [node_to_detected[n] for n in graph.nodes()],
    ) if detected else np.nan

    out = pd.DataFrame([{
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph) if graph.number_of_nodes() > 1 else np.nan,
        "intra_cluster_edge_ratio": intra / total if total else np.nan,
        "inter_cluster_edge_ratio": 1 - (intra / total) if total else np.nan,
        "label_modularity": modularity,
        "detected_communities": len(detected),
        "ari_detected_vs_kmeans6": ari,
    }])
    out.to_csv(out_dir / "knn_network_quality.csv", index=False)
    return out


def temporal_cluster_network(labels_path, raw_tsv_path, label_col, out_dir, chunksize):
    labels = pd.read_csv(labels_path, dtype={"wallet": str})
    labels["wallet"] = clean_wallet(labels["wallet"])
    labels = labels.drop_duplicates("wallet")
    labels[label_col] = labels[label_col].astype(int)
    label_map = labels.set_index("wallet")[label_col].to_dict()

    daily_parts = []
    pair_counts = {}
    pair_values = {}
    total_rows = 0
    kept_rows = 0

    usecols = ["time", "sender", "recipient", "value"]
    for chunk in pd.read_csv(
        raw_tsv_path,
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
        kept_rows += len(chunk)
        if chunk.empty:
            continue

        chunk["source_cluster"] = chunk["source_cluster"].astype(int)
        chunk["target_cluster"] = chunk["target_cluster"].astype(int)
        chunk["date"] = pd.to_datetime(chunk["time"], errors="coerce").dt.date
        chunk["value"] = pd.to_numeric(chunk["value"], errors="coerce").fillna(0.0)

        grouped = chunk.groupby(["date", "source_cluster", "target_cluster"]).agg(
            tx_count=("value", "size"),
            total_value=("value", "sum"),
        ).reset_index()
        daily_parts.append(grouped)

        for row in grouped.itertuples(index=False):
            key = (int(row.source_cluster), int(row.target_cluster))
            pair_counts[key] = pair_counts.get(key, 0) + int(row.tx_count)
            pair_values[key] = pair_values.get(key, 0.0) + float(row.total_value)

    if daily_parts:
        daily = pd.concat(daily_parts, ignore_index=True)
        daily = daily.groupby(["date", "source_cluster", "target_cluster"], as_index=False).agg(
            tx_count=("tx_count", "sum"),
            total_value=("total_value", "sum"),
        )
    else:
        daily = pd.DataFrame(columns=["date", "source_cluster", "target_cluster", "tx_count", "total_value"])

    daily.to_csv(out_dir / "cluster_pair_daily_transactions.csv", index=False)

    clusters = sorted(labels[label_col].dropna().astype(int).unique())
    count_matrix = pd.DataFrame(0, index=clusters, columns=clusters, dtype=np.int64)
    value_matrix = pd.DataFrame(0.0, index=clusters, columns=clusters)
    for (src, dst), count in pair_counts.items():
        count_matrix.loc[src, dst] = count
        value_matrix.loc[src, dst] = pair_values.get((src, dst), 0.0)

    count_matrix.to_csv(out_dir / "cluster_adjacency_tx_counts.csv")
    value_matrix.to_csv(out_dir / "cluster_adjacency_values.csv")

    graph = nx.from_pandas_adjacency(count_matrix, create_using=nx.DiGraph)
    metrics = []
    for cluster in clusters:
        metrics.append({
            "cluster": cluster,
            "weighted_out_degree": graph.out_degree(cluster, weight="weight"),
            "weighted_in_degree": graph.in_degree(cluster, weight="weight"),
            "self_loop_tx": graph.get_edge_data(cluster, cluster, default={}).get("weight", 0),
        })
    network_metrics = pd.DataFrame(metrics)
    network_metrics["external_out_tx"] = network_metrics["weighted_out_degree"] - network_metrics["self_loop_tx"]
    network_metrics["external_in_tx"] = network_metrics["weighted_in_degree"] - network_metrics["self_loop_tx"]
    network_metrics.to_csv(out_dir / "cluster_network_metrics.csv", index=False)

    summary = pd.DataFrame([{
        "raw_rows_read": total_rows,
        "rows_with_both_cluster_labels": kept_rows,
        "coverage_ratio": kept_rows / total_rows if total_rows else np.nan,
        "graph_reciprocity": nx.reciprocity(graph) if graph.number_of_edges() else np.nan,
    }])
    summary.to_csv(out_dir / "transaction_network_coverage.csv", index=False)

    if not daily.empty:
        daily["date"] = pd.to_datetime(daily["date"])
        focus = daily[
            ((daily["source_cluster"] == 1) & (daily["target_cluster"] == 4)) |
            ((daily["source_cluster"] == 4) & (daily["target_cluster"] == 1))
        ].copy()
        if not focus.empty:
            pivot = focus.pivot_table(
                index="date",
                columns=["source_cluster", "target_cluster"],
                values="tx_count",
                aggfunc="sum",
                fill_value=0,
            )
            pivot.columns = [f"c{src}_to_c{dst}_tx" for src, dst in pivot.columns]
            pivot.to_csv(out_dir / "c1_c4_daily_connection_timeseries.csv")
            plt.figure(figsize=(10, 4.8))
            for col in pivot.columns:
                plt.plot(pivot.index, pivot[col], marker="o", linewidth=1.4, label=col.replace("_tx", "").replace("_to_", " -> ").upper())
            plt.xlabel("Date")
            plt.ylabel("Transactions")
            plt.title("Temporal Connection Between Cluster 1 and Cluster 4")
            plt.legend()
            plt.tight_layout()
            plt.savefig(out_dir / "c1_c4_daily_connection_timeseries.png", dpi=220)
            plt.close()

        plt.figure(figsize=(7, 5.8))
        plt.imshow(np.log1p(count_matrix.to_numpy()), aspect="auto")
        plt.xticks(range(len(clusters)), [f"C{c}" for c in clusters])
        plt.yticks(range(len(clusters)), [f"C{c}" for c in clusters])
        plt.xlabel("Target cluster")
        plt.ylabel("Source cluster")
        plt.title("Cluster-to-Cluster Transaction Network, log(1 + tx)")
        plt.colorbar(label="log(1 + transaction count)")
        plt.tight_layout()
        plt.savefig(out_dir / "cluster_adjacency_tx_counts_heatmap.png", dpi=220)
        plt.close()

    return summary, network_metrics


def write_markdown(month, out_dir, behavior, global_tests, pair_tests, alt_k, knn_quality):
    strongest_pairs = pair_tests[pair_tests["q_value_bh"] < 0.05].sort_values("effect_size_abs", ascending=False).head(12)
    md = []
    md.append(f"# Network Science Cluster Analysis - {month}\n")
    md.append("## Supervisor Questions Mapped to Outputs\n")
    md.append("- Daha farkli clusterlara ayrilabilir mi: `alternative_k_clusterability.csv/png` checks k=3..10 against silhouette and ARI.")
    md.append("- Clusterlari daha fazla nasil tanimlayabiliriz: `cluster_behavior_labels.csv` gives behavior labels and strongest features.")
    md.append("- Farkli clusterlar istatistiksel olarak ne kadar farkli: `cluster_global_statistical_tests.csv` and `cluster_pairwise_statistical_tests.csv` use Kruskal-Wallis, Mann-Whitney U, Cliff's delta, and BH-FDR q-values.")
    md.append("- C1 ve C4 arasinda baglanti yok gibi ama zamanla degisiyor mu: `c1_c4_daily_connection_timeseries.csv/png` tracks C1->C4 and C4->C1 by day.")
    md.append("- Clusterlar manali insan davranislari ifade ediyor mu: behavior labels should be interpreted as wallet behavior types, then checked against event/context knowledge.\n")

    md.append("## Cluster Behavior Labels\n")
    md.append(behavior.to_markdown(index=False))
    md.append("\n## KNN Network Quality\n")
    md.append(knn_quality.to_markdown(index=False))
    md.append("\n## Alternative k Check\n")
    md.append(alt_k.to_markdown(index=False))
    md.append("\n## Strongest Pairwise Statistical Differences\n")
    md.append(strongest_pairs.to_markdown(index=False))
    md.append("\n## Globally Most Different Features\n")
    md.append(global_tests.head(12).to_markdown(index=False))

    (out_dir / "network_science_summary.md").write_text("\n".join(md), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Network-science analysis for Ethereum wallet clusters.")
    parser.add_argument("--month", default="202209")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--label-col", default="cluster_1", help="Use cluster_1 for KMeans6, cluster_2 for the other assistant's labels.")
    parser.add_argument("--sample-per-cluster", type=int, default=4000)
    parser.add_argument("--chunksize", type=int, default=750000)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--skip-raw-network", action="store_true")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    paths = month_paths(base_dir, args.month)
    out_dir = paths["month_dir"] / "network_science_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    full_df, sampled_df = load_feature_sample(paths["features"], args.label_col, args.sample_per_cluster, args.random_state)
    scaled_full = pd.read_csv(paths["scaled"], dtype={"wallet": str})
    scaled_full["wallet"] = clean_wallet(scaled_full["wallet"])
    if args.label_col in scaled_full.columns:
        scaled_full = scaled_full.dropna(subset=[args.label_col]).copy()
        scaled_full[args.label_col] = scaled_full[args.label_col].astype(int)
    else:
        scaled_full = scaled_full.merge(
            full_df[["wallet", args.label_col]].drop_duplicates("wallet"),
            on="wallet",
            how="inner",
        )
    scaled_sample = scaled_full[scaled_full["wallet"].isin(sampled_df["wallet"])].copy()

    _, behavior = describe_clusters(scaled_full, args.label_col, out_dir)
    global_tests, pair_tests = statistical_tests(sampled_df, args.label_col, out_dir)
    alt_k = alternative_clusterability(scaled_sample, args.label_col, out_dir, args.random_state)
    knn_quality = knn_network_quality(scaled_sample, args.label_col, out_dir, args.random_state)

    if not args.skip_raw_network:
        temporal_cluster_network(paths["labels"], paths["raw_tsv"], args.label_col, out_dir, args.chunksize)

    write_markdown(args.month, out_dir, behavior, global_tests, pair_tests, alt_k, knn_quality)
    print(f"Saved network science analysis to: {out_dir}")


if __name__ == "__main__":
    main()
