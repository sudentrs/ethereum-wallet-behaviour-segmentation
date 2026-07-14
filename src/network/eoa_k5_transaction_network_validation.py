import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd


def clean_wallet(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def load_labels(path: Path) -> pd.DataFrame:
    labels = pd.read_csv(path, usecols=["wallet", "cluster"], dtype={"wallet": str})
    labels["wallet"] = clean_wallet(labels["wallet"])
    labels["cluster"] = labels["cluster"].astype(int)
    return labels.drop_duplicates("wallet")


def sample_edges_for_null(edges: pd.DataFrame, sample_size: int, random_state: int) -> pd.DataFrame:
    if len(edges) <= sample_size:
        return edges.copy()
    return edges.sample(n=sample_size, random_state=random_state).reset_index(drop=True)


def permutation_same_cluster_test(
    sampled_edges: pd.DataFrame,
    null_permutations: int,
    random_state: int,
) -> dict:
    if sampled_edges.empty:
        return {
            "sample_edges": 0,
            "observed_sample_same_cluster_ratio": np.nan,
            "null_mean": np.nan,
            "null_std": np.nan,
            "null_max": np.nan,
            "p_value_upper": np.nan,
        }

    observed = float((sampled_edges["source_cluster"] == sampled_edges["target_cluster"]).mean())
    wallets = pd.Index(pd.concat([sampled_edges["sender"], sampled_edges["recipient"]]).unique())
    wallet_to_pos = {wallet: pos for pos, wallet in enumerate(wallets)}
    labels = pd.Series(index=wallets, dtype="int64")
    source_labels = sampled_edges.drop_duplicates("sender").set_index("sender")["source_cluster"]
    target_labels = sampled_edges.drop_duplicates("recipient").set_index("recipient")["target_cluster"]
    labels.loc[source_labels.index] = source_labels
    labels.loc[target_labels.index] = labels.loc[target_labels.index].fillna(target_labels)
    labels = labels.astype(int).to_numpy()

    src_pos = sampled_edges["sender"].map(wallet_to_pos).to_numpy()
    dst_pos = sampled_edges["recipient"].map(wallet_to_pos).to_numpy()
    rng = np.random.default_rng(random_state)
    null_scores = []
    for _ in range(null_permutations):
        shuffled = labels.copy()
        rng.shuffle(shuffled)
        null_scores.append(float((shuffled[src_pos] == shuffled[dst_pos]).mean()))

    null = np.array(null_scores, dtype=float)
    p_value = (1 + np.sum(null >= observed)) / (len(null) + 1)
    return {
        "sample_edges": int(len(sampled_edges)),
        "observed_sample_same_cluster_ratio": observed,
        "null_mean": float(null.mean()),
        "null_std": float(null.std(ddof=1)) if len(null) > 1 else 0.0,
        "null_max": float(null.max()),
        "p_value_upper": float(p_value),
    }


def build_sample_wallet_graph(sampled_edges: pd.DataFrame) -> tuple[nx.Graph, pd.DataFrame]:
    pair_counts = (
        sampled_edges.groupby(["sender", "recipient", "source_cluster", "target_cluster"])
        .size()
        .reset_index(name="weight")
    )
    graph = nx.Graph()
    for row in pair_counts.itertuples(index=False):
        graph.add_node(row.sender, cluster=int(row.source_cluster))
        graph.add_node(row.recipient, cluster=int(row.target_cluster))
        if graph.has_edge(row.sender, row.recipient):
            graph[row.sender][row.recipient]["weight"] += int(row.weight)
        else:
            graph.add_edge(row.sender, row.recipient, weight=int(row.weight))
    return graph, pair_counts


def wallet_graph_metrics(sampled_edges: pd.DataFrame) -> dict:
    if sampled_edges.empty:
        return {
            "sample_wallet_graph_nodes": 0,
            "sample_wallet_graph_edges": 0,
            "sample_wallet_graph_density": np.nan,
            "sample_wallet_label_modularity": np.nan,
            "sample_wallet_attribute_assortativity": np.nan,
            "sample_wallet_intra_cluster_edge_ratio": np.nan,
        }

    graph, _ = build_sample_wallet_graph(sampled_edges)
    clusters = sorted({data["cluster"] for _, data in graph.nodes(data=True)})
    communities = [
        {node for node, data in graph.nodes(data=True) if data["cluster"] == cluster}
        for cluster in clusters
    ]
    total_weight = sum(data.get("weight", 1) for _, _, data in graph.edges(data=True))
    intra_weight = sum(
        data.get("weight", 1)
        for source, target, data in graph.edges(data=True)
        if graph.nodes[source]["cluster"] == graph.nodes[target]["cluster"]
    )
    modularity = (
        nx.algorithms.community.quality.modularity(graph, communities, weight="weight")
        if graph.number_of_edges()
        else np.nan
    )
    assortativity = (
        nx.attribute_assortativity_coefficient(graph, "cluster")
        if graph.number_of_edges()
        else np.nan
    )
    return {
        "sample_wallet_graph_nodes": graph.number_of_nodes(),
        "sample_wallet_graph_edges": graph.number_of_edges(),
        "sample_wallet_graph_density": nx.density(graph) if graph.number_of_nodes() > 1 else np.nan,
        "sample_wallet_label_modularity": modularity,
        "sample_wallet_attribute_assortativity": assortativity,
        "sample_wallet_intra_cluster_edge_ratio": intra_weight / total_weight if total_weight else np.nan,
    }


def plot_matrix(matrix: pd.DataFrame, path: Path, title: str, label: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 5.8))
    data = matrix.to_numpy(dtype=float)
    im = ax.imshow(data, aspect="auto", cmap="viridis")
    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels([f"C{c}" for c in matrix.columns])
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels([f"C{c}" for c in matrix.index])
    ax.set_xlabel("Target cluster")
    ax.set_ylabel("Source cluster")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label=label)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def write_report(
    out_dir: Path,
    month: str,
    analysis_label: str,
    report_stem: str,
    summary: dict,
    adjacency: pd.DataFrame,
    centrality: pd.DataFrame,
) -> None:
    if pd.notna(summary.get("p_value_upper", np.nan)) and summary["p_value_upper"] <= 0.05:
        network_commentary = (
            f"For this {analysis_label} run, the observed sampled same-cluster ratio was above the randomized-label null. "
            f"This supports the claim that {analysis_label} roles have non-random within-role transaction-network alignment."
        )
    else:
        network_commentary = (
            f"For this {analysis_label} run, the observed sampled same-cluster ratio was "
            f"`{summary.get('observed_sample_same_cluster_ratio', np.nan):.4f}`, while the randomized-label "
            f"null mean was `{summary.get('null_mean', np.nan):.4f}` with an upper-tail p-value of "
            f"`{summary.get('p_value_upper', np.nan):.4f}`. Therefore, this specific same-cluster network test "
            f"does not support the claim that {analysis_label} roles form stronger within-role transaction structure than random labels. "
            f"The {analysis_label} network evidence should be reported as mixed."
        )
    lines = [
        f"# {analysis_label} Transaction-Network Validation - {month}",
        "",
        "## Purpose",
        "",
        f"This analysis checks whether the {analysis_label} wallet roles also appear in the real transaction network. A defensible behavioural taxonomy should not only separate wallets in feature space; wallets with the same or related roles should show non-random interaction structure.",
        "",
        "## Main Metrics",
        "",
        pd.DataFrame([summary]).to_markdown(index=False),
        "",
        "## Role-To-Role Transaction Count Matrix",
        "",
        adjacency.to_markdown(),
        "",
        "## Cluster Network Centrality",
        "",
        centrality.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        f"The key proof-style check is the random-label comparison. It shuffles wallet cluster labels while preserving the same sampled transaction pairs. If the observed same-cluster transaction ratio is above the randomized ratios, then the {analysis_label} labels are aligned with transaction-network structure rather than behaving like arbitrary labels.",
        "",
        network_commentary,
        "",
        "The role-level adjacency matrix shows which behavioural roles exchange transactions with each other. Strong diagonal values indicate within-role interaction, while strong off-diagonal values identify bridges between behavioural roles.",
        "",
        "The wallet-graph modularity and assortativity metrics are sample-based network checks. Higher values indicate that wallet labels are organized in the transaction graph rather than being evenly mixed.",
    ]
    (out_dir / f"{report_stem}_transaction_network_validation_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate EOA-only K5 clusters with raw transaction-network structure.")
    parser.add_argument("--cluster-file", required=True)
    parser.add_argument("--raw-tsv", required=True)
    parser.add_argument("--out-dir", default="results/eoa_only_kmeans5/network_validation")
    parser.add_argument("--month", default="202209")
    parser.add_argument("--analysis-label", default="EOA-Only K5")
    parser.add_argument("--report-stem", default="eoa_k5")
    parser.add_argument("--chunksize", type=int, default=750_000)
    parser.add_argument("--null-sample-size", type=int, default=200_000)
    parser.add_argument("--null-permutations", type=int, default=100)
    parser.add_argument("--random-state", type=int, default=492)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(exist_ok=True)

    labels = load_labels(Path(args.cluster_file))
    label_map = labels.set_index("wallet")["cluster"].to_dict()
    clusters = sorted(labels["cluster"].unique())
    count_matrix = pd.DataFrame(0, index=clusters, columns=clusters, dtype=np.int64)
    value_matrix = pd.DataFrame(0.0, index=clusters, columns=clusters)

    total_rows = 0
    covered_rows = 0
    sampled_parts = []
    usecols = ["time", "sender", "recipient", "value"]
    for chunk_id, chunk in enumerate(
        pd.read_csv(
            args.raw_tsv,
            sep="\t",
            usecols=usecols,
            dtype={"sender": str, "recipient": str, "value": str},
            chunksize=args.chunksize,
        ),
        start=1,
    ):
        total_rows += len(chunk)
        chunk["sender"] = clean_wallet(chunk["sender"])
        chunk["recipient"] = clean_wallet(chunk["recipient"])
        chunk["source_cluster"] = chunk["sender"].map(label_map)
        chunk["target_cluster"] = chunk["recipient"].map(label_map)
        chunk = chunk.dropna(subset=["source_cluster", "target_cluster"]).copy()
        covered_rows += len(chunk)
        if chunk.empty:
            print(f"chunk={chunk_id:03d} total={total_rows:,} covered={covered_rows:,}", flush=True)
            continue

        chunk["source_cluster"] = chunk["source_cluster"].astype(int)
        chunk["target_cluster"] = chunk["target_cluster"].astype(int)
        chunk["value_numeric"] = pd.to_numeric(chunk["value"], errors="coerce").fillna(0.0)

        grouped = chunk.groupby(["source_cluster", "target_cluster"]).agg(
            tx_count=("value_numeric", "size"),
            total_value=("value_numeric", "sum"),
        ).reset_index()
        for row in grouped.itertuples(index=False):
            count_matrix.loc[int(row.source_cluster), int(row.target_cluster)] += int(row.tx_count)
            value_matrix.loc[int(row.source_cluster), int(row.target_cluster)] += float(row.total_value)

        if sum(len(part) for part in sampled_parts) < args.null_sample_size * 2:
            sampled_parts.append(
                chunk[["sender", "recipient", "source_cluster", "target_cluster"]]
                .sample(n=min(len(chunk), max(1, args.null_sample_size // 10)), random_state=args.random_state + chunk_id)
            )
        print(f"chunk={chunk_id:03d} total={total_rows:,} covered={covered_rows:,}", flush=True)

    sampled_edges = (
        sample_edges_for_null(pd.concat(sampled_parts, ignore_index=True), args.null_sample_size, args.random_state)
        if sampled_parts
        else pd.DataFrame(columns=["sender", "recipient", "source_cluster", "target_cluster"])
    )

    count_matrix.to_csv(out_dir / "cluster_adjacency_tx_counts.csv")
    value_matrix.to_csv(out_dir / "cluster_adjacency_values.csv")
    plot_matrix(
        np.log1p(count_matrix),
        fig_dir / "cluster_adjacency_tx_counts_log_heatmap.png",
        f"{args.analysis_label} Cluster-To-Cluster Transactions",
        "log(1 + tx count)",
    )

    graph = nx.from_pandas_adjacency(count_matrix, create_using=nx.DiGraph)
    centrality_rows = []
    for cluster in clusters:
        self_loop = count_matrix.loc[cluster, cluster]
        out_weight = graph.out_degree(cluster, weight="weight")
        in_weight = graph.in_degree(cluster, weight="weight")
        centrality_rows.append(
            {
                "cluster": cluster,
                "weighted_out_degree": int(out_weight),
                "weighted_in_degree": int(in_weight),
                "self_loop_tx": int(self_loop),
                "external_out_tx": int(out_weight - self_loop),
                "external_in_tx": int(in_weight - self_loop),
                "net_external_in_minus_out": int((in_weight - self_loop) - (out_weight - self_loop)),
            }
        )
    centrality = pd.DataFrame(centrality_rows)
    centrality.to_csv(out_dir / "cluster_network_centrality.csv", index=False)

    total_cluster_tx = int(count_matrix.to_numpy().sum())
    self_loop_tx = int(np.trace(count_matrix.to_numpy()))
    null = permutation_same_cluster_test(sampled_edges, args.null_permutations, args.random_state)
    graph_stats = wallet_graph_metrics(sampled_edges)
    summary = {
        "month": args.month,
        "cluster_wallets": int(labels["wallet"].nunique()),
        "raw_rows_read": int(total_rows),
        "rows_with_both_cluster_labels": int(covered_rows),
        "coverage_ratio": covered_rows / total_rows if total_rows else np.nan,
        "total_cluster_labeled_tx": total_cluster_tx,
        "self_loop_tx": self_loop_tx,
        "self_loop_ratio_all_labeled_tx": self_loop_tx / total_cluster_tx if total_cluster_tx else np.nan,
        **null,
        **graph_stats,
    }
    pd.DataFrame([summary]).to_csv(out_dir / "network_validation_summary.csv", index=False)
    sampled_edges.to_csv(out_dir / "sampled_edges_for_null_test.csv", index=False)
    write_report(out_dir, args.month, args.analysis_label, args.report_stem, summary, count_matrix, centrality)
    print(pd.DataFrame([summary]).to_string(index=False), flush=True)
    print(f"Saved {args.analysis_label} transaction-network validation to: {out_dir.resolve()}", flush=True)


if __name__ == "__main__":
    main()
