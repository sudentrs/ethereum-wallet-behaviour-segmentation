"""Assess K3 sensitivity to removing prespecified count/activity feature families."""
from __future__ import annotations

import argparse
import json
import hashlib
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from scipy.optimize import linear_sum_assignment
from threadpoolctl import threadpool_limits


FAMILIES = {
    "activity_level": ["active_days_observed", "total_tx", "avg_daily_tx_count", "max_daily_tx_count", "std_daily_tx_count"],
    "persistence_concentration": ["activity_span_days", "activity_density", "tx_count_cv", "tx_concentration_ratio"],
    "directionality": ["in_active_days", "out_active_days", "both_active_days", "in_active_day_ratio",
                         "out_active_day_ratio", "both_active_day_ratio", "in_out_day_balance"],
}


def aligned_agreement(reference: np.ndarray, candidate: np.ndarray, k: int) -> float:
    contingency = np.zeros((k, k), dtype=np.int64)
    np.add.at(contingency, (reference, candidate), 1)
    rows, cols = linear_sum_assignment(-contingency)
    return float(contingency[rows, cols].sum() / len(reference))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--reference-labels", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=492)
    parser.add_argument('--batch-size', type=int, default=8192)
    parser.add_argument('--n-init', type=int, default=10)
    parser.add_argument('--max-iter', type=int, default=200)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if min(args.batch_size, args.n_init, args.max_iter) < 1:
        parser.error('Fit settings must be positive')

    feature_columns = [col for col in pd.read_csv(args.features, nrows=0).columns
                       if col not in {"wallet", "cluster"}]
    dropped = {name: [feature_columns.index(col) for col in cols] for name, cols in FAMILIES.items()}
    x = np.load(args.matrix, mmap_mode="r")
    reference = np.load(args.reference_labels, mmap_mode="r").astype(np.int16, copy=False)
    if x.shape[0] != len(reference) or x.shape[1] != len(feature_columns):
        raise ValueError("Feature matrix, feature CSV, and reference labels are not aligned")

    results = []
    for name, indices in dropped.items():
        keep = np.array([i for i in range(x.shape[1]) if i not in indices])
        # The supplied matrix is already robust-scaled feature-wise; retaining columns preserves
        # the exact scaling used by the complete annual model.
        z = np.asarray(x[:, keep], dtype=np.float32)
        labels = MiniBatchKMeans(n_clusters=3, n_init=args.n_init, random_state=args.seed,
                                batch_size=args.batch_size, max_iter=args.max_iter).fit_predict(z).astype(np.int16)
        results.append({
            "removed_family": name,
            "features_removed": len(indices),
            "features_retained": len(keep),
            "ari_vs_full_k3": adjusted_rand_score(reference, labels),
            "nmi_vs_full_k3": normalized_mutual_info_score(reference, labels),
            "hungarian_agreement_vs_full_k3": aligned_agreement(reference, labels, 3),
        })
    result = pd.DataFrame(results)
    result.to_csv(args.out_dir / "k3_feature_holdout_sensitivity.csv", index=False)
    def sha256(path):
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(8*1024*1024), b''):
                digest.update(chunk)
        return digest.hexdigest()
    (args.out_dir / "k3_feature_holdout_manifest.json").write_text(json.dumps({
        "reference": str(args.reference_labels), "matrix": str(args.matrix),
        "reference_sha256": sha256(args.reference_labels), "matrix_sha256": sha256(args.matrix),
        "estimator": "MiniBatchKMeans", "batch_size": args.batch_size,
        "n_init": args.n_init, "max_iter": args.max_iter,
        "scikit_learn": sklearn.__version__, "python": platform.python_version(),
        "features": feature_columns, "families": FAMILIES, "seed": args.seed,
        "interpretation": "Feature-family holdouts measure representation sensitivity. They do not provide independent external validation."
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
