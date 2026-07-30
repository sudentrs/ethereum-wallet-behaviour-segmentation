import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.preprocessing import StandardScaler


ID_COLS = {"wallet", "k_cluster"}


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def feature_columns(path: Path) -> list[str]:
    header = pd.read_csv(path, nrows=1)
    return [col for col in header.columns if col not in ID_COLS]


def matrix_from_chunk(chunk: pd.DataFrame, cols: list[str]) -> np.ndarray:
    return chunk[cols].replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy(dtype=np.float64)


def fit_scaler(feature_path: Path, cols: list[str], chunksize: int) -> StandardScaler:
    scaler = StandardScaler()
    for chunk_id, chunk in enumerate(pd.read_csv(feature_path, chunksize=chunksize), start=1):
        scaler.partial_fit(matrix_from_chunk(chunk, cols))
        print(f"  scaler chunk={chunk_id}", flush=True)
    return scaler


def reservoir_sample_features(
    feature_path: Path,
    cols: list[str],
    chunksize: int,
    sample_size: int,
    random_state: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    sample = pd.DataFrame()
    seen = 0
    for chunk_id, chunk in enumerate(pd.read_csv(feature_path, chunksize=chunksize), start=1):
        chunk = chunk[cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        seen += len(chunk)
        if sample.empty:
            sample = chunk.sample(n=min(sample_size, len(chunk)), random_state=int(rng.integers(0, 2**31 - 1)))
        else:
            combined = pd.concat([sample, chunk], ignore_index=True)
            keep = min(sample_size, len(combined))
            sample = combined.sample(n=keep, random_state=int(rng.integers(0, 2**31 - 1)))
        print(f"  sample chunk={chunk_id} rows_seen={seen:,} sample_rows={len(sample):,}", flush=True)
    return sample.reset_index(drop=True)


def fit_full_model(
    feature_path: Path,
    cols: list[str],
    scaler: StandardScaler,
    k: int,
    chunksize: int,
    batch_size: int,
    epochs: int,
    random_state: int,
) -> MiniBatchKMeans:
    model = MiniBatchKMeans(
        n_clusters=k,
        random_state=random_state,
        batch_size=batch_size,
        n_init=1,
    )
    for epoch in range(epochs):
        for chunk_id, chunk in enumerate(pd.read_csv(feature_path, chunksize=chunksize), start=1):
            model.partial_fit(scaler.transform(matrix_from_chunk(chunk, cols)))
            print(f"  k={k} epoch={epoch + 1}/{epochs} fit_chunk={chunk_id}", flush=True)
    return model


def profile_full_data(
    feature_path: Path,
    cols: list[str],
    scaler: StandardScaler,
    model: MiniBatchKMeans,
    chunksize: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    profile_parts = []
    count_parts = []
    k_cluster_parts = []
    for chunk_id, chunk in enumerate(pd.read_csv(feature_path, chunksize=chunksize), start=1):
        labels = model.predict(scaler.transform(matrix_from_chunk(chunk, cols))).astype(int)
        prof = chunk[cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        prof["cluster"] = labels
        profile_parts.append(prof.groupby("cluster")[cols].sum())
        count_parts.append(pd.Series(labels).value_counts().sort_index())
        if "k_cluster" in chunk.columns:
            cross = pd.crosstab(chunk["k_cluster"].astype(int), labels)
            k_cluster_parts.append(cross)
        print(f"  profile chunk={chunk_id}", flush=True)

    counts = pd.concat(count_parts, axis=1).fillna(0).sum(axis=1).sort_index()
    profiles = pd.concat(profile_parts).groupby(level=0).sum().sort_index().div(counts, axis=0)
    profiles.insert(0, "wallet_count", counts.astype(int))
    profiles.insert(1, "wallet_share", counts / counts.sum())
    profiles = profiles.reset_index()

    if k_cluster_parts:
        crosstab = pd.concat(k_cluster_parts).groupby(level=0).sum().sort_index()
        crosstab = crosstab.reindex(sorted(crosstab.columns), axis=1, fill_value=0)
    else:
        crosstab = pd.DataFrame()
    return profiles, crosstab


def sample_stability_metrics(x_sample: np.ndarray, k: int, seeds: list[int], batch_size: int) -> dict[str, float]:
    labels_by_seed = []
    for seed in seeds:
        model = MiniBatchKMeans(n_clusters=k, random_state=seed, batch_size=batch_size, n_init=5)
        labels_by_seed.append(model.fit_predict(x_sample))

    ari_scores = []
    nmi_scores = []
    for left, right in combinations(labels_by_seed, 2):
        ari_scores.append(adjusted_rand_score(left, right))
        nmi_scores.append(normalized_mutual_info_score(left, right))

    return {
        "seed_stability_mean_ari": float(np.mean(ari_scores)) if ari_scores else np.nan,
        "seed_stability_min_ari": float(np.min(ari_scores)) if ari_scores else np.nan,
        "seed_stability_mean_nmi": float(np.mean(nmi_scores)) if nmi_scores else np.nan,
        "seed_stability_min_nmi": float(np.min(nmi_scores)) if nmi_scores else np.nan,
    }


def cluster_entropy_normalized(counts: pd.Series) -> float:
    shares = counts[counts > 0] / counts.sum()
    if len(shares) <= 1:
        return 0.0
    return float(-(shares * np.log(shares)).sum() / np.log(len(shares)))


def label_time_domain_clusters(profiles: pd.DataFrame) -> pd.DataFrame:
    numeric = profiles.set_index("cluster")
    med = numeric.median(numeric_only=True)
    rows = []
    for cluster, row in numeric.iterrows():
        active_days = float(row.get("active_days", 0.0))
        inactive_gap = float(row.get("longest_inactive_gap", 0.0))
        switches = float(row.get("active_inactive_switches", 0.0))
        burstiness = float(row.get("tx_burstiness_cv", 0.0))
        max_ratio = float(row.get("max_to_mean_tx_ratio", 0.0))
        if active_days >= 330:
            label = "near-continuous active state"
        elif active_days >= 180:
            label = "sustained active state"
        elif active_days >= 60 and switches >= med.get("active_inactive_switches", 0):
            label = "intermittent switching state"
        elif active_days >= 60:
            label = "intermittent active state"
        elif active_days < 30 and inactive_gap >= med.get("longest_inactive_gap", 0):
            label = "sparse long-gap state"
        elif burstiness >= med.get("tx_burstiness_cv", 0) and max_ratio >= med.get("max_to_mean_tx_ratio", 0):
            label = "bursty spike state"
        else:
            label = "low-activity mixed state"
        rows.append(
            {
                "cluster": int(cluster),
                "interpretive_label": label,
                "evidence": (
                    f"mean active days={active_days:.2f}; longest inactive gap={inactive_gap:.2f}; "
                    f"switches={switches:.2f}; tx burstiness cv={burstiness:.3f}; max/mean tx={max_ratio:.3f}"
                ),
            }
        )
    return pd.DataFrame(rows)


def label_wavelength_clusters(profiles: pd.DataFrame) -> pd.DataFrame:
    numeric = profiles.set_index("cluster")
    entropy_median = numeric["tx_spectral_entropy"].median()
    rows = []
    for cluster, row in numeric.iterrows():
        components = {
            "low-frequency": float(row.get("tx_low_frequency_power_share", 0.0)),
            "medium-frequency": float(row.get("tx_medium_frequency_power_share", 0.0)),
            "high-frequency": float(row.get("tx_high_frequency_power_share", 0.0)),
            "weekly-band": float(row.get("tx_weekly_band_power_share", 0.0)),
            "monthly-band": float(row.get("tx_monthly_band_power_share", 0.0)),
        }
        dominant = max(components, key=components.get)
        period = float(row.get("tx_dominant_period_days", 0.0))
        entropy_value = float(row.get("tx_spectral_entropy", 0.0))
        concentrated = entropy_value < entropy_median
        if dominant == "low-frequency" and concentrated:
            label = "concentrated slow-cycle rhythm"
        elif dominant == "low-frequency":
            label = "distributed slow-cycle rhythm"
        elif dominant == "high-frequency" and period <= 14:
            label = "short-cycle high-frequency rhythm"
        elif dominant == "high-frequency":
            label = "distributed high-frequency rhythm"
        elif dominant == "weekly-band":
            label = "weekly-cycle rhythm"
        elif dominant == "monthly-band":
            label = "monthly-cycle rhythm"
        else:
            label = "mid-frequency mixed rhythm"
        rows.append(
            {
                "cluster": int(cluster),
                "interpretive_label": label,
                "evidence": (
                    f"dominant component={dominant}; dominant period={period:.2f} days; "
                    f"spectral entropy={entropy_value:.3f}; tx high={components['high-frequency']:.3f}; "
                    f"tx low={components['low-frequency']:.3f}"
                ),
            }
        )
    return pd.DataFrame(rows)


def write_recommendation(out_dir: Path, summaries: list[pd.DataFrame]) -> None:
    lines = ["# Temporal Signal K Selection", ""]
    combined = pd.concat(summaries, ignore_index=True)
    for signal_type, group in combined.groupby("signal_type", sort=False):
        best = group.sort_values("selection_score", ascending=False).iloc[0]
        lines.append(
            f"- {signal_type}: recommended K={int(best['k'])} "
            f"(score={best['selection_score']:.4f}, silhouette={best['silhouette_sample']:.4f}, "
            f"mean ARI={best['seed_stability_mean_ari']:.4f}, max share={best['cluster_share_max']:.4f})."
        )
    lines.extend(
        [
            "",
            "Selection score is a practical ranking, not a theorem: silhouette rewards separation, seed ARI rewards stability,",
            "and very dominant or tiny clusters are penalized. Final choice should also inspect the profile and label CSVs.",
        ]
    )
    (out_dir / "model_selection_recommendation.md").write_text("\n".join(lines), encoding="utf-8")


def evaluate_signal_type(
    signal_type: str,
    feature_path: Path,
    out_dir: Path,
    k_values: list[int],
    seeds: list[int],
    args: argparse.Namespace,
) -> pd.DataFrame:
    print(f"\n=== {signal_type} ===", flush=True)
    cols = feature_columns(feature_path)
    print(f"features={len(cols)} file={feature_path}", flush=True)
    scaler = fit_scaler(feature_path, cols, args.chunksize)
    sample_df = reservoir_sample_features(feature_path, cols, args.chunksize, args.sample_size, args.primary_seed)
    x_sample = scaler.transform(sample_df.to_numpy(dtype=np.float64))

    rows = []
    for k in k_values:
        print(f"\n--- {signal_type} k={k} ---", flush=True)
        model = fit_full_model(
            feature_path,
            cols,
            scaler,
            k,
            args.chunksize,
            args.batch_size,
            args.kmeans_epochs,
            args.primary_seed,
        )
        profiles, crosstab = profile_full_data(feature_path, cols, scaler, model, args.chunksize)
        labeler = label_time_domain_clusters if signal_type == "time_domain" else label_wavelength_clusters
        labels = labeler(profiles)

        profiles.to_csv(out_dir / f"{signal_type}_k{k}_cluster_profiles.csv", index=False)
        labels.to_csv(out_dir / f"{signal_type}_k{k}_interpretive_labels.csv", index=False)
        if not crosstab.empty:
            crosstab.to_csv(out_dir / f"{signal_type}_k{k}_vs_behavior_k_cluster_crosstab.csv")

        sample_labels = model.predict(x_sample)
        unique_sample_labels = np.unique(sample_labels)
        silhouette = np.nan
        if 1 < len(unique_sample_labels) < len(sample_labels):
            silhouette_n = min(args.silhouette_size, len(sample_labels))
            silhouette = float(
                silhouette_score(
                    x_sample,
                    sample_labels,
                    sample_size=silhouette_n,
                    random_state=args.primary_seed,
                )
            )

        counts = profiles.set_index("cluster")["wallet_count"].astype(int)
        shares = counts / counts.sum()
        stability = sample_stability_metrics(x_sample, k, seeds, args.batch_size)
        imbalance_penalty = max(0.0, float(shares.max()) - 0.75) + max(0.0, 0.01 - float(shares.min()))
        selection_score = float(np.nan_to_num(silhouette, nan=-1.0)) + 0.25 * float(
            np.nan_to_num(stability["seed_stability_mean_ari"], nan=0.0)
        ) - imbalance_penalty

        row = {
            "signal_type": signal_type,
            "k": k,
            "wallets": int(counts.sum()),
            "feature_count": len(cols),
            "sample_size": int(len(sample_df)),
            "silhouette_size": int(min(args.silhouette_size, len(sample_df))),
            "silhouette_sample": silhouette,
            "cluster_share_min": float(shares.min()),
            "cluster_share_max": float(shares.max()),
            "cluster_share_entropy_norm": cluster_entropy_normalized(counts),
            "selection_score": selection_score,
            "primary_seed": args.primary_seed,
            "kmeans_epochs": args.kmeans_epochs,
            "chunksize": args.chunksize,
            "batch_size": args.batch_size,
        }
        row.update(stability)
        rows.append(row)
        print(
            f"  summary k={k}: silhouette={silhouette:.4f} "
            f"mean_ari={stability['seed_stability_mean_ari']:.4f} "
            f"min_share={shares.min():.4f} max_share={shares.max():.4f} "
            f"score={selection_score:.4f}",
            flush=True,
        )

    summary = pd.DataFrame(rows)
    summary.to_csv(out_dir / f"{signal_type}_model_selection_summary.csv", index=False)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select K for full EOA time-domain and wavelength temporal signal clustering without rebuilding features."
    )
    parser.add_argument("--base-dir", default="results/full_eoa_temporal_signal_streaming_k5")
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--k-values", default="3,4,5,6,7,8")
    parser.add_argument("--seeds", default="101,202,303")
    parser.add_argument("--primary-seed", type=int, default=492)
    parser.add_argument("--chunksize", type=int, default=250000)
    parser.add_argument("--sample-size", type=int, default=100000)
    parser.add_argument("--silhouette-size", type=int, default=10000)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--kmeans-epochs", type=int, default=3)
    parser.add_argument("--only", choices=["both", "time_domain", "wavelength"], default="both")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    out_dir = Path(args.out_dir) if args.out_dir else base_dir / "model_selection"
    out_dir.mkdir(parents=True, exist_ok=True)

    k_values = parse_int_list(args.k_values)
    seeds = parse_int_list(args.seeds)
    summaries = []
    jobs = []
    if args.only in {"both", "time_domain"}:
        jobs.append(("time_domain", base_dir / "full_eoa_time_domain_features_raw.csv"))
    if args.only in {"both", "wavelength"}:
        jobs.append(("wavelength", base_dir / "full_eoa_wavelength_features_raw.csv"))

    for signal_type, feature_path in jobs:
        if not feature_path.exists():
            raise FileNotFoundError(f"Missing feature file: {feature_path}")
        summaries.append(evaluate_signal_type(signal_type, feature_path, out_dir, k_values, seeds, args))

    pd.concat(summaries, ignore_index=True).to_csv(out_dir / "temporal_signal_model_selection_summary.csv", index=False)
    write_recommendation(out_dir, summaries)
    print(f"\nWrote model selection outputs to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
