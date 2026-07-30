import argparse
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler


ID_COLS = {"wallet", "k_cluster"}


def clean_wallet(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def safe_numeric(series: pd.Series) -> np.ndarray:
    return pd.to_numeric(series, errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)


def load_label_map(path: Path, wallet_col: str, cluster_col: str) -> dict[str, int]:
    labels = pd.read_csv(path, usecols=[wallet_col, cluster_col], dtype={wallet_col: str})
    labels = labels.rename(columns={wallet_col: "wallet", cluster_col: "k_cluster"})
    labels["wallet"] = clean_wallet(labels["wallet"])
    labels["k_cluster"] = pd.to_numeric(labels["k_cluster"], errors="coerce").fillna(-1).astype(int)
    labels = labels.drop_duplicates("wallet")
    return dict(zip(labels["wallet"], labels["k_cluster"]))


def day_lookup() -> dict[str, int]:
    dates = pd.date_range("2022-01-01", "2022-12-31", freq="D")
    return {str(day.date()): i for i, day in enumerate(dates)}


def longest_run(mask: np.ndarray, value: bool) -> int:
    best = 0
    current = 0
    for item in mask:
        if bool(item) == value:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def count_switches(mask: np.ndarray) -> int:
    if len(mask) < 2:
        return 0
    return int(np.sum(mask[1:] != mask[:-1]))


def signal_from_wallet_rows(rows: pd.DataFrame, lookup: dict[str, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    tx = np.zeros(365, dtype=np.float64)
    total_flow = np.zeros(365, dtype=np.float64)
    net_flow = np.zeros(365, dtype=np.float64)
    day_idx = rows["date"].astype("string").str.slice(0, 10).map(lookup).fillna(-1).to_numpy(dtype=np.int16)
    valid = day_idx >= 0
    if not valid.any():
        return tx, total_flow, net_flow

    rows = rows.iloc[np.flatnonzero(valid)]
    day_idx = day_idx[valid]
    total_in = safe_numeric(rows["total_in"])
    total_out = safe_numeric(rows["total_out"])
    tx_count = safe_numeric(rows["tx_count"])
    flow = total_in + total_out
    net = total_in - total_out

    np.add.at(tx, day_idx, tx_count)
    np.add.at(total_flow, day_idx, flow)
    np.add.at(net_flow, day_idx, net)
    return tx, total_flow, net_flow


def time_domain_features(tx: np.ndarray, total_flow: np.ndarray, net_flow: np.ndarray) -> dict[str, float]:
    flow_log = np.log1p(np.maximum(total_flow, 0))
    active = tx > 0
    active_days = int(active.sum())
    tx_sum = float(tx.sum())
    flow_sum = float(total_flow.sum())
    mean_tx_active = float(tx[active].mean()) if active_days else 0.0
    std_tx_active = float(tx[active].std()) if active_days else 0.0
    mean_flow_active = float(flow_log[active].mean()) if active_days else 0.0
    std_flow_active = float(flow_log[active].std()) if active_days else 0.0
    weekly_tx = pd.Series(tx).rolling(7, min_periods=1).sum().to_numpy()
    weekly_change = np.abs(np.diff(weekly_tx))
    max_weekly_change = float(weekly_change.max()) if len(weekly_change) else 0.0
    return {
        "active_days": active_days,
        "active_ratio": active_days / 365,
        "total_tx": tx_sum,
        "log_total_flow_sum": float(flow_log.sum()),
        "mean_tx_active_day": mean_tx_active,
        "tx_burstiness_cv": std_tx_active / mean_tx_active if mean_tx_active else 0.0,
        "max_to_mean_tx_ratio": float(tx.max() / mean_tx_active) if mean_tx_active else 0.0,
        "log_flow_burstiness_cv": std_flow_active / mean_flow_active if mean_flow_active else 0.0,
        "net_direction_bias": float(net_flow.sum() / flow_sum) if flow_sum else 0.0,
        "longest_active_streak": longest_run(active, True),
        "longest_inactive_gap": longest_run(active, False),
        "active_inactive_switches": count_switches(active),
        "max_weekly_tx_change": max_weekly_change,
        "max_weekly_tx_change_ratio": max_weekly_change / tx_sum if tx_sum else 0.0,
    }


def spectral_features(signal: np.ndarray, prefix: str) -> dict[str, float]:
    transformed = np.log1p(np.maximum(signal, 0))
    centered = transformed - transformed.mean()
    power = np.abs(np.fft.rfft(centered)) ** 2
    freqs = np.fft.rfftfreq(len(signal), d=1.0)
    power_no_dc = power[1:]
    freqs_no_dc = freqs[1:]
    total_power = float(power_no_dc.sum())
    total_power_safe = total_power if total_power else 1.0
    norm_power = power_no_dc / total_power_safe
    dominant_idx = int(np.argmax(power_no_dc)) if len(power_no_dc) else 0
    dominant_freq = float(freqs_no_dc[dominant_idx]) if len(freqs_no_dc) else 0.0
    dominant_period = 1.0 / dominant_freq if dominant_freq > 0 else 0.0
    peak_share = float(power_no_dc[dominant_idx] / total_power_safe) if len(power_no_dc) else 0.0

    def band_share(low_freq: float, high_freq: float) -> float:
        mask = (freqs_no_dc >= low_freq) & (freqs_no_dc < high_freq)
        if not mask.any():
            return 0.0
        return float(norm_power[mask].sum())

    return {
        f"{prefix}_spectral_total_power": float(np.log1p(total_power)),
        f"{prefix}_dominant_frequency": dominant_freq,
        f"{prefix}_dominant_period_days": float(dominant_period),
        f"{prefix}_peak_power_share": peak_share,
        f"{prefix}_low_frequency_power_share": band_share(0.0, 1 / 60),
        f"{prefix}_medium_frequency_power_share": band_share(1 / 60, 1 / 14),
        f"{prefix}_high_frequency_power_share": band_share(1 / 14, 0.5 + 1e-9),
        f"{prefix}_weekly_band_power_share": band_share(1 / 8, 1 / 6),
        f"{prefix}_monthly_band_power_share": band_share(1 / 35, 1 / 25),
        f"{prefix}_spectral_entropy": float(np.nan_to_num(entropy(norm_power, base=2), nan=0.0)),
    }


def append_rows(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan).fillna(0.0).to_csv(
        path,
        mode="a",
        header=not path.exists(),
        index=False,
    )


def process_wallet(wallet: str, rows: pd.DataFrame, labels: dict[str, int], lookup: dict[str, int]) -> tuple[dict, dict] | None:
    k_cluster = labels.get(wallet)
    if k_cluster is None:
        return None
    tx, total_flow, net_flow = signal_from_wallet_rows(rows, lookup)
    base = {"wallet": wallet, "k_cluster": k_cluster}
    time_row = dict(base)
    time_row.update(time_domain_features(tx, total_flow, net_flow))
    wave_row = dict(base)
    wave_row.update(spectral_features(tx, "tx"))
    wave_row.update(spectral_features(total_flow, "flow"))
    return time_row, wave_row


def extract_features(args: argparse.Namespace, out_dir: Path) -> tuple[Path, Path]:
    labels = load_label_map(Path(args.wallet_file), args.wallet_col, args.cluster_col)
    lookup = day_lookup()
    daily_path = Path(args.daily_file)
    time_path = out_dir / "full_eoa_time_domain_features_raw.csv"
    wave_path = out_dir / "full_eoa_wavelength_features_raw.csv"
    if args.rebuild_features:
        for path in [time_path, wave_path]:
            if path.exists():
                path.unlink()
    if time_path.exists() and wave_path.exists() and not args.rebuild_features:
        print("Raw feature files already exist; use --rebuild-features to regenerate.", flush=True)
        return time_path, wave_path

    partition_dir = out_dir / "daily_wallet_partitions"
    partition_daily_file(daily_path, labels, partition_dir, args)

    time_buffer: list[dict] = []
    wave_buffer: list[dict] = []
    processed = 0
    for bucket in range(args.partition_count):
        bucket_path = partition_dir / f"wallet_daily_bucket_{bucket:04d}.csv"
        if not bucket_path.exists():
            continue
        bucket_df = pd.read_csv(bucket_path, dtype={"wallet": str})
        bucket_df["wallet"] = clean_wallet(bucket_df["wallet"])
        for wallet, rows in bucket_df.groupby("wallet", sort=False):
            result = process_wallet(wallet, rows, labels, lookup)
            if result is None:
                continue
            time_row, wave_row = result
            time_buffer.append(time_row)
            wave_buffer.append(wave_row)
            processed += 1
            if len(time_buffer) >= args.write_buffer_wallets:
                append_rows(time_buffer, time_path)
                append_rows(wave_buffer, wave_path)
                time_buffer.clear()
                wave_buffer.clear()

        print(f"processed bucket={bucket + 1}/{args.partition_count} processed_eoa_wallets={processed:,}", flush=True)

    append_rows(time_buffer, time_path)
    append_rows(wave_buffer, wave_path)
    print(f"feature extraction complete processed_eoa_wallets={processed:,}", flush=True)
    return time_path, wave_path


def partition_daily_file(
    daily_path: Path,
    labels: dict[str, int],
    partition_dir: Path,
    args: argparse.Namespace,
) -> None:
    manifest = partition_dir / "_SUCCESS"
    if manifest.exists() and not args.rebuild_partitions:
        print(f"Using existing wallet hash partitions: {partition_dir}", flush=True)
        return
    if partition_dir.exists():
        shutil.rmtree(partition_dir)
    partition_dir.mkdir(parents=True, exist_ok=True)

    usecols = ["wallet", "date", "total_in", "total_out", "tx_count"]
    label_wallets = set(labels)
    total_kept = 0
    for chunk_id, chunk in enumerate(pd.read_csv(daily_path, usecols=usecols, dtype={"wallet": str}, chunksize=args.chunksize), start=1):
        chunk["wallet"] = clean_wallet(chunk["wallet"])
        chunk = chunk[chunk["wallet"].isin(label_wallets)].copy()
        if chunk.empty:
            print(f"partition chunk={chunk_id:,} kept=0 total_kept={total_kept:,}", flush=True)
            continue
        buckets = pd.util.hash_pandas_object(chunk["wallet"], index=False).to_numpy(dtype=np.uint64) % args.partition_count
        chunk["_bucket"] = buckets.astype(np.int32)
        total_kept += len(chunk)
        for bucket, sub in chunk.groupby("_bucket", sort=False):
            path = partition_dir / f"wallet_daily_bucket_{int(bucket):04d}.csv"
            sub = sub.drop(columns=["_bucket"])
            sub.to_csv(path, mode="a", header=not path.exists(), index=False)
        print(f"partition chunk={chunk_id:,} kept={len(chunk):,} total_kept={total_kept:,}", flush=True)
    manifest.write_text(f"partition_count={args.partition_count}\nrows={total_kept}\n", encoding="utf-8")


def feature_columns(path: Path) -> list[str]:
    header = pd.read_csv(path, nrows=1)
    return [col for col in header.columns if col not in ID_COLS and pd.api.types.is_numeric_dtype(header[col])]


def matrix_from_chunk(chunk: pd.DataFrame, cols: list[str]) -> np.ndarray:
    return chunk[cols].replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy(dtype=np.float64)


def cluster_feature_file(
    feature_path: Path,
    out_path: Path,
    label_col: str,
    k: int,
    chunksize: int,
    batch_size: int,
    epochs: int,
    random_state: int,
) -> pd.DataFrame:
    cols = feature_columns(feature_path)
    scaler = StandardScaler()
    for chunk in pd.read_csv(feature_path, chunksize=chunksize):
        scaler.partial_fit(matrix_from_chunk(chunk, cols))

    model = MiniBatchKMeans(
        n_clusters=k,
        random_state=random_state,
        batch_size=batch_size,
        n_init=1,
    )
    for epoch in range(epochs):
        print(f"fit {label_col} epoch {epoch + 1}/{epochs}", flush=True)
        for chunk in pd.read_csv(feature_path, chunksize=chunksize):
            model.partial_fit(scaler.transform(matrix_from_chunk(chunk, cols)))

    if out_path.exists():
        out_path.unlink()
    profile_parts = []
    count_parts = []
    for chunk in pd.read_csv(feature_path, chunksize=chunksize):
        labels = model.predict(scaler.transform(matrix_from_chunk(chunk, cols))).astype(int)
        assign = chunk[["wallet", "k_cluster"]].copy()
        assign[label_col] = labels
        append_rows(assign.to_dict("records"), out_path)
        prof = chunk[cols].copy()
        prof[label_col] = labels
        profile_parts.append(prof.groupby(label_col)[cols].sum())
        count_parts.append(pd.Series(labels).value_counts().sort_index())

    counts = pd.concat(count_parts, axis=1).fillna(0).sum(axis=1).sort_index()
    profiles = pd.concat(profile_parts).groupby(level=0).sum().sort_index().div(counts, axis=0)
    profiles = profiles.reset_index().rename(columns={label_col: "cluster"})
    return profiles


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
                "time_domain_cluster": int(cluster),
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
                "wavelength_cluster": int(cluster),
                "interpretive_label": label,
                "evidence": (
                    f"dominant component={dominant}; dominant period={period:.2f} days; "
                    f"spectral entropy={entropy_value:.3f}; tx high={components['high-frequency']:.3f}; "
                    f"tx low={components['low-frequency']:.3f}"
                ),
            }
        )
    return pd.DataFrame(rows)


def build_assignment_summaries(out_dir: Path, time_assignments: Path, wave_assignments: Path) -> None:
    time = pd.read_csv(time_assignments)
    wave = pd.read_csv(wave_assignments, usecols=["wallet", "wavelength_cluster"])
    assignments = time.merge(wave, on="wallet", how="inner")
    assignments.to_csv(out_dir / "full_eoa_temporal_signal_assignments.csv", index=False)
    for col in ["time_domain_cluster", "wavelength_cluster"]:
        sizes = assignments[col].value_counts().sort_index().reset_index()
        sizes.columns = [col, "wallet_count"]
        sizes["wallet_share"] = sizes["wallet_count"] / sizes["wallet_count"].sum()
        sizes.to_csv(out_dir / f"{col}_sizes.csv", index=False)
    pd.crosstab(assignments["k_cluster"], assignments["time_domain_cluster"]).to_csv(out_dir / "k_cluster_vs_time_domain_cluster_crosstab.csv")
    pd.crosstab(assignments["k_cluster"], assignments["wavelength_cluster"]).to_csv(out_dir / "k_cluster_vs_wavelength_cluster_crosstab.csv")


def write_report(out_dir: Path, args: argparse.Namespace) -> None:
    text = f"""# Full EOA Temporal Signal Streaming Pack

This pack applies the same daily-signal feature logic as the 10k temporal signal analysis to the full EOA-only wallet dataset.

## RAM Safety

- The script reads `wallet_daily_2022.csv` in chunks.
- It does not assume the daily file is sorted by wallet.
- It first hash-partitions daily rows by wallet into `{args.partition_count}` disk buckets.
- Each wallet is guaranteed to stay in one bucket, so full-year signals are complete inside a bucket.
- It computes wallet-level 365-day transaction, total-flow, and net-flow signals bucket by bucket.
- Clustering uses `StandardScaler.partial_fit` and `MiniBatchKMeans.partial_fit`.

## Outputs

- `full_eoa_time_domain_features_raw.csv`
- `full_eoa_wavelength_features_raw.csv`
- `full_eoa_time_domain_assignments.csv`
- `full_eoa_wavelength_assignments.csv`
- `full_eoa_temporal_signal_assignments.csv`
- `time_domain_cluster_profiles.csv`
- `wavelength_cluster_profiles.csv`
- `time_domain_cluster_interpretive_labels.csv`
- `wavelength_cluster_interpretive_labels.csv`

## Parameters

- k signal clusters: `{args.k_signal}`
- kmeans epochs: `{args.kmeans_epochs}`
- chunk size: `{args.chunksize}`
"""
    (out_dir / "full_eoa_temporal_signal_streaming_report.md").write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Streaming full EOA temporal signal analysis using the same 10k feature logic.")
    parser.add_argument("--wallet-file", default="results/eoa_only_kmeans6/wallet_eoa_only_kmeans_clusters.csv")
    parser.add_argument("--wallet-col", default="wallet")
    parser.add_argument("--cluster-col", default="cluster")
    parser.add_argument("--daily-file", default="data/processed/wallet_daily_2022.csv")
    parser.add_argument("--out-dir", default="results/full_eoa_temporal_signal_streaming")
    parser.add_argument("--chunksize", type=int, default=750000)
    parser.add_argument("--partition-count", type=int, default=512)
    parser.add_argument("--write-buffer-wallets", type=int, default=10000)
    parser.add_argument("--features-only", action="store_true")
    parser.add_argument("--rebuild-features", action="store_true")
    parser.add_argument("--rebuild-partitions", action="store_true")
    parser.add_argument("--k-signal", type=int, default=5)
    parser.add_argument("--kmeans-chunksize", type=int, default=250000)
    parser.add_argument("--kmeans-batch-size", type=int, default=8192)
    parser.add_argument("--kmeans-epochs", type=int, default=3)
    parser.add_argument("--random-state", type=int, default=492)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    time_features, wave_features = extract_features(args, out_dir)
    if args.features_only:
        write_report(out_dir, args)
        return

    time_profiles = cluster_feature_file(
        time_features,
        out_dir / "full_eoa_time_domain_assignments.csv",
        "time_domain_cluster",
        args.k_signal,
        args.kmeans_chunksize,
        args.kmeans_batch_size,
        args.kmeans_epochs,
        args.random_state,
    )
    wave_profiles = cluster_feature_file(
        wave_features,
        out_dir / "full_eoa_wavelength_assignments.csv",
        "wavelength_cluster",
        args.k_signal,
        args.kmeans_chunksize,
        args.kmeans_batch_size,
        args.kmeans_epochs,
        args.random_state,
    )
    time_profiles.to_csv(out_dir / "time_domain_cluster_profiles.csv", index=False)
    wave_profiles.to_csv(out_dir / "wavelength_cluster_profiles.csv", index=False)
    label_time_domain_clusters(time_profiles).to_csv(out_dir / "time_domain_cluster_interpretive_labels.csv", index=False)
    label_wavelength_clusters(wave_profiles).to_csv(out_dir / "wavelength_cluster_interpretive_labels.csv", index=False)
    build_assignment_summaries(
        out_dir,
        out_dir / "full_eoa_time_domain_assignments.csv",
        out_dir / "full_eoa_wavelength_assignments.csv",
    )
    write_report(out_dir, args)


if __name__ == "__main__":
    main()
