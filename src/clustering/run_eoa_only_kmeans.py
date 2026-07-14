import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score


def numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    banned = {"wallet", "cluster", "old_cluster", "first_active_date", "last_active_date"}
    return [
        col
        for col in df.columns
        if col not in banned and pd.api.types.is_numeric_dtype(df[col])
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run KMeans clustering on an EOA-only robust-scaled wallet feature table."
    )
    parser.add_argument("--features", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--random-state", type=int, default=492)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--n-init", type=int, default=10)
    parser.add_argument("--max-iter", type=int, default=200)
    parser.add_argument(
        "--silhouette-sample-size",
        type=int,
        default=50000,
        help="Rows sampled for silhouette. Use 0 to skip.",
    )
    parser.add_argument(
        "--write-feature-table",
        action="store_true",
        help="Write the full feature table with new cluster labels. This can be very large.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.features, dtype={"wallet": str})
    feature_cols = numeric_feature_columns(df)
    if not feature_cols:
        raise ValueError("No numeric feature columns found.")

    X = (
        df[feature_cols]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .to_numpy(dtype=np.float32)
    )
    model = MiniBatchKMeans(
        n_clusters=args.k,
        random_state=args.random_state,
        batch_size=args.batch_size,
        n_init=args.n_init,
        max_iter=args.max_iter,
    )
    labels = model.fit_predict(X)

    assignments = pd.DataFrame({"wallet": df["wallet"], "cluster": labels.astype(int)})
    assignments.to_csv(out_dir / "wallet_eoa_only_kmeans_clusters.csv", index=False)

    features_with_labels = df.copy()
    if "cluster" in features_with_labels.columns:
        features_with_labels = features_with_labels.rename(columns={"cluster": "old_cluster"})
    features_with_labels["cluster"] = labels.astype(int)
    if args.write_feature_table:
        features_with_labels.to_csv(
            out_dir / f"wallet_eoa_only_kmeans{args.k}_features_robust_scaled.csv",
            index=False,
        )

    sizes = assignments["cluster"].value_counts().sort_index().reset_index()
    sizes.columns = ["cluster", "wallet_count"]
    sizes["wallet_share"] = sizes["wallet_count"] / len(assignments)
    sizes.to_csv(out_dir / "cluster_sizes.csv", index=False)

    profiles = features_with_labels.groupby("cluster")[feature_cols].median().sort_index()
    profiles.to_csv(out_dir / "cluster_feature_medians_robust_scaled.csv")

    silhouette = np.nan
    if args.silhouette_sample_size:
        n_sample = min(args.silhouette_sample_size, len(df))
        if n_sample > args.k:
            rng = np.random.default_rng(args.random_state)
            idx = rng.choice(len(df), size=n_sample, replace=False)
            silhouette = float(
                silhouette_score(X[idx], labels[idx], random_state=args.random_state)
            )

    summary = pd.DataFrame(
        [
            {
                "features_file": args.features,
                "wallets_clustered": len(assignments),
                "feature_count": len(feature_cols),
                "k": args.k,
                "random_state": args.random_state,
                "inertia": float(model.inertia_),
                "silhouette_sample_size": int(args.silhouette_sample_size),
                "silhouette": silhouette,
            }
        ]
    )
    summary.to_csv(out_dir / "kmeans_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(f"Saved EOA-only clustering outputs to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
