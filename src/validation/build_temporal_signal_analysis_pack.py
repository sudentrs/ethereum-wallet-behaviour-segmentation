import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.preprocessing import StandardScaler


MONTHS_2022 = [
    "202201",
    "202202",
    "202203",
    "202204",
    "202205",
    "202206",
    "202207",
    "202208",
    "202209",
    "202210",
    "202211",
    "202212",
]


def clean_wallet(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def load_stratified_sample(labels_path: Path, sample_per_cluster: int, random_state: int) -> pd.DataFrame:
    labels = pd.read_csv(labels_path, dtype={"wallet": str})
    labels["wallet"] = clean_wallet(labels["wallet"])
    labels["cluster"] = labels["cluster"].astype(int)
    rng = np.random.default_rng(random_state)
    parts = []
    for cluster, sub in labels.groupby("cluster"):
        n = min(sample_per_cluster, len(sub))
        chosen = rng.choice(sub.index.to_numpy(), size=n, replace=False)
        parts.append(labels.loc[chosen, ["wallet", "cluster"]])
    sample = pd.concat(parts, ignore_index=True)
    return sample.sort_values(["cluster", "wallet"]).reset_index(drop=True)


def build_daily_signal_matrices(
    sample: pd.DataFrame,
    daily_data_dir: Path,
    chunksize: int,
) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray]:
    dates = pd.date_range("2022-01-01", "2022-12-31", freq="D")
    day_lookup = {str(day.date()): i for i, day in enumerate(dates)}
    wallets = sample["wallet"].to_numpy()
    wallet_to_idx = {wallet: i for i, wallet in enumerate(wallets)}
    wallet_set = set(wallets)
    n_wallets = len(wallets)
    n_days = len(dates)

    tx = np.zeros((n_wallets, n_days), dtype=np.float64)
    total_flow = np.zeros((n_wallets, n_days), dtype=np.float64)
    net_flow = np.zeros((n_wallets, n_days), dtype=np.float64)

    usecols = ["wallet", "date", "total_in", "total_out", "tx_count"]
    for month in MONTHS_2022:
        path = daily_data_dir / f"wallet_daily_clean_{month}.csv"
        if not path.exists():
            path = daily_data_dir / f"wallet_daily_{month}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing daily file for {month}: {path}")

        print(f"reading month={month} file={path}", flush=True)
        for chunk in pd.read_csv(path, usecols=usecols, dtype={"wallet": str}, chunksize=chunksize):
            chunk["wallet"] = clean_wallet(chunk["wallet"])
            chunk = chunk[chunk["wallet"].isin(wallet_set)].copy()
            if chunk.empty:
                continue

            row_idx = chunk["wallet"].map(wallet_to_idx).to_numpy(dtype=np.int64)
            day_idx = chunk["date"].map(day_lookup).to_numpy(dtype=np.int64)
            total_in = pd.to_numeric(chunk["total_in"], errors="coerce").fillna(0).to_numpy(dtype=np.float64)
            total_out = pd.to_numeric(chunk["total_out"], errors="coerce").fillna(0).to_numpy(dtype=np.float64)
            tx_count = pd.to_numeric(chunk["tx_count"], errors="coerce").fillna(0).to_numpy(dtype=np.float64)
            flow = total_in + total_out
            net = total_in - total_out

            np.add.at(tx, (row_idx, day_idx), tx_count)
            np.add.at(total_flow, (row_idx, day_idx), flow)
            np.add.at(net_flow, (row_idx, day_idx), net)

    return dates, tx, total_flow, net_flow


def sanitize_signal_matrix(matrix: np.ndarray) -> np.ndarray:
    matrix = matrix.astype(np.float64, copy=True)
    finite = matrix[np.isfinite(matrix)]
    cap = float(np.nanmax(finite)) if finite.size else 0.0
    return np.nan_to_num(matrix, nan=0.0, posinf=cap, neginf=-cap)


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


def extract_time_domain_features(tx: np.ndarray, total_flow: np.ndarray, net_flow: np.ndarray) -> pd.DataFrame:
    tx = sanitize_signal_matrix(tx)
    total_flow = sanitize_signal_matrix(total_flow)
    net_flow = sanitize_signal_matrix(net_flow)
    rows = []
    for i in range(tx.shape[0]):
        tx_i = tx[i]
        flow_i = total_flow[i]
        net_i = net_flow[i]
        flow_log_i = np.log1p(np.maximum(flow_i, 0))
        active = tx_i > 0
        active_days = int(active.sum())
        active_ratio = active_days / len(active)
        tx_sum = float(tx_i.sum())
        flow_sum = float(flow_i.sum())
        flow_log_sum = float(flow_log_i.sum())
        mean_tx_active = float(tx_i[active].mean()) if active_days else 0.0
        std_tx_active = float(tx_i[active].std()) if active_days else 0.0
        burstiness = std_tx_active / mean_tx_active if mean_tx_active else 0.0
        max_to_mean_tx = float(tx_i.max() / mean_tx_active) if mean_tx_active else 0.0
        mean_flow_active = float(flow_log_i[active].mean()) if active_days else 0.0
        std_flow_active = float(flow_log_i[active].std()) if active_days else 0.0
        flow_burstiness = std_flow_active / mean_flow_active if mean_flow_active else 0.0
        net_direction_bias = float(net_i.sum() / flow_sum) if flow_sum else 0.0
        active_streak = longest_run(active, True)
        inactive_streak = longest_run(active, False)
        active_switches = count_switches(active)

        weekly_tx = pd.Series(tx_i).rolling(7, min_periods=1).sum().to_numpy()
        weekly_change = np.abs(np.diff(weekly_tx))
        max_weekly_change = float(weekly_change.max()) if len(weekly_change) else 0.0
        weekly_change_ratio = max_weekly_change / tx_sum if tx_sum else 0.0

        row = {
            "active_days": active_days,
            "active_ratio": active_ratio,
            "total_tx": tx_sum,
            "log_total_flow_sum": flow_log_sum,
            "mean_tx_active_day": mean_tx_active,
            "tx_burstiness_cv": burstiness,
            "max_to_mean_tx_ratio": max_to_mean_tx,
            "log_flow_burstiness_cv": flow_burstiness,
            "net_direction_bias": net_direction_bias,
            "longest_active_streak": active_streak,
            "longest_inactive_gap": inactive_streak,
            "active_inactive_switches": active_switches,
            "max_weekly_tx_change": max_weekly_change,
            "max_weekly_tx_change_ratio": weekly_change_ratio,
        }
        rows.append(row)
    out = pd.DataFrame(rows)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def spectral_features_for_signal(signal: np.ndarray, prefix: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    signal = sanitize_signal_matrix(signal)
    transformed = np.log1p(np.maximum(signal, 0))
    centered = transformed - transformed.mean(axis=1, keepdims=True)
    fft = np.fft.rfft(centered, axis=1)
    power = np.abs(fft) ** 2
    freqs = np.fft.rfftfreq(signal.shape[1], d=1.0)

    # Remove DC component for behavioural rhythm analysis.
    power_no_dc = power[:, 1:]
    freqs_no_dc = freqs[1:]
    total_power = power_no_dc.sum(axis=1)
    total_power_safe = np.where(total_power == 0, 1.0, total_power)
    norm_power = power_no_dc / total_power_safe[:, None]

    dominant_idx = np.argmax(power_no_dc, axis=1)
    dominant_freq = freqs_no_dc[dominant_idx]
    dominant_period = np.divide(1.0, dominant_freq, out=np.zeros_like(dominant_freq), where=dominant_freq > 0)
    peak_share = power_no_dc[np.arange(len(power_no_dc)), dominant_idx] / total_power_safe

    def band_share(low_freq: float, high_freq: float) -> np.ndarray:
        mask = (freqs_no_dc >= low_freq) & (freqs_no_dc < high_freq)
        if not mask.any():
            return np.zeros(signal.shape[0])
        return norm_power[:, mask].sum(axis=1)

    low_frequency_power = band_share(0.0, 1 / 60)
    medium_frequency_power = band_share(1 / 60, 1 / 14)
    high_frequency_power = band_share(1 / 14, 0.5 + 1e-9)
    weekly_band_power = band_share(1 / 8, 1 / 6)
    monthly_band_power = band_share(1 / 35, 1 / 25)
    spectral_entropy = entropy(norm_power.T, base=2)
    spectral_entropy = np.nan_to_num(spectral_entropy, nan=0.0, posinf=0.0, neginf=0.0)

    features = pd.DataFrame(
        {
            f"{prefix}_spectral_total_power": np.log1p(total_power),
            f"{prefix}_dominant_frequency": dominant_freq,
            f"{prefix}_dominant_period_days": dominant_period,
            f"{prefix}_peak_power_share": peak_share,
            f"{prefix}_low_frequency_power_share": low_frequency_power,
            f"{prefix}_medium_frequency_power_share": medium_frequency_power,
            f"{prefix}_high_frequency_power_share": high_frequency_power,
            f"{prefix}_weekly_band_power_share": weekly_band_power,
            f"{prefix}_monthly_band_power_share": monthly_band_power,
            f"{prefix}_spectral_entropy": spectral_entropy,
        }
    )
    features = features.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    norm_power = np.nan_to_num(norm_power, nan=0.0, posinf=0.0, neginf=0.0)
    return features, freqs_no_dc, norm_power


def cluster_features(features: pd.DataFrame, k: int, random_state: int) -> tuple[np.ndarray, pd.DataFrame]:
    scaler = StandardScaler()
    X = scaler.fit_transform(features.replace([np.inf, -np.inf], np.nan).fillna(0.0))
    model = MiniBatchKMeans(n_clusters=k, random_state=random_state, n_init=20, batch_size=4096)
    labels = model.fit_predict(X)
    profiles = features.assign(cluster=labels).groupby("cluster").median(numeric_only=True).reset_index()
    return labels, profiles


def plot_mean_power_by_group(
    out_path: Path,
    freqs: np.ndarray,
    norm_power: np.ndarray,
    group_labels: np.ndarray,
    title: str,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    for group in sorted(np.unique(group_labels)):
        mask = group_labels == group
        if mask.sum() == 0:
            continue
        ax.plot(freqs, norm_power[mask].mean(axis=0), label=f"C{group}", linewidth=1.8)
    ax.set_xlabel("Frequency (cycles per day)")
    ax.set_ylabel("Mean normalized spectral power")
    ax.set_title(title)
    ax.legend(ncol=3, fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def random_label_null_same_cluster(edges: pd.DataFrame, label_col: str, permutations: int, random_state: int) -> dict:
    valid = edges.dropna(subset=[f"source_{label_col}", f"target_{label_col}"]).copy()
    if valid.empty:
        return {
            "edge_count": 0,
            "observed_same_cluster_ratio": np.nan,
            "null_mean": np.nan,
            "null_std": np.nan,
            "p_value_upper": np.nan,
        }
    observed = (valid[f"source_{label_col}"].to_numpy() == valid[f"target_{label_col}"].to_numpy()).mean()
    unique_nodes = pd.unique(pd.concat([valid["sender"], valid["recipient"]], ignore_index=True))
    node_labels = (
        pd.concat(
            [
                valid[["sender", f"source_{label_col}"]].rename(columns={"sender": "wallet", f"source_{label_col}": "label"}),
                valid[["recipient", f"target_{label_col}"]].rename(columns={"recipient": "wallet", f"target_{label_col}": "label"}),
            ],
            ignore_index=True,
        )
        .drop_duplicates("wallet")
        .set_index("wallet")["label"]
        .reindex(unique_nodes)
    )
    rng = np.random.default_rng(random_state)
    null = []
    for _ in range(permutations):
        shuffled = node_labels.to_numpy().copy()
        rng.shuffle(shuffled)
        shuffled_map = dict(zip(unique_nodes, shuffled))
        s = valid["sender"].map(shuffled_map).to_numpy()
        t = valid["recipient"].map(shuffled_map).to_numpy()
        null.append((s == t).mean())
    null = np.asarray(null)
    return {
        "edge_count": len(valid),
        "observed_same_cluster_ratio": float(observed),
        "null_mean": float(null.mean()),
        "null_std": float(null.std()),
        "p_value_upper": float((np.sum(null >= observed) + 1) / (len(null) + 1)),
    }


def build_network_signal_validation(
    edges_path: Path,
    assignments: pd.DataFrame,
    out_dir: Path,
    permutations: int,
    random_state: int,
) -> pd.DataFrame:
    if not edges_path.exists():
        return pd.DataFrame(
            [
                {
                    "label_type": "not_run",
                    "edge_count": 0,
                    "observed_same_cluster_ratio": np.nan,
                    "null_mean": np.nan,
                    "null_std": np.nan,
                    "p_value_upper": np.nan,
                    "note": f"Missing edge file: {edges_path}",
                }
            ]
        )

    edges = pd.read_csv(edges_path, dtype={"sender": str, "recipient": str})
    edges["sender"] = clean_wallet(edges["sender"])
    edges["recipient"] = clean_wallet(edges["recipient"])
    label_map = assignments.set_index("wallet")
    for label_col in ["k5_cluster", "wavelength_cluster", "time_domain_cluster"]:
        edges[f"source_{label_col}"] = edges["sender"].map(label_map[label_col])
        edges[f"target_{label_col}"] = edges["recipient"].map(label_map[label_col])

    rows = []
    for label_col in ["k5_cluster", "wavelength_cluster", "time_domain_cluster"]:
        result = random_label_null_same_cluster(edges, label_col, permutations, random_state)
        result["label_type"] = label_col
        result["note"] = "sampled September 2022 transaction edges restricted to wallets in the signal-analysis sample"
        rows.append(result)
    summary = pd.DataFrame(rows)
    summary = summary[
        [
            "label_type",
            "edge_count",
            "observed_same_cluster_ratio",
            "null_mean",
            "null_std",
            "p_value_upper",
            "note",
        ]
    ]
    summary.to_csv(out_dir / "network_signal_cluster_null_tests.csv", index=False)
    return summary


def write_report(
    out_dir: Path,
    sample_size: int,
    comparison: pd.DataFrame,
    network_summary: pd.DataFrame,
    trajectory_files: list[str],
) -> None:
    lines = [
        "# Temporal Signal Analysis Pack",
        "",
        "## Purpose",
        "",
        "This pack starts the next academic stage of the project: moving from static aggregate wallet roles to temporal signal-based wallet profiling.",
        "",
        "The analysis has four parts:",
        "",
        "1. Wavelength/spectrum-based clustering of wallet activity signals.",
        "2. Frequency-domain analysis with frequency on the x-axis.",
        "3. Time-domain temporal signature analysis.",
        "4. Network-science validation of the resulting signal clusters.",
        "",
        "## Method Summary",
        "",
        f"The first run uses a stratified sample of `{sample_size}` EOA wallets from the K5 taxonomy.",
        "",
        "For each sampled wallet, the script builds daily 2022 signals from transaction count, total value flow, and net flow.",
        "",
        "Frequency-domain features are extracted using the real FFT of daily transaction-count and total-flow signals. The DC component is removed so the analysis focuses on rhythms rather than total scale.",
        "",
        "Time-domain features measure active days, active/inactive switching, burstiness, active streaks, inactive gaps, direction bias, and weekly change intensity.",
        "",
        "The network-science step uses sampled September 2022 transaction edges and tests whether signal-cluster labels show same-cluster transaction concentration stronger than shuffled-label null models.",
        "",
        "## Cluster Correspondence With Existing K5 Roles",
        "",
        comparison.to_markdown(index=False),
        "",
        "Interpretation: ARI and NMI measure whether the new signal-derived clusters reproduce the existing K5 behavioural taxonomy. Low or moderate agreement is not necessarily a failure; it can mean the temporal-signal view captures a different axis of behaviour.",
        "",
        "## Network-Science Signal Validation",
        "",
        network_summary.to_markdown(index=False),
        "",
        "Interpretation: this is an early network check. Because the signal clusters are built on a wallet sample, the network test is limited to sampled wallets that also appear in the sampled transaction-edge file.",
        "",
        "In this first run, the network test is underpowered if the edge count is very small. In that case, it should be treated as a pipeline proof-of-concept rather than evidence for or against network alignment.",
        "",
        "The next network-valid version should either increase the signal-analysis sample size substantially, sample wallets directly from transaction-edge endpoints, or assign signal features to the full EOA population before rerunning network assortativity/null tests.",
        "",
        "## First-Pass Findings",
        "",
        "- The wavelength/spectral clusters have low agreement with the original K5 roles, which suggests that frequency-domain rhythm captures a different behavioural axis from aggregate wallet features.",
        "- The time-domain clusters show somewhat stronger, but still limited, agreement with K5. This is expected because both include activity intensity and persistence information.",
        "- Frequency-domain and time-domain clusters also have low agreement with each other, suggesting that rhythm-based behaviour and direct time-axis burst/gap behaviour are related but not identical.",
        "- The network-science component has been scaffolded, but the first sample is not large enough for a meaningful signal-cluster network test.",
        "",
        "## Main Output Files",
        "",
    ]
    for file in trajectory_files:
        lines.append(f"- `{file}`")
    lines.extend(
        [
            "",
            "## Academic Claim Boundary",
            "",
            "This is a first signal-analysis pipeline, not yet a final causal or intelligence-style detection system.",
            "",
            "Safe wording:",
            "",
            "> We extend wallet segmentation by representing wallet activity as daily temporal signals and comparing frequency-domain, time-domain, and network-structural evidence.",
            "",
            "Avoid wording:",
            "",
            "> These methods identify real-world entities, prove causality, or replicate classified security-agency systems.",
        ]
    )
    (out_dir / "temporal_signal_analysis_report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build temporal signal, frequency, time-domain, and network-science analysis pack.")
    parser.add_argument("--cluster-file", default="results/eoa_only_kmeans5/wallet_eoa_only_kmeans_clusters.csv")
    parser.add_argument("--daily-data-dir", default="../dataverse_files")
    parser.add_argument("--edges", default="results/eoa_only_kmeans5/network_validation/sampled_edges_for_null_test.csv")
    parser.add_argument("--out-dir", default="results/temporal_signal_analysis")
    parser.add_argument("--sample-per-cluster", type=int, default=1000)
    parser.add_argument("--k-signal", type=int, default=5)
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    parser.add_argument("--permutations", type=int, default=200)
    parser.add_argument("--random-state", type=int, default=492)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(exist_ok=True)

    sample_path = out_dir / "signal_analysis_wallet_sample.csv"
    matrix_path = out_dir / "sample_daily_signal_matrices.npz"
    if sample_path.exists():
        sample = pd.read_csv(sample_path, dtype={"wallet": str})
        sample["wallet"] = clean_wallet(sample["wallet"])
        print(f"Loaded existing wallet sample: {sample_path}", flush=True)
    else:
        sample = load_stratified_sample(Path(args.cluster_file), args.sample_per_cluster, args.random_state)
        sample = sample.rename(columns={"cluster": "k5_cluster"})
        sample.to_csv(sample_path, index=False)

    if matrix_path.exists():
        loaded = np.load(matrix_path)
        tx = sanitize_signal_matrix(loaded["tx"])
        total_flow = sanitize_signal_matrix(loaded["total_flow"])
        net_flow = sanitize_signal_matrix(loaded["net_flow"])
        dates = pd.date_range("2022-01-01", "2022-12-31", freq="D")
        np.savez_compressed(matrix_path, tx=tx, total_flow=total_flow, net_flow=net_flow)
        print(f"Loaded existing signal matrices: {matrix_path}", flush=True)
    else:
        dates, tx, total_flow, net_flow = build_daily_signal_matrices(sample, Path(args.daily_data_dir), args.chunksize)
        tx = sanitize_signal_matrix(tx)
        total_flow = sanitize_signal_matrix(total_flow)
        net_flow = sanitize_signal_matrix(net_flow)
        np.savez_compressed(matrix_path, tx=tx, total_flow=total_flow, net_flow=net_flow)

    time_features = extract_time_domain_features(tx, total_flow, net_flow)
    tx_spectral, freqs, tx_norm_power = spectral_features_for_signal(tx, "tx")
    flow_spectral, _, flow_norm_power = spectral_features_for_signal(total_flow, "flow")
    spectral_features = pd.concat([tx_spectral, flow_spectral], axis=1)

    wavelength_labels, wavelength_profiles = cluster_features(spectral_features, args.k_signal, args.random_state)
    time_labels, time_profiles = cluster_features(time_features, args.k_signal, args.random_state)

    assignments = sample.copy()
    assignments["wavelength_cluster"] = wavelength_labels.astype(int)
    assignments["time_domain_cluster"] = time_labels.astype(int)
    assignments.to_csv(out_dir / "temporal_signal_cluster_assignments.csv", index=False)

    spectral_out = pd.concat([assignments[["wallet", "k5_cluster", "wavelength_cluster"]], spectral_features], axis=1)
    time_out = pd.concat([assignments[["wallet", "k5_cluster", "time_domain_cluster"]], time_features], axis=1)
    spectral_out.to_csv(out_dir / "wallet_frequency_domain_features.csv", index=False)
    time_out.to_csv(out_dir / "wallet_time_domain_features.csv", index=False)
    wavelength_profiles.to_csv(out_dir / "wavelength_cluster_profiles.csv", index=False)
    time_profiles.to_csv(out_dir / "time_domain_cluster_profiles.csv", index=False)

    comparison = pd.DataFrame(
        [
            {
                "comparison": "K5 vs wavelength/spectral clusters",
                "ari": adjusted_rand_score(assignments["k5_cluster"], assignments["wavelength_cluster"]),
                "nmi": normalized_mutual_info_score(assignments["k5_cluster"], assignments["wavelength_cluster"]),
            },
            {
                "comparison": "K5 vs time-domain clusters",
                "ari": adjusted_rand_score(assignments["k5_cluster"], assignments["time_domain_cluster"]),
                "nmi": normalized_mutual_info_score(assignments["k5_cluster"], assignments["time_domain_cluster"]),
            },
            {
                "comparison": "wavelength/spectral vs time-domain clusters",
                "ari": adjusted_rand_score(assignments["wavelength_cluster"], assignments["time_domain_cluster"]),
                "nmi": normalized_mutual_info_score(assignments["wavelength_cluster"], assignments["time_domain_cluster"]),
            },
        ]
    )
    comparison.to_csv(out_dir / "signal_cluster_correspondence_summary.csv", index=False)
    pd.crosstab(assignments["k5_cluster"], assignments["wavelength_cluster"]).to_csv(out_dir / "k5_vs_wavelength_cluster_crosstab.csv")
    pd.crosstab(assignments["k5_cluster"], assignments["time_domain_cluster"]).to_csv(out_dir / "k5_vs_time_domain_cluster_crosstab.csv")

    plot_mean_power_by_group(fig_dir / "frequency_power_by_k5_role.png", freqs, tx_norm_power, assignments["k5_cluster"].to_numpy(), "Mean Transaction-Count Spectrum By K5 Role")
    plot_mean_power_by_group(fig_dir / "frequency_power_by_wavelength_cluster.png", freqs, tx_norm_power, assignments["wavelength_cluster"].to_numpy(), "Mean Transaction-Count Spectrum By Wavelength Cluster")
    plot_mean_power_by_group(fig_dir / "flow_frequency_power_by_wavelength_cluster.png", freqs, flow_norm_power, assignments["wavelength_cluster"].to_numpy(), "Mean Total-Flow Spectrum By Wavelength Cluster")

    network_summary = build_network_signal_validation(
        Path(args.edges),
        assignments,
        out_dir,
        args.permutations,
        args.random_state,
    )

    write_report(
        out_dir,
        sample_size=len(sample),
        comparison=comparison,
        network_summary=network_summary,
        trajectory_files=[
            "signal_analysis_wallet_sample.csv",
            "wallet_frequency_domain_features.csv",
            "wallet_time_domain_features.csv",
            "temporal_signal_cluster_assignments.csv",
            "wavelength_cluster_profiles.csv",
            "time_domain_cluster_profiles.csv",
            "signal_cluster_correspondence_summary.csv",
            "network_signal_cluster_null_tests.csv",
            "figures/frequency_power_by_k5_role.png",
            "figures/frequency_power_by_wavelength_cluster.png",
            "figures/flow_frequency_power_by_wavelength_cluster.png",
        ],
    )
    print(f"Saved temporal signal analysis pack to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
