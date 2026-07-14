import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_SRC = Path(__file__).resolve().parents[1]
if str(PROJECT_SRC / "features") not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC / "features"))

from build_full_kmeans6_expanded_features import aggregate_daily_features, derive_features, read_labels


def load_scaling_stats(path: Path) -> dict:
    stats = pd.read_csv(path)
    return stats.set_index("feature").to_dict(orient="index")


def transform_with_stats(name: str, series: pd.Series, stats: dict) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    meta = stats[name]
    transform_type = meta["transform_type"]
    if transform_type == "log1p":
        transformed = np.log1p(s)
    elif transform_type == "signed_log1p":
        transformed = np.sign(s) * np.log1p(np.abs(s))
    elif transform_type == "raw":
        transformed = s
    else:
        raise ValueError(f"Unknown transform_type for {name}: {transform_type}")

    iqr = meta["iqr"]
    if pd.isna(iqr) or iqr == 0:
        return transformed - meta["median"]
    return (transformed - meta["median"]) / iqr


def scale_monthly_features(month_features: pd.DataFrame, stats: dict, feature_cols: list[str]) -> pd.DataFrame:
    out = month_features[["wallet"]].copy()
    for col in feature_cols:
        if col in month_features.columns and col in stats:
            out[col] = transform_with_stats(col, month_features[col], stats).astype("float32")
    return out


def nearest_centroid_assignments(month_scaled: pd.DataFrame, centroids: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    X = month_scaled[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy(dtype=np.float32)
    C = centroids[feature_cols].to_numpy(dtype=np.float32)
    labels = centroids.index.to_numpy()

    dists = np.empty((len(X), len(C)), dtype=np.float32)
    for i, centroid in enumerate(C):
        diff = X - centroid
        dists[:, i] = np.sqrt(np.sum(diff * diff, axis=1))

    order = np.argsort(dists, axis=1)
    best = order[:, 0]
    second = order[:, 1]
    assigned = month_scaled[["wallet"]].copy()
    assigned["monthly_state"] = labels[best].astype(int)
    assigned["nearest_distance"] = dists[np.arange(len(X)), best]
    assigned["second_nearest_distance"] = dists[np.arange(len(X)), second]
    assigned["assignment_margin"] = assigned["second_nearest_distance"] - assigned["nearest_distance"]
    assigned["assignment_margin_ratio"] = assigned["assignment_margin"] / assigned["second_nearest_distance"].replace(0, np.nan)
    return assigned


def entropy(probs: np.ndarray) -> float:
    p = np.asarray(probs, dtype=float)
    p = p[np.isfinite(p) & (p > 0)]
    if len(p) == 0:
        return 0.0
    return float(-(p * np.log2(p)).sum())


def plot_matrix(matrix: pd.DataFrame, out_path: Path, title: str, fmt: str = ".2f") -> None:
    fig, ax = plt.subplots(figsize=(7, 5.8))
    data = matrix.to_numpy(dtype=float)
    im = ax.imshow(data, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels([f"C{c}" for c in matrix.columns])
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels([f"C{c}" for c in matrix.index])
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if np.isfinite(val):
                ax.text(j, i, format(val, fmt), ha="center", va="center", fontsize=8, color="white")
    ax.set_xlabel("Next monthly state")
    ax.set_ylabel("Current monthly state")
    ax.set_title(title)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def two_step_return_analysis(assignments: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    rows = []
    for m0, m1, m2 in zip(months[:-2], months[1:-1], months[2:]):
        a = assignments[assignments["month"] == m0][["wallet", "monthly_state"]].rename(columns={"monthly_state": "state_t"})
        b = assignments[assignments["month"] == m1][["wallet", "monthly_state"]].rename(columns={"monthly_state": "state_t1"})
        c = assignments[assignments["month"] == m2][["wallet", "monthly_state"]].rename(columns={"monthly_state": "state_t2"})
        merged = a.merge(b, on="wallet", how="inner").merge(c, on="wallet", how="inner")
        if merged.empty:
            rows.append({
                "month_t": m0,
                "month_t1": m1,
                "month_t2": m2,
                "wallets_present_all_three": 0,
                "left_original_state_count": 0,
                "returned_to_original_state_count": 0,
                "two_step_return_rate_after_leaving": np.nan,
                "same_state_all_three_rate": np.nan,
            })
            continue
        left = merged[merged["state_t"] != merged["state_t1"]]
        returned = left[left["state_t2"] == left["state_t"]]
        rows.append({
            "month_t": m0,
            "month_t1": m1,
            "month_t2": m2,
            "wallets_present_all_three": len(merged),
            "left_original_state_count": len(left),
            "returned_to_original_state_count": len(returned),
            "two_step_return_rate_after_leaving": len(returned) / len(left) if len(left) else np.nan,
            "same_state_all_three_rate": ((merged["state_t"] == merged["state_t1"]) & (merged["state_t1"] == merged["state_t2"])).mean(),
        })
    return pd.DataFrame(rows)


def write_report(
    out_dir: Path,
    analysis_label: str,
    report_stem: str,
    months: list[str],
    monthly_summary: pd.DataFrame,
    prob_matrix: pd.DataFrame,
    state_stability: pd.DataFrame,
    transition_summary: pd.DataFrame,
    two_step: pd.DataFrame,
) -> None:
    lines = [
        f"# {analysis_label} Temporal Validation",
        "",
        "## Purpose",
        "",
        f"This analysis checks whether the {analysis_label} roles behave like stable behavioural states over time. Each wallet-month is assigned to the nearest full-year prototype in robust-scaled feature space, then month-to-month transitions are summarized.",
        "",
        "## Months",
        "",
        ", ".join(months),
        "",
        "## Monthly State Summary",
        "",
        monthly_summary.to_markdown(index=False),
        "",
        "## Overall Transition Probability Matrix",
        "",
        prob_matrix.to_markdown(),
        "",
        "## State Stability",
        "",
        state_stability.to_markdown(index=False),
        "",
        "## Monthly Transition Summary",
        "",
        transition_summary.to_markdown(index=False),
        "",
        "## Two-Step Return Analysis",
        "",
        two_step.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "The diagonal of the transition matrix measures persistence: wallets that remain in the same behavioural state from one month to the next. High diagonal values support the interpretation of clusters as recurring behavioural states rather than one-time labels.",
        "",
        "Off-diagonal values show common movement paths between roles. These transitions are useful because wallet behaviour is expected to change over time; the important question is whether those changes are structured.",
        "",
        "The two-step return analysis checks the pattern discussed during project review: a wallet can leave its original state for one month and then return to that original state in the following month. A non-trivial return rate supports the idea that some apparent movement is temporary deviation rather than permanent role change.",
    ]
    (out_dir / f"{report_stem}_temporal_validation_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate EOA-only KMeans clusters with monthly temporal state transitions.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--cluster-file", required=True)
    parser.add_argument("--centroids", required=True)
    parser.add_argument("--scaling-stats", required=True)
    parser.add_argument("--out-dir", default="results/eoa_only_kmeans5/temporal_validation")
    parser.add_argument("--analysis-label", default="EOA-Only K5")
    parser.add_argument("--report-stem", default="eoa_k5")
    parser.add_argument("--months", default="202201,202202,202203,202204,202205,202206,202207,202208,202209,202210,202211,202212")
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(exist_ok=True)

    labels = read_labels(args.cluster_file)
    label_map = labels.set_index("wallet")["cluster"]
    centroids = pd.read_csv(args.centroids, index_col=0)
    centroids.index = centroids.index.astype(int)
    stats = load_scaling_stats(Path(args.scaling_stats))
    feature_cols = [col for col in centroids.columns if col in stats]
    months = [month.strip() for month in args.months.split(",") if month.strip()]

    assignment_parts = []
    monthly_rows = []
    for month in months:
        daily_file = data_dir / f"wallet_daily_clean_{month}.csv"
        if not daily_file.exists():
            daily_file = data_dir / f"wallet_daily_{month}.csv"
        if not daily_file.exists():
            raise FileNotFoundError(f"Missing monthly daily file for {month}")

        print(f"month={month} daily_file={daily_file}", flush=True)
        agg, total_rows, kept_rows = aggregate_daily_features(daily_file, labels, args.chunksize)
        month_features = derive_features(agg)
        month_scaled = scale_monthly_features(month_features, stats, feature_cols)
        assigned = nearest_centroid_assignments(month_scaled, centroids, feature_cols)
        assigned["month"] = month
        assigned["full_year_cluster"] = assigned["wallet"].map(label_map).astype(int)
        assigned["matches_full_year_cluster"] = assigned["monthly_state"] == assigned["full_year_cluster"]

        state_counts = assigned["monthly_state"].value_counts(normalize=True).sort_index()
        monthly_rows.append({
            "month": month,
            "daily_rows_read": total_rows,
            "daily_rows_matching_cluster_wallets": kept_rows,
            "active_wallets_assigned": len(assigned),
            "state_entropy_bits": entropy(state_counts.values),
            "matches_full_year_cluster_ratio": assigned["matches_full_year_cluster"].mean(),
            "median_assignment_margin": assigned["assignment_margin"].median(),
            **{f"state_C{c}_share": state_counts.get(c, 0.0) for c in centroids.index},
        })
        assignment_parts.append(assigned)

    assignments = pd.concat(assignment_parts, ignore_index=True)
    assignments.to_csv(out_dir / "wallet_monthly_behavior_states.csv", index=False)
    monthly_summary = pd.DataFrame(monthly_rows)
    monthly_summary.to_csv(out_dir / "monthly_behavior_state_summary.csv", index=False)

    transition_rows = []
    for prev_month, next_month in zip(months[:-1], months[1:]):
        prev = assignments[assignments["month"] == prev_month][["wallet", "monthly_state"]].rename(columns={"monthly_state": "from_state"})
        nxt = assignments[assignments["month"] == next_month][["wallet", "monthly_state"]].rename(columns={"monthly_state": "to_state"})
        merged = prev.merge(nxt, on="wallet", how="inner")
        counts = merged.groupby(["from_state", "to_state"]).size().reset_index(name="wallet_count")
        counts["from_month"] = prev_month
        counts["to_month"] = next_month
        transition_rows.append(counts)

    transitions = pd.concat(transition_rows, ignore_index=True)
    transitions.to_csv(out_dir / "monthly_state_transition_counts_long.csv", index=False)
    clusters = list(centroids.index)
    total_matrix = transitions.groupby(["from_state", "to_state"])["wallet_count"].sum().reset_index()
    count_matrix = total_matrix.pivot(index="from_state", columns="to_state", values="wallet_count").reindex(index=clusters, columns=clusters).fillna(0).astype(int)
    prob_matrix = count_matrix.div(count_matrix.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    count_matrix.to_csv(out_dir / "overall_transition_count_matrix.csv")
    prob_matrix.to_csv(out_dir / "overall_transition_probability_matrix.csv")
    plot_matrix(prob_matrix, fig_dir / "overall_transition_probability_matrix.png", f"{args.analysis_label} Monthly State Transition Probabilities")
    plot_matrix(np.log1p(count_matrix), fig_dir / "overall_transition_count_matrix_log.png", f"{args.analysis_label} Monthly State Transition Counts", fmt=".1f")

    transition_summary_rows = []
    for (prev_month, next_month), sub in transitions.groupby(["from_month", "to_month"]):
        mat = sub.pivot(index="from_state", columns="to_state", values="wallet_count").reindex(index=clusters, columns=clusters).fillna(0)
        total = mat.to_numpy().sum()
        self_count = sum(mat.loc[c, c] for c in clusters)
        probs = mat.div(mat.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
        transition_summary_rows.append({
            "from_month": prev_month,
            "to_month": next_month,
            "wallets_in_both_months": int(total),
            "self_transition_count": int(self_count),
            "self_transition_rate": self_count / total if total else np.nan,
            "mean_row_entropy_bits": np.mean([entropy(probs.loc[c].values) for c in clusters]),
        })
    transition_summary = pd.DataFrame(transition_summary_rows)
    transition_summary.to_csv(out_dir / "monthly_transition_summary.csv", index=False)

    state_rows = []
    for state in clusters:
        row = prob_matrix.loc[state]
        top_dest = row.sort_values(ascending=False).head(3)
        state_rows.append({
            "from_state": state,
            "self_transition_probability": row.loc[state],
            "transition_entropy_bits": entropy(row.values),
            "top_destinations": "; ".join(f"C{idx}={val:.3f}" for idx, val in top_dest.items()),
        })
    state_stability = pd.DataFrame(state_rows)
    state_stability.to_csv(out_dir / "state_transition_stability.csv", index=False)

    two_step = two_step_return_analysis(assignments, months)
    two_step.to_csv(out_dir / "two_step_return_analysis.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for cluster in clusters:
        ax.plot(range(len(monthly_summary)), monthly_summary[f"state_C{cluster}_share"], marker="o", label=f"C{cluster}")
    ax.set_xticks(range(len(monthly_summary["month"])))
    ax.set_xticklabels(monthly_summary["month"], rotation=45, ha="right")
    ax.set_ylabel("Share of active wallets assigned to state")
    ax.set_xlabel("Month")
    ax.set_title(f"{args.analysis_label} Monthly Behaviour-State Composition")
    ax.legend(ncol=3)
    fig.tight_layout()
    fig.savefig(fig_dir / "monthly_behavior_state_composition.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(
        range(len(transition_summary)),
        transition_summary["self_transition_rate"],
        marker="o",
    )
    ax.set_xticks(range(len(transition_summary)))
    ax.set_xticklabels(transition_summary["from_month"] + "->" + transition_summary["to_month"], rotation=45, ha="right")
    ax.set_ylabel("Self-transition rate")
    ax.set_xlabel("Month pair")
    ax.set_title(f"{args.analysis_label} Behavioural State Persistence Over Time")
    fig.tight_layout()
    fig.savefig(fig_dir / "monthly_self_transition_rate.png", dpi=220)
    plt.close(fig)

    write_report(out_dir, args.analysis_label, args.report_stem, months, monthly_summary, prob_matrix, state_stability, transition_summary, two_step)
    print(f"Saved {args.analysis_label} temporal validation to: {out_dir.resolve()}", flush=True)


if __name__ == "__main__":
    main()
