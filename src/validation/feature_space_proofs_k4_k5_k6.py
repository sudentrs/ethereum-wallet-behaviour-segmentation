from __future__ import annotations

from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu
from sklearn.metrics import adjusted_rand_score
from sklearn.neighbors import NearestNeighbors


ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / "wallet_eoa_only_kmeans6_features_robust_scaled" / "wallet_eoa_only_kmeans6_features_robust_scaled.csv"
OUT_DIR = ROOT / "results" / "academic_paper_pack" / "feature_space_proofs"


def clean_wallet(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def feature_cols(df: pd.DataFrame) -> list[str]:
    banned = {"wallet", "cluster", "old_cluster", "first_active_date", "last_active_date"}
    return [col for col in df.columns if col not in banned and pd.api.types.is_numeric_dtype(df[col])]


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) == 0 or len(y) == 0:
        return np.nan
    combined = np.concatenate([x, y])
    ranks = pd.Series(combined).rank(method="average").to_numpy()
    rx = ranks[: len(x)].sum()
    return float((2 * rx - len(x) * (len(x) + 1) - len(x) * len(y)) / (len(x) * len(y)))


def fdr_bh(p_values: pd.Series) -> np.ndarray:
    p = p_values.to_numpy(dtype=float)
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


def load_labels(k: int) -> pd.DataFrame:
    labels = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv", dtype={"wallet": str})
    labels["wallet"] = clean_wallet(labels["wallet"])
    labels["cluster"] = labels["cluster"].astype(int)
    return labels.drop_duplicates("wallet")


def load_feature_sample(k: int, sample_per_cluster: int = 5000, random_state: int = 492) -> pd.DataFrame:
    labels = load_labels(k)
    parts = []
    for cluster, sub in labels.groupby("cluster"):
        n = min(sample_per_cluster, len(sub))
        parts.append(sub.sample(n=n, random_state=random_state + int(cluster)))
    sampled_wallets = pd.concat(parts, ignore_index=True)
    wanted = set(sampled_wallets["wallet"])

    chunks = []
    usecols = None
    for chunk in pd.read_csv(FEATURES, dtype={"wallet": str}, chunksize=250_000):
        chunk["wallet"] = clean_wallet(chunk["wallet"])
        kept = chunk[chunk["wallet"].isin(wanted)].copy()
        if not kept.empty:
            chunks.append(kept)
        if usecols is None:
            usecols = chunk.columns.tolist()
    features = pd.concat(chunks, ignore_index=True)
    feature_cluster_cols = [col for col in features.columns if col in {"cluster", "old_cluster"}]
    features = features.drop(columns=feature_cluster_cols)
    out = sampled_wallets.merge(features, on="wallet", how="inner")
    out["cluster"] = out["cluster"].astype(int)
    return out


def global_feature_tests(df: pd.DataFrame, k: int, out_dir: Path) -> pd.DataFrame:
    cols = feature_cols(df)
    rows = []
    n = len(df)
    clusters = sorted(df["cluster"].unique())
    for col in cols:
        groups = [
            sub[col].replace([np.inf, -np.inf], np.nan).dropna().to_numpy(dtype=float)
            for _, sub in df.groupby("cluster")
        ]
        stat, p_value = kruskal(*groups)
        epsilon_sq = max(0.0, (stat - len(clusters) + 1) / (n - len(clusters)))
        rows.append({"k": k, "feature": col, "kruskal_stat": stat, "p_value": p_value, "epsilon_squared": epsilon_sq})
    tests = pd.DataFrame(rows).sort_values(["epsilon_squared", "kruskal_stat"], ascending=False)
    tests["q_value_bh"] = fdr_bh(tests["p_value"])
    tests.to_csv(out_dir / f"k{k}_global_feature_separation_tests.csv", index=False)
    return tests


def pairwise_feature_tests(df: pd.DataFrame, k: int, out_dir: Path) -> pd.DataFrame:
    cols = feature_cols(df)
    rows = []
    for c_a, c_b in combinations(sorted(df["cluster"].unique()), 2):
        a = df[df["cluster"] == c_a]
        b = df[df["cluster"] == c_b]
        for col in cols:
            x = a[col].replace([np.inf, -np.inf], np.nan).dropna().to_numpy(dtype=float)
            y = b[col].replace([np.inf, -np.inf], np.nan).dropna().to_numpy(dtype=float)
            stat, p_value = mannwhitneyu(x, y, alternative="two-sided")
            delta = cliffs_delta(x, y)
            rows.append(
                {
                    "k": k,
                    "cluster_a": c_a,
                    "cluster_b": c_b,
                    "feature": col,
                    "median_a": float(np.nanmedian(x)),
                    "median_b": float(np.nanmedian(y)),
                    "median_difference_a_minus_b": float(np.nanmedian(x) - np.nanmedian(y)),
                    "p_value": p_value,
                    "cliffs_delta": delta,
                    "effect_size_abs": abs(delta),
                }
            )
    tests = pd.DataFrame(rows)
    tests["q_value_bh"] = fdr_bh(tests["p_value"])
    tests = tests.sort_values(["effect_size_abs", "q_value_bh"], ascending=[False, True])
    tests.to_csv(out_dir / f"k{k}_pairwise_feature_separation_tests.csv", index=False)
    return tests


def knn_network_quality(df: pd.DataFrame, k: int, out_dir: Path, n_neighbors: int = 11) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = feature_cols(df)
    X = df[cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy(dtype=np.float32)
    labels = df["cluster"].astype(int).to_numpy()
    nbrs = NearestNeighbors(n_neighbors=min(n_neighbors, len(df)), metric="cosine")
    nbrs.fit(X)
    _, indices = nbrs.kneighbors(X)

    graph = nx.Graph()
    for i, neighs in enumerate(indices):
        graph.add_node(i, cluster=int(labels[i]))
        for j in neighs[1:]:
            graph.add_node(int(j), cluster=int(labels[j]))
            graph.add_edge(i, int(j))

    total_edges = graph.number_of_edges()
    intra_edges = sum(
        1 for source, target in graph.edges() if graph.nodes[source]["cluster"] == graph.nodes[target]["cluster"]
    )
    clusters = sorted(np.unique(labels))
    communities = [{node for node, data in graph.nodes(data=True) if data["cluster"] == cluster} for cluster in clusters]
    modularity = nx.algorithms.community.quality.modularity(graph, communities) if total_edges else np.nan
    assortativity = nx.attribute_assortativity_coefficient(graph, "cluster") if total_edges else np.nan
    try:
        detected = nx.algorithms.community.louvain_communities(graph, seed=492)
        node_to_detected = {}
        for community_id, nodes in enumerate(detected):
            for node in nodes:
                node_to_detected[node] = community_id
        ari = adjusted_rand_score([graph.nodes[n]["cluster"] for n in graph.nodes()], [node_to_detected[n] for n in graph.nodes()])
        detected_count = len(detected)
    except Exception:
        ari = np.nan
        detected_count = np.nan

    summary = pd.DataFrame(
        [
            {
                "k": k,
                "sample_wallets": len(df),
                "nodes": graph.number_of_nodes(),
                "edges": total_edges,
                "density": nx.density(graph) if graph.number_of_nodes() > 1 else np.nan,
                "intra_cluster_edge_ratio": intra_edges / total_edges if total_edges else np.nan,
                "label_modularity": modularity,
                "attribute_assortativity": assortativity,
                "detected_communities": detected_count,
                "ari_detected_vs_labels": ari,
            }
        ]
    )

    adjacency = pd.crosstab(
        pd.Series([labels[source] for source, _ in graph.edges()], name="source_cluster"),
        pd.Series([labels[target] for _, target in graph.edges()], name="target_cluster"),
    )
    adjacency = adjacency.reindex(index=clusters, columns=clusters).fillna(0).astype(int)

    summary.to_csv(out_dir / f"k{k}_knn_feature_network_quality.csv", index=False)
    adjacency.to_csv(out_dir / f"k{k}_knn_feature_network_adjacency.csv")

    fig, ax = plt.subplots(figsize=(7, 5.8))
    im = ax.imshow(np.log1p(adjacency.to_numpy(dtype=float)), cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(clusters)))
    ax.set_xticklabels([f"C{c}" for c in clusters])
    ax.set_yticks(range(len(clusters)))
    ax.set_yticklabels([f"C{c}" for c in clusters])
    ax.set_xlabel("Neighbour cluster")
    ax.set_ylabel("Source cluster")
    ax.set_title(f"EOA K{k} Feature-Space KNN Adjacency")
    fig.colorbar(im, ax=ax, label="log(1 + edges)")
    fig.tight_layout()
    fig.savefig(out_dir / f"k{k}_knn_feature_network_adjacency.png", dpi=220)
    plt.close(fig)

    return summary, adjacency


def write_report(summaries: list[pd.DataFrame], top_global: list[pd.DataFrame], top_pairwise: list[pd.DataFrame]) -> None:
    summary = pd.concat(summaries, ignore_index=True)
    global_table = pd.concat(top_global, ignore_index=True)
    pair_table = pd.concat(top_pairwise, ignore_index=True)
    lines = [
        "# Feature-Space Proofs For EOA K4/K5/K6",
        "",
        "## Purpose",
        "",
        "This reproduces the feature-space proof style used in the earlier six-cluster work: KNN neighbourhood structure, global feature-separation tests, and pairwise cluster-separation tests.",
        "",
        "## KNN Feature-Network Quality",
        "",
        summary.to_markdown(index=False),
        "",
        "## Strongest Global Feature Separations",
        "",
        global_table.to_markdown(index=False),
        "",
        "## Strongest Pairwise Feature Separations",
        "",
        pair_table.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "High intra-cluster KNN edge ratios and positive modularity show that cluster labels are visible in local feature-space neighbourhoods. Kruskal-Wallis and Mann-Whitney/Cliff's-delta tests confirm that cluster profiles differ on engineered behavioural features. These tests validate feature-space separation, not real-world identity labels.",
    ]
    (OUT_DIR / "feature_space_proofs_report.md").write_text("\n".join(lines), encoding="utf-8")
    summary.to_csv(OUT_DIR / "knn_feature_network_quality_all_k.csv", index=False)
    global_table.to_csv(OUT_DIR / "top_global_feature_separation_all_k.csv", index=False)
    pair_table.to_csv(OUT_DIR / "top_pairwise_feature_separation_all_k.csv", index=False)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    top_global = []
    top_pairwise = []
    for k in [4, 5, 6]:
        print(f"Processing feature-space proofs for K={k}", flush=True)
        k_out = OUT_DIR / f"k{k}"
        k_out.mkdir(exist_ok=True)
        sample = load_feature_sample(k)
        sample.to_csv(k_out / f"k{k}_feature_proof_sample.csv", index=False)
        summary, _ = knn_network_quality(sample, k, k_out)
        global_tests = global_feature_tests(sample, k, k_out)
        pairwise_tests = pairwise_feature_tests(sample, k, k_out)
        summaries.append(summary)
        top_global.append(global_tests.head(8))
        top_pairwise.append(pairwise_tests.head(12))
    write_report(summaries, top_global, top_pairwise)
    print(f"Saved feature-space proofs to: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
