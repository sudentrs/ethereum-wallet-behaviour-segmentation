import argparse
from pathlib import Path

import pandas as pd


FEATURE_GROUPS = {
    "activity_intensity": [
        "total_tx",
        "avg_daily_tx_count",
        "max_daily_tx_count",
        "std_daily_tx_count",
        "tx_count_cv",
        "tx_concentration_ratio",
    ],
    "activity_persistence": [
        "active_days_observed",
        "activity_span_days",
        "activity_density",
        "in_active_days",
        "out_active_days",
        "both_active_days",
    ],
    "value_scale": [
        "total_in_sum",
        "total_out_sum",
        "total_net_flow_sum",
        "total_flow_sum",
        "avg_daily_total_in",
        "avg_daily_total_out",
        "avg_daily_net_flow",
        "avg_daily_total_flow",
        "max_daily_total_in",
        "max_daily_total_out",
        "max_daily_total_flow",
    ],
    "directionality": [
        "in_active_day_ratio",
        "out_active_day_ratio",
        "both_active_day_ratio",
        "in_out_day_balance",
    ],
    "volatility": [
        "std_daily_total_in",
        "std_daily_total_out",
        "std_daily_net_flow",
        "std_daily_total_flow",
        "total_flow_cv",
        "flow_concentration_ratio",
    ],
}


def score_groups(row: pd.Series) -> dict[str, float]:
    scores = {}
    for group, cols in FEATURE_GROUPS.items():
        available = [col for col in cols if col in row.index]
        scores[group] = float(row[available].mean()) if available else 0.0
    return scores


def label_from_scores(scores: dict[str, float], row: pd.Series) -> str:
    bits = []
    if scores["activity_intensity"] >= 0.75:
        bits.append("high-transaction")
    elif scores["activity_intensity"] <= -0.45:
        bits.append("low-transaction")

    if scores["activity_persistence"] >= 0.65:
        bits.append("persistent")
    elif scores["activity_persistence"] <= -0.55:
        bits.append("short-lived")

    if scores["value_scale"] >= 0.55:
        bits.append("large-value-flow")
    elif scores["value_scale"] <= -0.45:
        bits.append("small-value-flow")

    if abs(scores["directionality"]) >= 0.35:
        if row.get("in_out_day_balance", 0) > 0:
            bits.append("inflow-leaning")
        else:
            bits.append("outflow-leaning")

    if scores["volatility"] >= 0.45:
        bits.append("bursty-volatile")

    if not bits:
        dominant = max(scores.items(), key=lambda item: abs(item[1]))[0]
        bits.append(f"{dominant}-leaning")
    return ", ".join(bits)


def main() -> None:
    parser = argparse.ArgumentParser(description="Describe EOA-only KMeans cluster profiles.")
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--sizes", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    profiles = pd.read_csv(args.profiles)
    sizes = pd.read_csv(args.sizes)
    feature_cols = [col for col in profiles.columns if col != "cluster"]

    rows = []
    for _, row in profiles.iterrows():
        cluster = int(row["cluster"])
        feature_values = row[feature_cols].astype(float)
        high = feature_values.sort_values(ascending=False).head(6)
        low = feature_values.sort_values().head(6)
        scores = score_groups(feature_values)
        rows.append(
            {
                "cluster": cluster,
                "behavior_label": label_from_scores(scores, feature_values),
                "top_high_features": "; ".join(f"{key}={value:.2f}" for key, value in high.items()),
                "top_low_features": "; ".join(f"{key}={value:.2f}" for key, value in low.items()),
                **scores,
            }
        )

    descriptions = pd.DataFrame(rows).merge(sizes, on="cluster", how="left")
    ordered_cols = [
        "cluster",
        "wallet_count",
        "wallet_share",
        "behavior_label",
        "activity_intensity",
        "activity_persistence",
        "value_scale",
        "directionality",
        "volatility",
        "top_high_features",
        "top_low_features",
    ]
    descriptions = descriptions[ordered_cols].sort_values("cluster")
    descriptions.to_csv(out_dir / "eoa_only_cluster_behavior_labels.csv", index=False)

    lines = [
        "# EOA-Only KMeans6 Cluster Behavior Labels",
        "",
        "These labels describe the post-Gate-1 EOA-only clusters. They should replace the pre-Gate-1 mixed-address role labels in paper-facing claims.",
        "",
        descriptions.to_markdown(index=False),
        "",
        "## Caution",
        "",
        "The labels are behavioural summaries, not verified real-world identities. They are based on median robust-scaled feature profiles after removing contract addresses.",
    ]
    (out_dir / "eoa_only_cluster_behavior_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(descriptions.to_string(index=False))
    print(f"Saved EOA-only cluster descriptions to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
