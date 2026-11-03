"""Fit reproducible K2--K6 count/activity models for the year-end cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import os

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
from threadpoolctl import threadpool_limits


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--wallet-source", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--k-values", default="2,3,4,5,6")
    parser.add_argument("--seeds", default="492,493,494")
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--n-init", type=int, default=10)
    parser.add_argument("--max-iter", type=int, default=200)
    parser.add_argument("--silhouette-sample-size", type=int, default=5_000,
                        help="Deterministic diagnostic sample; silhouette is quadratic in this size.")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    ks = [int(value) for value in args.k_values.split(",")]
    seeds = [int(value) for value in args.seeds.split(",")]
    if not ks or not seeds or min(ks) < 2 or args.batch_size < 1 or args.n_init < 1 or args.threads < 1:
        parser.error("Invalid k, seed, or fit settings")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    header = pd.read_csv(args.wallet_source, nrows=1, dtype={"wallet": "string"})
    features = [c for c in header.columns if c not in {"wallet", "cluster"}]
    wallets = pd.concat([chunk.wallet.astype("string") for chunk in pd.read_csv(
        args.wallet_source, usecols=["wallet"], dtype={"wallet": "string"}, chunksize=200_000)],
        ignore_index=True)
    if wallets.duplicated().any() or len(wallets) < max(ks):
        raise ValueError("Invalid wallet identifiers or insufficient rows")
    X = np.load(args.matrix, mmap_mode="r")
    if X.ndim != 2 or X.shape != (len(wallets), len(features)):
        raise ValueError("Scaled matrix shape does not match source feature order")
    if not np.isfinite(X).all():
        raise ValueError("Non-finite scaled features")
    sample_n = min(args.silhouette_sample_size, len(X))
    rng = np.random.default_rng(492)
    sample = rng.choice(len(X), size=sample_n, replace=False)
    wallets.to_frame(name="wallet").iloc[sample].to_csv(args.out_dir / "silhouette_sample_wallets.csv", index=False)
    run_manifest = {"matrix_file": str(args.matrix), "matrix_sha256": sha256(args.matrix),
                    "wallet_source": str(args.wallet_source), "wallet_source_sha256": sha256(args.wallet_source),
                    "wallet_count": len(X), "feature_columns": features, "k_values": ks,
                    "seeds": seeds, "batch_size": args.batch_size, "n_init": args.n_init,
                    "max_iter": args.max_iter, "silhouette_sample_size": sample_n,
                    "scikit_learn": sklearn.__version__, "python": platform.python_version()}
    (args.out_dir / "fit_manifest.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(args.threads))
    with threadpool_limits(limits=args.threads):
        for k in ks:
            for seed in seeds:
                labels_path = args.out_dir / f"k{k}_seed{seed}_labels.npy"
                summary_path = args.out_dir / f"k{k}_seed{seed}_summary.csv"
                model_path = args.out_dir / f"k{k}_seed{seed}_model.joblib"
                if labels_path.exists() or summary_path.exists() or model_path.exists():
                    raise FileExistsError(f"Existing output for K{k}, seed {seed}")
                print(f"starting K{k}, seed={seed}, n_init={args.n_init}", flush=True)
                model = MiniBatchKMeans(n_clusters=k, random_state=seed, n_init=args.n_init,
                                       batch_size=args.batch_size, max_iter=args.max_iter, verbose=0)
                labels = model.fit_predict(X)
                if len(np.unique(labels)) != k:
                    raise ValueError(f"K{k} seed {seed} produced fewer than k clusters")
                sizes = np.bincount(labels, minlength=k)
                np.save(args.out_dir / f"k{k}_seed{seed}_labels.npy", labels.astype(np.int8))
                joblib.dump(model, model_path)
                if seed == seeds[0]:
                    print(f"assigned K{k}, seed={seed}; computing silhouette on {sample_n:,} wallets", flush=True)
                    silhouette = float(silhouette_score(X[sample], labels[sample], random_state=seed))
                else:
                    silhouette = np.nan
                summary = {"k": k, "seed": seed, "wallets": len(X), "feature_count": len(features),
                           "inertia": float(model.inertia_), "silhouette": silhouette,
                           "min_cluster_share": float(sizes.min()/len(X)),
                           "max_cluster_share": float(sizes.max()/len(X)),
                           "labels_sha256": sha256(args.out_dir / f"k{k}_seed{seed}_labels.npy")}
                pd.DataFrame([summary]).to_csv(summary_path, index=False)
                print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
