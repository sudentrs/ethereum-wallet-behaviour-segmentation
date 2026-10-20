"""Local annual sensitivity pilot; never replaces published cohort files.

Freeze the original scaler and feature representation. Reconstruct absent
estimators, measure archival agreement, then compare paired MiniBatchKMeans
fits with identical initial centers. Mini-batch schedules still depend on n.
"""
import gc
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/interim/verified_eoa_restoration_pilot"


def align(reference, candidate, k):
    table = np.bincount(reference.astype(np.int64) * k + candidate,
                        minlength=k*k).reshape(k, k)
    rows, cols = linear_sum_assignment(-table)
    mapping = np.empty(k, dtype=int)
    mapping[cols] = rows
    return mapping, mapping[candidate]


def compare(reference, candidate, k):
    mapping, aligned = align(reference, candidate, k)
    return mapping, aligned, {"ari": adjusted_rand_score(reference, candidate),
                             "nmi": normalized_mutual_info_score(reference, candidate),
                             "changed_shared_wallets": int(np.count_nonzero(reference != aligned)),
                             "agreement": float(np.mean(reference == aligned))}


def transform(raw, stats):
    result = np.empty((len(raw), len(stats)), dtype=np.float32)
    for j, meta in enumerate(stats.itertuples(index=False)):
        values = pd.to_numeric(raw[meta.feature], errors="coerce").replace(
            [np.inf, -np.inf], np.nan).fillna(0).to_numpy(dtype=float)
        if meta.transform_type == "log1p":
            if np.any(values < 0):
                raise ValueError(f"Negative input for log1p feature {meta.feature}")
            values = np.log1p(values)
        elif meta.transform_type == "signed_log1p":
            values = np.sign(values) * np.log1p(np.abs(values))
        elif meta.transform_type != "raw":
            raise ValueError(f"Unknown transformation {meta.transform_type}")
        denominator = meta.iqr if np.isfinite(meta.iqr) and meta.iqr != 0 else 1.
        result[:, j] = (values - meta.median) / denominator
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite transformed features")
    return result


def model(k, seed, init="k-means++", n_init=10):
    return MiniBatchKMeans(n_clusters=k, random_state=seed, init=init,
                          n_init=n_init, batch_size=8192, max_iter=200)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = pd.read_csv(ROOT / "data/interim/excluded_code_type_audit/historical_origination_audit.csv")
    evidence = evidence.loc[evidence.status.eq("verified_top_level_sender_in_2022")].copy()
    if len(evidence) != 33 or evidence.address.duplicated().any():
        raise ValueError("Expected 33 independently evidenced distinct addresses")
    evidence["wallet"] = evidence.address.str.removeprefix("0x")
    evidence.to_csv(OUT / "restoration_manifest.csv", index=False)
    stats_path = ROOT / "data/processed/wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled_scaling_stats.csv"
    stats = pd.read_csv(stats_path)
    features = stats.feature.tolist()
    scaled_path = ROOT / "results/eoa_only_kmeans6/wallet_eoa_only_kmeans6_features_robust_scaled.csv"
    print("Loading original full-cohort scaled features...", flush=True)
    frame = pd.read_csv(scaled_path, usecols=["wallet", *features],
                        dtype={"wallet": str, **{c: np.float32 for c in features}})
    wallets = pd.Index(frame.pop("wallet"))
    X = np.ascontiguousarray(frame[features].to_numpy(), dtype=np.float32)
    del frame
    gc.collect()
    if wallets.has_duplicates or set(evidence.wallet) & set(wallets):
        raise ValueError("Duplicate baseline wallets or restoration overlap")
    print(f"Baseline: {len(X):,} wallets, {len(features)} features", flush=True)
    check_wallets = wallets[:64].tolist()
    wanted = set(check_wallets) | set(evidence.wallet)
    parts = []
    raw_path = ROOT / "data/processed/wallet_kmeans6_expanded_daily_features.csv"
    for i, chunk in enumerate(pd.read_csv(raw_path, usecols=["wallet", *features],
                                          dtype={"wallet": str}, chunksize=100000), 1):
        parts.append(chunk.loc[chunk.wallet.isin(wanted)].copy())
        if i % 5 == 0:
            print(f"Reading raw features: {i * 100000:,} rows scanned", flush=True)
    raw = pd.concat(parts).set_index("wallet")
    if raw.index.has_duplicates or set(raw.index) != wanted:
        raise ValueError("Missing or duplicate raw feature rows")
    check = transform(raw.loc[check_wallets], stats)
    error = float(np.max(np.abs(check - X[:64])))
    if not np.allclose(check, X[:64], atol=2e-5, rtol=2e-5):
        raise ValueError(f"Saved scaler does not reproduce baseline values: max error {error}")
    added_wallets = evidence.wallet.tolist()
    added_raw = raw.loc[added_wallets]
    added = transform(added_raw, stats)
    added_raw.to_csv(OUT / "restored_raw_features.csv")
    pd.DataFrame(added, index=added_wallets, columns=features).rename_axis("wallet").to_csv(OUT / "restored_scaled_features.csv")
    expanded = np.concatenate([X, added])
    seeds = [492, 493, 494]
    metadata = {"baseline_wallets": len(X), "added_wallets": len(added),
                "feature_count": len(features), "seeds": seeds, "sklearn_version": sklearn.__version__,
                "batch_size": 8192, "max_iter": 200, "reference_n_init": 10,
                "paired_n_init": 1, "scaler_max_check_error": error,
                "scaler_sha256": hashlib.sha256(stats_path.read_bytes()).hexdigest(),
                "representation": "Existing legacy features, including unresolved token denomination; no economic volume inference.",
                "design": "Same initial reference centers per pair and same seed. n changes mini-batch draws; pairs include schedule sensitivity. Frozen scaler.",
                "frozen_model_caveat": "Original estimators absent; reconstructed estimator agreement with archived labels reported explicitly."}
    (OUT / "settings.json").write_text(json.dumps(metadata, indent=2))
    agreement_rows, fixed_rows, paired_rows, size_rows, profile_rows, variation_rows = [], [], [], [], [], []
    for k in (4, 5, 6):
        print(f"K{k}: reconstructing baseline estimator (seed 492, n_init 10)...", flush=True)
        archive = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv", dtype={"wallet": str})
        archive = archive.set_index("wallet").reindex(wallets)
        if archive.cluster.isna().any():
            raise ValueError("Archived labels do not cover baseline wallets")
        y_archive = archive.cluster.to_numpy(dtype=int)
        reference = model(k, 492).fit(X)
        y_reference = reference.predict(X)
        map_archive, _, metrics = compare(y_archive, y_reference, k)
        agreement_rows.append({"k": k, **metrics})
        pd.DataFrame(agreement_rows).to_csv(OUT / "reconstruction_agreement.csv", index=False)
        joblib.dump(reference, OUT / f"reconstructed_k{k}.joblib")
        np.save(OUT / f"reconstructed_k{k}_centers.npy", reference.cluster_centers_)
        for wallet, label in zip(added_wallets, reference.predict(added)):
            fixed_rows.append({"k": k, "wallet": wallet, "reconstructed_cluster": int(label),
                               "archival_aligned_cluster": int(map_archive[label])})
        pd.DataFrame(fixed_rows).to_csv(OUT / "fixed_model_added_assignments.csv", index=False)
        by_seed = {}
        for seed in seeds:
            print(f"K{k} seed {seed}: paired baseline/expanded fits...", flush=True)
            init = reference.cluster_centers_.copy()
            baseline_model = model(k, seed, init.copy(), 1).fit(X)
            augmented_model = model(k, seed, init.copy(), 1).fit(expanded)
            before = baseline_model.predict(X)
            after = augmented_model.predict(X)
            mapping, aligned, metrics = compare(before, after, k)
            by_seed[seed] = before
            paired_rows.append({"k": k, "seed": seed, **metrics,
                                "baseline_inertia_on_shared": float(baseline_model.inertia_),
                                "expanded_inertia_on_shared": float(-augmented_model.score(X))})
            labels_added = mapping[augmented_model.predict(added)]
            a_counts = np.bincount(before, minlength=k)
            b_counts = np.bincount(aligned, minlength=k) + np.bincount(labels_added, minlength=k)
            for cluster in range(k):
                size_rows.append({"k": k, "seed": seed, "cluster": cluster,
                                  "baseline_count": int(a_counts[cluster]), "expanded_count": int(b_counts[cluster]),
                                  "baseline_share": a_counts[cluster] / len(X),
                                  "expanded_share": b_counts[cluster] / len(expanded)})
                old_profile = np.median(X[before == cluster], axis=0)
                new_profile = np.median(expanded[np.concatenate([aligned, labels_added]) == cluster], axis=0)
                for j, feature in enumerate(features):
                    profile_rows.append({"k": k, "seed": seed, "cluster": cluster, "feature": feature,
                                         "baseline_median": float(old_profile[j]), "expanded_median": float(new_profile[j]),
                                         "median_delta": float(new_profile[j] - old_profile[j])})
            pd.DataFrame(paired_rows).to_csv(OUT / "paired_refit_summary.csv", index=False)
            pd.DataFrame(size_rows).to_csv(OUT / "paired_cluster_sizes.csv", index=False)
            pd.DataFrame(profile_rows).to_csv(OUT / "paired_profile_drift.csv", index=False)
            joblib.dump(augmented_model, OUT / f"expanded_k{k}_seed{seed}.joblib")
            np.save(OUT / f"baseline_labels_k{k}_seed{seed}.npy", before)
            np.save(OUT / f"expanded_shared_labels_k{k}_seed{seed}.npy", aligned)
            print(f"  ARI={metrics['ari']:.6f}; changed shared wallets={metrics['changed_shared_wallets']:,}", flush=True)
        for seed_a, seed_b in combinations(seeds, 2):
            _, _, metrics = compare(by_seed[seed_a], by_seed[seed_b], k)
            variation_rows.append({"k": k, "seed_a": seed_a, "seed_b": seed_b, **metrics})
        pd.DataFrame(variation_rows).to_csv(OUT / "baseline_seed_variation.csv", index=False)
        del reference, baseline_model, augmented_model, archive, by_seed
        gc.collect()
    activity = pd.read_csv(ROOT / "data/processed/wallet_kmeans6_expanded_daily_features.csv",
                           usecols=["wallet", "total_tx", "active_days_observed"], dtype={"wallet": str})
    original_activity = activity.loc[activity.wallet.isin(wallets)]
    restored_activity = activity.loc[activity.wallet.isin(added_wallets)]
    summary = {"added_wallet_count": len(added), "baseline_wallet_count": len(X),
               "added_wallet_share_of_expanded": len(added) / len(expanded),
               "baseline_wallet_transfer_count": float(original_activity.total_tx.sum()),
               "added_wallet_transfer_count": float(restored_activity.total_tx.sum()),
               "added_wallet_days": int(restored_activity.active_days_observed.sum())}
    (OUT / "activity_summary.json").write_text(json.dumps(summary, indent=2))
    pd.Series(wallets, name="wallet").to_csv(OUT / "baseline_wallet_order.csv", index=False)
    (OUT / "ANNUAL_COMPLETE").write_text("Annual pilot complete; downstream analyses reported separately.\n")
    print(f"Annual pilot complete: {OUT}", flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
