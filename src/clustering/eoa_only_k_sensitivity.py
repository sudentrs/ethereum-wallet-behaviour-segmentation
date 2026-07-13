import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)


def numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    banned = {"wallet", "cluster", "old_cluster", "first_active_date", "last_active_date"}
    return [
        col
        for col in df.columns
        if col not in banned and pd.api.types.is_numeric_dtype(df[col])
    ]


def load_feature_rows(path: str, max_rows: int, chunksize: int, full_data: bool) -> pd.DataFrame:
    header = pd.read_csv(path, nrows=5000, dtype={"wallet": str})
    feature_cols = numeric_feature_columns(header)
    usecols = ["wallet", *feature_cols]

    parts = []
    threshold = max_rows
    modulo = 10_000_000
    for chunk_id, chunk in enumerate(
        pd.read_csv(path, usecols=usecols, dtype={"wallet": str}, chunksize=chunksize),
        start=1,
    ):
        if full_data:
            kept = chunk
        else:
            hashes = pd.util.hash_pandas_object(chunk["wallet"], index=False).astype("uint64")
            keep = (hashes % modulo) < threshold
            kept = chunk.loc[keep].copy()
        if not kept.empty:
            parts.append(kept)
        total_kept = sum(len(part) for part in parts)
        mode = "full" if full_data else "sample"
        print(f"{mode} chunk={chunk_id:03d} kept_so_far={total_kept:,}")

    rows = pd.concat(parts, ignore_index=True)
    if not full_data and len(rows) > max_rows:
        rows = rows.sample(n=max_rows, random_state=492).reset_index(drop=True)
    return rows


def parse_k_values(text: str) -> list[int]:
    if ".." in text:
        start, end = text.split("..", 1)
        return list(range(int(start), int(end) + 1))
    return [int(part.strip()) for part in text.split(",") if part.strip()]


def label_cluster_sizes(labels: np.ndarray) -> tuple[float, float]:
    counts = pd.Series(labels).value_counts(normalize=True)
    return float(counts.min()), float(counts.max())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run EOA-only k-sensitivity and seed-stability checks on a deterministic wallet sample."
    )
    parser.add_argument("--features", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--k-values", default="2..10")
    parser.add_argument("--sample-size", type=int, default=300_000)
    parser.add_argument(
        "--full-data",
        action="store_true",
        help="Use every row in the feature file instead of a deterministic sample.",
    )
    parser.add_argument("--chunksize", type=int, default=100_000)
    parser.add_argument("--seeds", default="492,493,494,495,496")
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--n-init", type=int, default=5)
    parser.add_argument("--max-iter", type=int, default=150)
    parser.add_argument("--silhouette-sample-size", type=int, default=50_000)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    k_values = parse_k_values(args.k_values)
    seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]

    sample = load_feature_rows(args.features, args.sample_size, args.chunksize, args.full_data)
    feature_cols = numeric_feature_columns(sample)
    X = (
        sample[feature_cols]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .to_numpy(dtype=np.float32)
    )
    sample[["wallet"]].to_csv(out_dir / "sample_wallets.csv", index=False)

    rng = np.random.default_rng(492)
    sil_n = min(args.silhouette_sample_size, len(sample))
    sil_idx = rng.choice(len(sample), size=sil_n, replace=False) if sil_n else np.arange(len(sample))

    run_rows = []
    label_by_k_seed = {}
    for k in k_values:
        for seed in seeds:
            model = MiniBatchKMeans(
                n_clusters=k,
                random_state=seed,
                batch_size=args.batch_size,
                n_init=args.n_init,
                max_iter=args.max_iter,
            )
            labels = model.fit_predict(X)
            label_by_k_seed[(k, seed)] = labels
            min_share, max_share = label_cluster_sizes(labels)
            sil = (
                silhouette_score(X[sil_idx], labels[sil_idx], random_state=seed)
                if len(np.unique(labels[sil_idx])) > 1
                else np.nan
            )
            db = davies_bouldin_score(X, labels)
            ch = calinski_harabasz_score(X, labels)
            run_rows.append(
                {
                    "k": k,
                    "seed": seed,
                    "sample_wallets": len(sample),
                    "feature_count": len(feature_cols),
                    "inertia": float(model.inertia_),
                    "silhouette": float(sil),
                    "davies_bouldin": float(db),
                    "calinski_harabasz": float(ch),
                    "min_cluster_share": min_share,
                    "max_cluster_share": max_share,
                }
            )
            print(f"k={k} seed={seed} silhouette={sil:.4f} min_share={min_share:.4f}")

    run_df = pd.DataFrame(run_rows)
    run_df.to_csv(out_dir / "k_sensitivity_runs.csv", index=False)

    stability_rows = []
    for k in k_values:
        for seed_a, seed_b in combinations(seeds, 2):
            labels_a = label_by_k_seed[(k, seed_a)]
            labels_b = label_by_k_seed[(k, seed_b)]
            stability_rows.append(
                {
                    "k": k,
                    "seed_a": seed_a,
                    "seed_b": seed_b,
                    "ari": adjusted_rand_score(labels_a, labels_b),
                    "nmi": normalized_mutual_info_score(labels_a, labels_b),
                }
            )
    stability = pd.DataFrame(stability_rows)
    stability.to_csv(out_dir / "k_seed_stability_pairs.csv", index=False)

    summary = (
        run_df.groupby("k")
        .agg(
            silhouette_mean=("silhouette", "mean"),
            silhouette_std=("silhouette", "std"),
            davies_bouldin_mean=("davies_bouldin", "mean"),
            calinski_harabasz_mean=("calinski_harabasz", "mean"),
            inertia_mean=("inertia", "mean"),
            min_cluster_share_mean=("min_cluster_share", "mean"),
            max_cluster_share_mean=("max_cluster_share", "mean"),
        )
        .reset_index()
        .merge(
            stability.groupby("k").agg(
                stability_ari_mean=("ari", "mean"),
                stability_ari_std=("ari", "std"),
                stability_nmi_mean=("nmi", "mean"),
                stability_nmi_std=("nmi", "std"),
            ).reset_index(),
            on="k",
            how="left",
        )
    )
    summary["rank_stability_ari"] = summary["stability_ari_mean"].rank(ascending=False, method="min")
    summary["rank_silhouette"] = summary["silhouette_mean"].rank(ascending=False, method="min")
    summary.to_csv(out_dir / "k_sensitivity_summary.csv", index=False)

    best_stability = summary.sort_values(["stability_ari_mean", "silhouette_mean"], ascending=False).iloc[0]
    best_silhouette = summary.sort_values(["silhouette_mean", "stability_ari_mean"], ascending=False).iloc[0]

    lines = [
        "# EOA-Only K Sensitivity And Seed Stability",
        "",
        f"Rows used: `{len(sample):,}` wallets.",
        f"Full data mode: `{args.full_data}`.",
        f"Seeds: `{', '.join(map(str, seeds))}`.",
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Recommended Reading",
        "",
        f"- Most seed-stable k by mean ARI: `k={int(best_stability['k'])}` "
        f"(ARI={best_stability['stability_ari_mean']:.3f}, silhouette={best_stability['silhouette_mean']:.3f}).",
        f"- Best k by silhouette: `k={int(best_silhouette['k'])}` "
        f"(silhouette={best_silhouette['silhouette_mean']:.3f}, ARI={best_silhouette['stability_ari_mean']:.3f}).",
        "",
        "Use this as a screening experiment. Final paper claims should combine stability, interpretability, role sizes, and downstream validation rather than choosing k from one metric alone.",
    ]
    (out_dir / "k_sensitivity_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(summary.to_string(index=False))
    print(f"Saved k-sensitivity outputs to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
