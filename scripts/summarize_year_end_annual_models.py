"""Stream exact role profiles and stability from year-end annual model artifacts."""

from __future__ import annotations

import argparse
from itertools import combinations
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def align(reference: np.ndarray, candidate: np.ndarray, k: int) -> np.ndarray:
    counts = np.bincount(reference.astype(np.int64) * k + candidate, minlength=k*k).reshape(k, k)
    rows, cols = linear_sum_assignment(-counts)
    mapping = np.empty(k, dtype=int)
    mapping[cols] = rows
    return mapping[candidate]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fit-dir", type=Path, required=True)
    parser.add_argument("--raw-features", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--k-values", default="2,3,4,5,6")
    parser.add_argument("--seeds", default="492,493,494")
    parser.add_argument("--chunksize", type=int, default=200_000)
    parser.add_argument("--skip-profiles", action="store_true")
    args = parser.parse_args()
    ks = [int(item) for item in args.k_values.split(",")]
    seeds = [int(item) for item in args.seeds.split(",")]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((args.fit_dir / "fit_manifest.json").read_text())
    if manifest["wallet_source_sha256"] != digest(args.raw_features):
        raise ValueError("Raw feature source differs from the fitted model manifest")
    header = pd.read_csv(args.raw_features, nrows=1)
    features = [c for c in header.columns if c not in {"wallet", "cluster"}]
    if features != manifest["feature_columns"]:
        raise ValueError("Feature order differs from fitted model manifest")
    n = int(manifest["wallet_count"])
    labels: dict[tuple[int, int], np.ndarray] = {}
    run_rows, size_rows, stability_rows = [], [], []
    for k in ks:
        for seed in seeds:
            value = np.load(args.fit_dir / f"k{k}_seed{seed}_labels.npy")
            if value.shape != (n,) or not np.isin(value, np.arange(k)).all():
                raise ValueError(f"Invalid K{k}, seed={seed} labels")
            labels[k, seed] = value.astype(np.int8, copy=False)
            run_rows.append(pd.read_csv(args.fit_dir / f"k{k}_seed{seed}_summary.csv").iloc[0].to_dict())
            sizes = np.bincount(value, minlength=k)
            for cluster, count in enumerate(sizes):
                size_rows.append({"k": k, "seed": seed, "cluster": cluster,
                                  "wallet_count": int(count), "wallet_share": float(count/n)})
        for seed_a, seed_b in combinations(seeds, 2):
            a, b = labels[k, seed_a], labels[k, seed_b]
            aligned = align(a, b, k)
            stability_rows.append({"k": k, "seed_a": seed_a, "seed_b": seed_b,
                                   "ari": adjusted_rand_score(a, b),
                                   "nmi": normalized_mutual_info_score(a, b),
                                   "hungarian_agreement": float(np.mean(a == aligned)),
                                   "changed_wallets": int(np.count_nonzero(a != aligned))})
    pd.DataFrame(run_rows).to_csv(args.out_dir / "annual_fit_runs.csv", index=False)
    pd.DataFrame(size_rows).to_csv(args.out_dir / "annual_cluster_sizes.csv", index=False)
    pd.DataFrame(stability_rows).to_csv(args.out_dir / "annual_seed_stability.csv", index=False)

    if args.skip_profiles:
        output_manifest = {"raw_features_sha256": digest(args.raw_features), "fit_manifest": manifest,
                           "profiles": "not_computed_in_this_invocation"}
        (args.out_dir / "annual_summary_manifest.json").write_text(json.dumps(output_manifest, indent=2), encoding="utf-8")
        print("annual stability summary complete", flush=True)
        return

    # Exact raw profiles for the reference seed, with one feature streamed at a time.
    reference = seeds[0]
    profiles = []
    for k in ks:
        profile_path = args.out_dir / f"annual_exact_raw_profiles_seed{reference}_k{k}.csv"
        k_profiles = pd.read_csv(profile_path).to_dict("records") if profile_path.exists() else []
        completed = {feature for feature in features
                     if sum(item["feature"] == feature for item in k_profiles) == k}
        for feature in features:
            if feature in completed:
                print(f"reusing K{k} profile for {feature}", flush=True)
                continue
            values_by_cluster = {cluster: [] for cluster in range(k)}
            offset = 0
            for chunk_no, chunk in enumerate(pd.read_csv(args.raw_features, usecols=[feature], chunksize=args.chunksize), 1):
                values = pd.to_numeric(chunk[feature], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy(float)
                end = offset + len(values)
                local = labels[k, reference][offset:end]
                for cluster in range(k):
                    values_by_cluster[cluster].append(values[local == cluster])
                offset = end
                if chunk_no % 4 == 0 or offset == n:
                    print(f"K{k} {feature}: {offset:,}/{n:,}", flush=True)
            if offset != n:
                raise ValueError("Profile stream row count differs from labels")
            for cluster, parts in values_by_cluster.items():
                values = np.concatenate(parts)
                q25, median, q75 = np.quantile(values, [0.25, 0.5, 0.75])
                k_profiles.append({"k": k, "seed": reference, "cluster": cluster,
                                   "feature": feature, "n": len(values), "q25": q25,
                                   "median": median, "q75": q75})
            pd.DataFrame(k_profiles).to_csv(profile_path, index=False)
            print(f"completed K{k} profile for {feature}", flush=True)
        profiles.extend(k_profiles)
    pd.DataFrame(profiles).to_csv(args.out_dir / f"annual_exact_raw_profiles_seed{reference}.csv", index=False)
    output_manifest = {"raw_features_sha256": digest(args.raw_features), "fit_manifest": manifest,
                       "profile_method": "exact_featurewise_streaming_quantiles", "reference_seed": reference,
                       "profile_features": features}
    (args.out_dir / "annual_summary_manifest.json").write_text(json.dumps(output_manifest, indent=2), encoding="utf-8")
    print("annual summary complete", flush=True)


if __name__ == "__main__":
    main()
