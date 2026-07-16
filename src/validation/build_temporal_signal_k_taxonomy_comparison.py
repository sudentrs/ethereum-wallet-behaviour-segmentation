from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from build_temporal_signal_analysis_pack import clean_wallet, random_label_null_same_cluster


K_CLUSTER_FILES = {
    "k4": Path("results/eoa_only_kmeans4/wallet_eoa_only_kmeans_clusters.csv"),
    "k5": Path("results/eoa_only_kmeans5/wallet_eoa_only_kmeans_clusters.csv"),
    "k6": Path("results/eoa_only_kmeans6/wallet_eoa_only_kmeans_clusters.csv"),
}


def load_taxonomy_labels(path: Path, wallets: set[str], label_name: str, chunksize: int = 1_000_000) -> pd.DataFrame:
    parts = []
    for chunk in pd.read_csv(path, dtype={"wallet": str}, chunksize=chunksize):
        chunk["wallet"] = clean_wallet(chunk["wallet"])
        chunk = chunk[chunk["wallet"].isin(wallets)].copy()
        if chunk.empty:
            continue
        chunk = chunk[["wallet", "cluster"]].rename(columns={"cluster": label_name})
        chunk[label_name] = chunk[label_name].astype(int)
        parts.append(chunk)
    if not parts:
        raise ValueError(f"No sampled wallets matched {path}")
    return pd.concat(parts, ignore_index=True).drop_duplicates("wallet")


def build_enrichment(assignments: pd.DataFrame, taxonomy_col: str, signal_col: str) -> pd.DataFrame:
    counts = pd.crosstab(assignments[taxonomy_col], assignments[signal_col])
    shares = counts.div(counts.sum(axis=1), axis=0)
    rows = []
    for taxonomy_cluster in counts.index:
        for signal_cluster in counts.columns:
            rows.append(
                {
                    "taxonomy": taxonomy_col,
                    "taxonomy_cluster": int(taxonomy_cluster),
                    "signal_cluster_type": signal_col,
                    "signal_cluster": int(signal_cluster),
                    "wallet_count": int(counts.loc[taxonomy_cluster, signal_cluster]),
                    "within_taxonomy_cluster_share": float(shares.loc[taxonomy_cluster, signal_cluster]),
                }
            )
    return pd.DataFrame(rows)


def build_network_summary(
    edges_path: Path,
    assignments: pd.DataFrame,
    taxonomy_cols: list[str],
    signal_cols: list[str],
    permutations: int,
    random_state: int,
    out_dir: Path,
) -> pd.DataFrame:
    edges = pd.read_csv(edges_path, dtype={"sender": str, "recipient": str})
    edges["sender"] = clean_wallet(edges["sender"])
    edges["recipient"] = clean_wallet(edges["recipient"])
    label_map = assignments.set_index("wallet")

    rows = []
    for label_col in taxonomy_cols + signal_cols:
        edges[f"source_{label_col}"] = edges["sender"].map(label_map[label_col])
        edges[f"target_{label_col}"] = edges["recipient"].map(label_map[label_col])
        result = random_label_null_same_cluster(edges, label_col, permutations, random_state)
        result["label_type"] = label_col
        rows.append(result)

        valid = edges.dropna(subset=[f"source_{label_col}", f"target_{label_col}"])
        if not valid.empty:
            adjacency = pd.crosstab(valid[f"source_{label_col}"].astype(int), valid[f"target_{label_col}"].astype(int))
            adjacency.to_csv(out_dir / f"{label_col}_edge_adjacency_counts.csv")

    return pd.DataFrame(rows)[
        [
            "label_type",
            "edge_count",
            "observed_same_cluster_ratio",
            "null_mean",
            "null_std",
            "p_value_upper",
        ]
    ]


def write_report(
    out_dir: Path,
    source_signal_dir: Path,
    sample_size: int,
    correspondence: pd.DataFrame,
    network: pd.DataFrame,
) -> None:
    lines = [
        "# Temporal Signal K-Taxonomy Comparison",
        "",
        "## Purpose",
        "",
        "This pack compares whether the temporal signal results align more strongly with K4, K5, or K6 EOA taxonomies.",
        "",
        "It does not ask which K is globally best by itself. Instead, it asks whether the same wallets' wavelength and time-domain signal clusters reproduce any of the candidate static taxonomies.",
        "",
        "## Input",
        "",
        f"Signal-analysis source folder: `{source_signal_dir}`",
        f"Sample size: `{sample_size}` wallets",
        "",
        "## Correspondence Results",
        "",
        correspondence.to_markdown(index=False),
        "",
        "Interpretation: ARI and NMI are low when the temporal signal clusters do not reproduce the static taxonomy. This is useful because it tells us that frequency and time-domain behaviour add a separate axis rather than merely repeating aggregate KMeans labels.",
        "",
        "## Network Null Tests",
        "",
        network.to_markdown(index=False),
        "",
        "Interpretation: the network null test asks whether wallets with the same label transact with each other more often than expected after shuffling labels across the same sampled wallets.",
        "",
        "## Paper-Framing Comment",
        "",
        "The strongest conservative framing is that K4/K5/K6 describe static aggregate behavioural roles, while wavelength and time-domain clusters describe temporal behavioural states. A good paper contribution is the comparison between these layers, not a claim that one layer fully replaces the other.",
    ]
    (out_dir / "temporal_signal_k_taxonomy_comparison_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    out_dir = Path("results/temporal_signal_k_taxonomy_comparison")
    signal_dir = Path("results/temporal_signal_analysis_edge_sample_10k")
    edges_path = Path("results/eoa_only_kmeans5/network_validation/sampled_edges_for_null_test.csv")
    permutations = 100
    random_state = 492
    out_dir.mkdir(parents=True, exist_ok=True)

    assignments = pd.read_csv(signal_dir / "temporal_signal_cluster_assignments.csv", dtype={"wallet": str})
    assignments["wallet"] = clean_wallet(assignments["wallet"])
    wallets = set(assignments["wallet"])

    taxonomy_cols = []
    for name, path in K_CLUSTER_FILES.items():
        col = f"{name}_cluster"
        taxonomy_cols.append(col)
        if col in assignments.columns:
            assignments[col] = assignments[col].astype(int)
            continue
        labels = load_taxonomy_labels(path, wallets, col)
        assignments = assignments.merge(labels, on="wallet", how="left")

    assignments.to_csv(out_dir / "signal_sample_with_k4_k5_k6_labels.csv", index=False)

    signal_cols = ["wavelength_cluster", "time_domain_cluster"]
    correspondence_rows = []
    enrichment_parts = []
    for taxonomy_col in taxonomy_cols:
        for signal_col in signal_cols:
            valid = assignments.dropna(subset=[taxonomy_col, signal_col])
            correspondence_rows.append(
                {
                    "taxonomy": taxonomy_col,
                    "signal_cluster_type": signal_col,
                    "sample_wallets": len(valid),
                    "taxonomy_k": int(valid[taxonomy_col].nunique()),
                    "signal_k": int(valid[signal_col].nunique()),
                    "ari": adjusted_rand_score(valid[taxonomy_col], valid[signal_col]),
                    "nmi": normalized_mutual_info_score(valid[taxonomy_col], valid[signal_col]),
                }
            )
            enrichment_parts.append(build_enrichment(valid, taxonomy_col, signal_col))

    correspondence = pd.DataFrame(correspondence_rows)
    correspondence.to_csv(out_dir / "k_taxonomy_signal_correspondence.csv", index=False)
    pd.concat(enrichment_parts, ignore_index=True).to_csv(out_dir / "k_taxonomy_signal_enrichment.csv", index=False)

    network = build_network_summary(edges_path, assignments, taxonomy_cols, signal_cols, permutations, random_state, out_dir)
    network.to_csv(out_dir / "k_taxonomy_signal_network_null_tests.csv", index=False)

    write_report(out_dir, signal_dir, len(assignments), correspondence, network)
    print(f"Saved K-taxonomy signal comparison to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
