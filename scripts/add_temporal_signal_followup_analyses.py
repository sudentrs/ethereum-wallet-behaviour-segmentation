from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BASE = Path("results/full_eoa_temporal_signal_streaming_k5/model_selection")
TEMPORAL = Path("results/eoa_only_kmeans5/temporal_validation")
K5_STRENGTH = Path("results/k5_academic_strengthening")
OUT = BASE / "followup_analyses"


TIME_FEATURES = Path("results/full_eoa_temporal_signal_streaming_k5/full_eoa_time_domain_features_raw.csv")
WAVE_FEATURES = Path("results/full_eoa_temporal_signal_streaming_k5/full_eoa_wavelength_features_raw.csv")
ASSIGNMENTS = Path("results/full_eoa_temporal_signal_streaming_k5/full_eoa_temporal_signal_assignments.csv")


def entropy_bits(values: np.ndarray) -> float:
    values = values.astype(float)
    total = values.sum()
    if total <= 0:
        return 0.0
    p = values[values > 0] / total
    return float(-(p * np.log2(p)).sum())


def transition_predictiveness() -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = pd.read_csv(TEMPORAL / "overall_transition_count_matrix.csv", index_col=0)
    counts.index = counts.index.astype(int)
    counts.columns = counts.columns.astype(int)
    total = counts.to_numpy().sum()
    row_totals = counts.sum(axis=1)
    col_totals = counts.sum(axis=0)
    marginal_next = col_totals / total
    h_next = entropy_bits(col_totals.to_numpy())
    h_next_given_state = 0.0
    rows = []
    for state, row in counts.iterrows():
        row_total = float(row.sum())
        probs = row / row_total
        row_entropy = entropy_bits(row.to_numpy())
        h_next_given_state += (row_total / total) * row_entropy
        top_state = int(probs.idxmax())
        rows.append(
            {
                "from_state": int(state),
                "wallet_month_pairs": int(row_total),
                "self_transition_probability": float(probs.loc[state]),
                "top_next_state": top_state,
                "top_next_probability": float(probs.loc[top_state]),
                "marginal_probability_of_top_next": float(marginal_next.loc[top_state]),
                "top_next_lift_vs_marginal": float(probs.loc[top_state] / marginal_next.loc[top_state]),
                "row_entropy_bits": row_entropy,
            }
        )

    mutual_information = h_next - h_next_given_state
    summary = pd.DataFrame(
        [
            {
                "total_wallet_month_pairs": int(total),
                "next_state_entropy_bits": h_next,
                "conditional_entropy_bits": h_next_given_state,
                "mutual_information_bits": mutual_information,
                "normalized_entropy_reduction": mutual_information / h_next if h_next else 0.0,
                "overall_self_transition_rate": float(np.trace(counts.to_numpy()) / total),
            }
        ]
    )
    detail = pd.DataFrame(rows)
    summary.to_csv(OUT / "temporal_transition_predictiveness_summary.csv", index=False)
    detail.to_csv(OUT / "temporal_transition_predictiveness_by_state.csv", index=False)
    return summary, detail


def load_assignments() -> pd.DataFrame:
    usecols = ["wallet", "k_cluster", "time_domain_cluster", "wavelength_cluster"]
    assignments = pd.read_csv(ASSIGNMENTS, usecols=usecols, dtype={"wallet": str})
    assignments["wallet"] = assignments["wallet"].astype("string").str.strip().str.lower()
    return assignments


def aggregate_time_outcomes(assignments: pd.DataFrame, chunksize: int = 250_000) -> pd.DataFrame:
    usecols = [
        "wallet",
        "active_days",
        "total_tx",
        "log_total_flow_sum",
        "mean_tx_active_day",
        "tx_burstiness_cv",
        "max_to_mean_tx_ratio",
        "longest_inactive_gap",
        "active_inactive_switches",
        "net_direction_bias",
    ]
    pieces = []
    keep = assignments[["wallet", "k_cluster", "time_domain_cluster"]]
    for chunk in pd.read_csv(TIME_FEATURES, usecols=usecols, dtype={"wallet": str}, chunksize=chunksize):
        chunk["wallet"] = chunk["wallet"].astype("string").str.strip().str.lower()
        merged = chunk.merge(keep, on="wallet", how="inner", copy=False)
        grouped = (
            merged.groupby(["k_cluster", "time_domain_cluster"], observed=True)
            .agg(
                wallet_count=("wallet", "count"),
                active_days_mean=("active_days", "mean"),
                total_tx_median=("total_tx", "median"),
                total_tx_mean=("total_tx", "mean"),
                log_total_flow_sum_mean=("log_total_flow_sum", "mean"),
                mean_tx_active_day_mean=("mean_tx_active_day", "mean"),
                tx_burstiness_cv_mean=("tx_burstiness_cv", "mean"),
                max_to_mean_tx_ratio_mean=("max_to_mean_tx_ratio", "mean"),
                longest_inactive_gap_mean=("longest_inactive_gap", "mean"),
                active_inactive_switches_mean=("active_inactive_switches", "mean"),
                net_direction_bias_mean=("net_direction_bias", "mean"),
            )
            .reset_index()
        )
        pieces.append(grouped)
    raw = pd.concat(pieces, ignore_index=True)
    metrics = [c for c in raw.columns if c not in {"k_cluster", "time_domain_cluster", "wallet_count"}]
    weighted = raw.copy()
    for c in metrics:
        weighted[c] = weighted[c] * weighted["wallet_count"]
    agg = weighted.groupby(["k_cluster", "time_domain_cluster"], observed=True).sum(numeric_only=True).reset_index()
    for c in metrics:
        agg[c] = agg[c] / agg["wallet_count"]
    agg["within_behavior_share"] = agg["wallet_count"] / agg.groupby("k_cluster")["wallet_count"].transform("sum")
    agg = agg.sort_values(["k_cluster", "within_behavior_share"], ascending=[True, False])
    agg.to_csv(OUT / "behavior_k5_time_domain_outcome_profile.csv", index=False)
    return agg


def trajectory_bridge() -> pd.DataFrame:
    by_start = pd.read_csv(K5_STRENGTH / "trajectory_type_by_start_state.csv")
    pivot = by_start.pivot_table(
        index="start_state",
        columns="trajectory_type",
        values="share_within_start_state",
        fill_value=0.0,
    ).reset_index()
    rename = {"start_state": "behavior_k5_start_state"}
    pivot = pivot.rename(columns=rename)
    for col in [
        "returner",
        "one_time_switcher",
        "persistent",
        "multi_step_mover",
        "volatile_switcher",
        "mostly_stable_with_noise",
        "insufficient_observation",
    ]:
        if col not in pivot.columns:
            pivot[col] = 0.0

    time_rel = pd.read_csv(BASE / "behavior_k5_vs_time_domain_cluster_long_summary.csv")
    wave_rel = pd.read_csv(BASE / "behavior_k5_vs_wavelength_cluster_long_summary.csv")
    td4 = time_rel[time_rel["time_domain_cluster"] == 4][
        ["behavior_k5_cluster", "within_behavior_share", "enrichment_vs_global"]
    ].rename(
        columns={
            "behavior_k5_cluster": "behavior_k5_start_state",
            "within_behavior_share": "td4_intermit_switching_share",
            "enrichment_vs_global": "td4_intermit_switching_enrichment",
        }
    )
    w2 = wave_rel[wave_rel["wavelength_cluster"] == 2][
        ["behavior_k5_cluster", "within_behavior_share", "enrichment_vs_global"]
    ].rename(
        columns={
            "behavior_k5_cluster": "behavior_k5_start_state",
            "within_behavior_share": "w2_slow_cycle_share",
            "enrichment_vs_global": "w2_slow_cycle_enrichment",
        }
    )
    bridge = pivot.merge(td4, on="behavior_k5_start_state", how="left").merge(w2, on="behavior_k5_start_state", how="left")
    bridge = bridge.fillna(0.0)
    bridge.to_csv(OUT / "trajectory_type_signal_bridge_by_behavior_k5.csv", index=False)
    return bridge


def write_report(summary: pd.DataFrame, state_detail: pd.DataFrame, time_out: pd.DataFrame, bridge: pd.DataFrame) -> None:
    def pct(x: float) -> str:
        return f"{100 * float(x):.1f}%"

    top_td = time_out.groupby("k_cluster").head(1)
    wave_rel = pd.read_csv(BASE / "behavior_k5_vs_wavelength_cluster_long_summary.csv")
    wave_profiles = pd.read_csv(BASE / "wavelength_k3_cluster_profiles.csv")
    top_wave = (
        wave_rel.sort_values(["behavior_k5_cluster", "within_behavior_share"], ascending=[True, False])
        .groupby("behavior_k5_cluster")
        .head(1)
    )
    lines = [
        "# Additional Temporal Signal Analyses",
        "",
        "This note adds three follow-up analyses requested after the initial time-domain and wavelength report.",
        "",
        "## 1. Temporal Transition Predictiveness",
        "",
    ]
    s = summary.iloc[0]
    lines += [
        f"- Total consecutive wallet-month pairs: `{int(s['total_wallet_month_pairs']):,}`.",
        f"- Overall self-transition rate: `{pct(s['overall_self_transition_rate'])}`.",
        f"- Next-state entropy: `{s['next_state_entropy_bits']:.3f}` bits.",
        f"- Conditional entropy after knowing current state: `{s['conditional_entropy_bits']:.3f}` bits.",
        f"- Entropy reduction / normalized predictiveness: `{100*s['normalized_entropy_reduction']:.1f}%`.",
        "",
        "| Current state | Self-transition | Top next state | Top-next probability | Lift vs marginal |",
        "|---:|---:|---:|---:|---:|",
    ]
    for _, r in state_detail.iterrows():
        lines.append(
            f"| {int(r['from_state'])} | {pct(r['self_transition_probability'])} | {int(r['top_next_state'])} | {pct(r['top_next_probability'])} | {r['top_next_lift_vs_marginal']:.2f}x |"
        )
    lines += [
        "",
        "Interpretation: the current monthly behavior state carries measurable information about the next monthly state. The effect is moderate, not deterministic, which is appropriate for behavioral wallet states.",
        "",
        "## 2. Behavior K5 x Signal Outcome Profiling",
        "",
        "### Time-domain dominant profile by Behavior K5",
        "",
        "| Behavior K5 | Dominant TD state | Share | Mean active days | Mean switches | Mean inactive gap | Mean burstiness |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in top_td.iterrows():
        lines.append(
            f"| {int(r['k_cluster'])} | TD{int(r['time_domain_cluster'])} | {pct(r['within_behavior_share'])} | {r['active_days_mean']:.2f} | {r['active_inactive_switches_mean']:.2f} | {r['longest_inactive_gap_mean']:.2f} | {r['tx_burstiness_cv_mean']:.3f} |"
        )
    lines += [
        "",
        "### Wavelength K3 rhythm relationship by Behavior K5",
        "",
        "| Behavior K5 | Dominant W state | Share | Enrichment vs global | Rhythm interpretation |",
        "|---:|---:|---:|---:|---|",
    ]
    for _, r in top_wave.iterrows():
        c = int(r["wavelength_cluster"])
        label = "slow-cycle concentrated rhythm" if c == 2 else "distributed rhythm"
        lines.append(
            f"| {int(r['behavior_k5_cluster'])} | W{c} | {pct(r['within_behavior_share'])} | {r['enrichment_vs_global']:.2f}x | {label} |"
        )
    lines += [
        "",
        "### Wavelength K3 global rhythm profiles",
        "",
        "| W state | Wallet share | Dominant period | High-frequency share | Low-frequency share | Entropy | Interpretation |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in wave_profiles.iterrows():
        c = int(r["cluster"])
        label = "short/medium distributed rhythm" if c == 0 else "longer distributed rhythm" if c == 1 else "slow-cycle concentrated rhythm"
        lines.append(
            f"| W{c} | {pct(r['wallet_share'])} | {r['tx_dominant_period_days']:.2f} | {r['tx_high_frequency_power_share']:.3f} | {r['tx_low_frequency_power_share']:.3f} | {r['tx_spectral_entropy']:.3f} | {label} |"
        )
    lines += [
        "",
        "Interpretation: Behavior K5 roles have different time-domain profiles and different wavelength K3 rhythm enrichments. This supports the claim that the static K5 taxonomy carries temporal signatures.",
        "",
        "## 3. Returner and One-Time Switcher Bridge",
        "",
        "This bridge uses the existing monthly K5 trajectory summary by starting behavior state and relates it to the signal-cluster enrichments observed in the full EOA temporal signal analysis.",
        "",
        "| Behavior K5 start | Returner share | One-time switcher share | TD4 intermittent enrichment | W2 slow-cycle enrichment |",
        "|---:|---:|---:|---:|---:|",
    ]
    for _, r in bridge.iterrows():
        lines.append(
            f"| {int(r['behavior_k5_start_state'])} | {pct(r['returner'])} | {pct(r['one_time_switcher'])} | {r['td4_intermit_switching_enrichment']:.2f}x | {r['w2_slow_cycle_enrichment']:.2f}x |"
        )
    lines += [
        "",
        "Interpretation: Behavior K5 cluster 3 combines a high one-time-switcher share with strong intermittent-switching and slow-cycle signal enrichment. Behavior K5 clusters 1, 2, and 4 are more returner-oriented, but cluster 4 has weaker monthly self-persistence and still carries slow-cycle signal enrichment.",
    ]
    (OUT / "additional_temporal_signal_analyses_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary, detail = transition_predictiveness()
    assignments = load_assignments()
    time_out = aggregate_time_outcomes(assignments)
    bridge = trajectory_bridge()
    write_report(summary, detail, time_out, bridge)
    print(OUT)


if __name__ == "__main__":
    main()
