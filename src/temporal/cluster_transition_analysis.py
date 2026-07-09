import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from build_full_kmeans6_expanded_features import read_labels, aggregate_daily_features, derive_features


def load_scaling_stats(path):
    stats = pd.read_csv(path)
    return stats.set_index("feature").to_dict(orient="index")


def transform_with_stats(name, s, stats):
    s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    meta = stats[name]
    transform_type = meta["transform_type"]
    if transform_type == "log1p":
        t = np.log1p(s)
    elif transform_type == "signed_log1p":
        t = np.sign(s) * np.log1p(np.abs(s))
    elif transform_type == "raw":
        t = s
    else:
        raise ValueError(f"Unknown transform_type for {name}: {transform_type}")
    iqr = meta["iqr"]
    if pd.isna(iqr) or iqr == 0:
        return t - meta["median"]
    return (t - meta["median"]) / iqr


def scale_monthly_features(month_features, stats):
    out = month_features[["wallet"]].copy()
    feature_cols = [c for c in stats.keys() if c in month_features.columns]
    for col in feature_cols:
        out[col] = transform_with_stats(col, month_features[col], stats).astype("float32")
    return out, feature_cols


def nearest_centroid_assignments(month_scaled, centroids, feature_cols):
    X = month_scaled[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy(dtype=np.float32)
    C = centroids[feature_cols].to_numpy(dtype=np.float32)
    labels = centroids.index.to_numpy()

    dists = np.empty((len(X), len(C)), dtype=np.float32)
    for i, c in enumerate(C):
        diff = X - c
        dists[:, i] = np.sqrt(np.sum(diff * diff, axis=1))

    order = np.argsort(dists, axis=1)
    best_idx = order[:, 0]
    second_idx = order[:, 1]
    best_dist = dists[np.arange(len(X)), best_idx]
    second_dist = dists[np.arange(len(X)), second_idx]

    assigned = month_scaled[["wallet"]].copy()
    assigned["monthly_state"] = labels[best_idx].astype(int)
    assigned["nearest_distance"] = best_dist
    assigned["second_nearest_distance"] = second_dist
    assigned["assignment_margin"] = second_dist - best_dist
    assigned["assignment_margin_ratio"] = assigned["assignment_margin"] / assigned["second_nearest_distance"].replace(0, np.nan)
    return assigned


def plot_matrix(matrix, out_path, title, fmt=".2f"):
    plt.figure(figsize=(7, 5.8))
    data = matrix.to_numpy(dtype=float)
    plt.imshow(data, aspect="auto", cmap="viridis")
    plt.xticks(range(len(matrix.columns)), [f"C{c}" for c in matrix.columns])
    plt.yticks(range(len(matrix.index)), [f"C{c}" for c in matrix.index])
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if np.isfinite(val):
                plt.text(j, i, format(val, fmt), ha="center", va="center", color="white" if val < np.nanmax(data) * 0.65 else "black", fontsize=8)
    plt.xlabel("Next monthly behavior state")
    plt.ylabel("Current monthly behavior state")
    plt.title(title)
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def entropy(probs):
    p = np.asarray(probs, dtype=float)
    p = p[np.isfinite(p) & (p > 0)]
    if len(p) == 0:
        return 0.0
    return float(-(p * np.log2(p)).sum())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="dataverse_files")
    parser.add_argument("--cluster-file", default="dataverse_files/wallet_kmeans_clusters.csv")
    parser.add_argument("--expanded-scaled", default="dataverse_files/wallet_kmeans6_expanded_daily_features_robust_scaled.csv")
    parser.add_argument("--scaling-stats", default="dataverse_files/wallet_kmeans6_expanded_daily_features_robust_scaled_scaling_stats.csv")
    parser.add_argument("--out-dir", default="dataverse_files/cluster_transition_analysis_expanded")
    parser.add_argument("--months", default="202201,202202,202203,202204,202205,202206,202207,202208,202209,202210,202211,202212")
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(exist_ok=True)

    labels = read_labels(args.cluster_file)
    label_map = labels.set_index("wallet")["cluster"]
    stats = load_scaling_stats(args.scaling_stats)

    full_scaled = pd.read_csv(args.expanded_scaled, dtype={"wallet": str})
    feature_cols = [c for c in full_scaled.columns if c not in {"wallet", "cluster"} and c in stats]
    centroids = full_scaled.groupby("cluster")[feature_cols].median().sort_index()

    months = [m.strip() for m in args.months.split(",") if m.strip()]
    assignment_parts = []
    monthly_summary_rows = []

    for month in months:
        daily_file = data_dir / f"wallet_daily_{month}.csv"
        if not daily_file.exists():
            daily_file = data_dir / f"wallet_daily_clean_{month}.csv"
        if not daily_file.exists():
            raise FileNotFoundError(f"Missing monthly daily file for {month}")

        print(f"Processing monthly behavior state for {month}: {daily_file}")
        agg, total_rows, kept_rows = aggregate_daily_features(daily_file, labels, args.chunksize)
        month_features = derive_features(agg)
        month_scaled, scaled_cols = scale_monthly_features(month_features, stats)
        use_cols = [c for c in feature_cols if c in scaled_cols]
        assigned = nearest_centroid_assignments(month_scaled, centroids, use_cols)
        assigned["month"] = month
        assigned["full_year_cluster"] = assigned["wallet"].map(label_map).astype(int)
        assigned["matches_full_year_cluster"] = assigned["monthly_state"] == assigned["full_year_cluster"]

        state_counts = assigned["monthly_state"].value_counts(normalize=True).sort_index()
        monthly_summary_rows.append({
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
    monthly_summary = pd.DataFrame(monthly_summary_rows)
    monthly_summary.to_csv(out_dir / "monthly_behavior_state_summary.csv", index=False)

    transition_parts = []
    for prev_month, next_month in zip(months[:-1], months[1:]):
        prev = assignments[assignments["month"] == prev_month][["wallet", "monthly_state"]].rename(columns={"monthly_state": "from_state"})
        nxt = assignments[assignments["month"] == next_month][["wallet", "monthly_state"]].rename(columns={"monthly_state": "to_state"})
        merged = prev.merge(nxt, on="wallet", how="inner")
        counts = merged.groupby(["from_state", "to_state"]).size().reset_index(name="wallet_count")
        counts["from_month"] = prev_month
        counts["to_month"] = next_month
        transition_parts.append(counts)

    transitions = pd.concat(transition_parts, ignore_index=True)
    transitions.to_csv(out_dir / "monthly_state_transition_counts_long.csv", index=False)

    clusters = list(centroids.index)
    total_matrix = transitions.groupby(["from_state", "to_state"])["wallet_count"].sum().reset_index()
    count_matrix = total_matrix.pivot(index="from_state", columns="to_state", values="wallet_count").reindex(index=clusters, columns=clusters).fillna(0).astype(int)
    prob_matrix = count_matrix.div(count_matrix.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    count_matrix.to_csv(out_dir / "overall_transition_count_matrix.csv")
    prob_matrix.to_csv(out_dir / "overall_transition_probability_matrix.csv")

    plot_matrix(prob_matrix, fig_dir / "overall_transition_probability_matrix.png", "Overall Monthly Behavior-State Transition Probabilities")
    plot_matrix(np.log1p(count_matrix), fig_dir / "overall_transition_count_matrix_log.png", "Overall Monthly Behavior-State Transition Counts, log(1 + count)", fmt=".1f")

    pair_rows = []
    for (prev_month, next_month), sub in transitions.groupby(["from_month", "to_month"]):
        mat = sub.pivot(index="from_state", columns="to_state", values="wallet_count").reindex(index=clusters, columns=clusters).fillna(0)
        total = mat.to_numpy().sum()
        self_transitions = sum(mat.loc[c, c] for c in clusters)
        probs = mat.div(mat.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
        pair_rows.append({
            "from_month": prev_month,
            "to_month": next_month,
            "wallets_in_both_months": int(total),
            "self_transition_count": int(self_transitions),
            "self_transition_rate": self_transitions / total if total else np.nan,
            "mean_row_entropy_bits": np.mean([entropy(probs.loc[c].values) for c in clusters]),
        })
    transition_summary = pd.DataFrame(pair_rows)
    transition_summary.to_csv(out_dir / "monthly_transition_summary.csv", index=False)

    state_stability_rows = []
    for state in clusters:
        row = prob_matrix.loc[state]
        top_dest = row.sort_values(ascending=False).head(3)
        state_stability_rows.append({
            "from_state": state,
            "self_transition_probability": row.loc[state],
            "transition_entropy_bits": entropy(row.values),
            "top_destinations": "; ".join(f"C{idx}={val:.3f}" for idx, val in top_dest.items()),
        })
    state_stability = pd.DataFrame(state_stability_rows)
    state_stability.to_csv(out_dir / "state_transition_stability.csv", index=False)

    plt.figure(figsize=(10, 5.5))
    for c in clusters:
        plt.plot(monthly_summary["month"], monthly_summary[f"state_C{c}_share"], marker="o", label=f"C{c}")
    plt.xticks(rotation=45)
    plt.ylabel("Share of active wallets assigned to state")
    plt.xlabel("Month")
    plt.title("Monthly Behavioral State Composition")
    plt.legend(ncol=3)
    plt.tight_layout()
    plt.savefig(fig_dir / "monthly_behavior_state_composition.png", dpi=220)
    plt.close()

    plt.figure(figsize=(9, 4.8))
    plt.plot(transition_summary["from_month"] + "->" + transition_summary["to_month"], transition_summary["self_transition_rate"], marker="o")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Self-transition rate")
    plt.xlabel("Month pair")
    plt.title("Behavioral State Persistence Over Time")
    plt.tight_layout()
    plt.savefig(fig_dir / "monthly_self_transition_rate.png", dpi=220)
    plt.close()

    report = []
    report.append("# Transitional Analysis of Wallet Behavioral States\n")
    report.append("This analysis estimates dynamic behavioral-state transitions. Each wallet-month is assigned to the nearest full-year KMeans6 behavioral prototype in the expanded robust-scaled feature space. Month-to-month transitions are then treated as a Markov transition matrix.\n")
    report.append("## Mathematical Definition\n")
    report.append("For wallet `i` in month `t`, let `x_{i,t}` be its monthly expanded behavior vector after full-year robust scaling. Let `mu_k` be the median prototype of full-year cluster `C_k`. The monthly behavioral state is assigned by nearest centroid:\n")
    report.append("`s_{i,t} = argmin_k ||x_{i,t} - mu_k||_2`.\n")
    report.append("The transition probability from state `a` to state `b` is estimated as:\n")
    report.append("`P_ab = #{i: s_{i,t}=a and s_{i,t+1}=b} / #{i: s_{i,t}=a}`.\n")
    report.append("## Monthly State Summary\n")
    report.append(monthly_summary.to_markdown(index=False))
    report.append("\n## Overall Transition Probability Matrix\n")
    report.append(prob_matrix.to_markdown())
    report.append("\n## State Stability\n")
    report.append(state_stability.to_markdown(index=False))
    report.append("\n## Monthly Transition Summary\n")
    report.append(transition_summary.to_markdown(index=False))
    report.append("\n## Interpretation\n")
    report.append("High diagonal probabilities imply persistent behavioral roles. Large off-diagonal probabilities identify transitional pathways, meaning wallets that change their monthly behavior from one prototype to another. This complements the static cluster analysis by showing whether clusters are stable roles or temporary states.")
    (out_dir / "transitional_analysis_report.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Saved transition analysis to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
