import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from scipy.stats import wasserstein_distance
from sklearn.covariance import LedoitWolf

warnings.filterwarnings("ignore")

# =========================================================
# CONFIG
# =========================================================

PROFILE_1_PATH = "cluster_1_profiles_202209.csv"
PROFILE_2_PATH = "cluster_2_profiles_202209.csv"

# Optional member-level datasets for Wasserstein
MEMBERS_1_PATH = "cluster_1_members_202209.csv"
MEMBERS_2_PATH = "cluster_2_members_202209.csv"

CLUSTER1_ID_COL = "cluster_1"
CLUSTER2_ID_COL = "cluster_2"

OUTPUT_DIR = "distance_comparison_results_202209_corrected"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FEATURE_COLS = None

THRESHOLDS = {
    "weighted_euclidean": None,
    "cosine": None,
    "mahalanobis": None,
    "wasserstein": None
}

FEATURE_GROUPS = {
    "activity": [
        "active_days_observed", "activity_span_days", "activity_density",
        "total_tx", "avg_daily_tx_count", "max_daily_tx_count", "std_daily_tx_count"
    ],
    "volume": [
        "total_in_sum", "total_out_sum", "total_net_flow_sum", "total_flow_sum",
        "avg_daily_total_in", "avg_daily_total_out", "avg_daily_net_flow", "avg_daily_total_flow",
        "max_daily_total_in", "max_daily_total_out", "max_daily_total_flow",
        "std_daily_total_in", "std_daily_total_out", "std_daily_net_flow", "std_daily_total_flow"
    ],
    "participation": [
        "in_active_days", "out_active_days", "both_active_days",
        "in_active_day_ratio", "out_active_day_ratio", "both_active_day_ratio",
        "in_out_day_balance"
    ],
    "concentration": [
        "tx_count_cv", "total_flow_cv", "tx_concentration_ratio", "flow_concentration_ratio"
    ]
}

GROUP_WEIGHTS = {
    "activity": 0.30,
    "volume": 0.30,
    "participation": 0.20,
    "concentration": 0.20
}

# =========================================================
# HELPERS
# =========================================================

def load_profiles():
    df1 = pd.read_csv(PROFILE_1_PATH)
    df2 = pd.read_csv(PROFILE_2_PATH)

    if CLUSTER1_ID_COL not in df1.columns:
        raise ValueError(f"{CLUSTER1_ID_COL} not found in {PROFILE_1_PATH}")
    if CLUSTER2_ID_COL not in df2.columns:
        raise ValueError(f"{CLUSTER2_ID_COL} not found in {PROFILE_2_PATH}")

    return df1, df2

def detect_common_features(df1, df2):
    if FEATURE_COLS is not None:
        return FEATURE_COLS

    num1 = set(df1.select_dtypes(include=[np.number]).columns)
    num2 = set(df2.select_dtypes(include=[np.number]).columns)

    common = sorted(list((num1 & num2) - {CLUSTER1_ID_COL, CLUSTER2_ID_COL}))
    if not common:
        raise ValueError("No common numeric features found.")
    return common

def get_feature_groups(features):
    usable = {}
    assigned = set()

    for group_name, group_feats in FEATURE_GROUPS.items():
        existing = [f for f in group_feats if f in features]
        if existing:
            usable[group_name] = existing
            assigned.update(existing)

    leftover = [f for f in features if f not in assigned]
    if leftover:
        usable["other"] = leftover

    used_weights = {g: GROUP_WEIGHTS.get(g, 0.0) for g in usable.keys()}

    if "other" in usable and used_weights.get("other", 0.0) == 0:
        used_weights["other"] = 0.10

    total_w = sum(used_weights.values())
    if total_w == 0:
        eq = 1.0 / len(usable)
        used_weights = {g: eq for g in usable.keys()}
    else:
        used_weights = {g: w / total_w for g, w in used_weights.items()}

    return usable, used_weights

def weighted_euclidean_matrix(df1, df2, features):
    groups, group_weights = get_feature_groups(features)

    X = df1[features].to_numpy(dtype=float)
    Y = df2[features].to_numpy(dtype=float)

    D = np.zeros((len(df1), len(df2)), dtype=float)

    for group_name, group_feats in groups.items():
        idx = [features.index(f) for f in group_feats]
        Xg = X[:, idx]
        Yg = Y[:, idx]
        Dg = cdist(Xg, Yg, metric="euclidean")
        D += group_weights[group_name] * Dg

    return D

def cosine_distance_matrix(df1, df2, features):
    X = df1[features].to_numpy(dtype=float)
    Y = df2[features].to_numpy(dtype=float)
    return cdist(X, Y, metric="cosine")

def regularized_mahalanobis_matrix(df1, df2, features):
    X = df1[features].to_numpy(dtype=float)
    Y = df2[features].to_numpy(dtype=float)
    Z = np.vstack([X, Y])

    lw = LedoitWolf()
    lw.fit(Z)
    VI = lw.precision_

    return cdist(X, Y, metric="mahalanobis", VI=VI)

def centroid_wasserstein_matrix(df1, df2, features):
    X = df1[features].to_numpy(dtype=float)
    Y = df2[features].to_numpy(dtype=float)

    D = np.zeros((len(df1), len(df2)), dtype=float)
    for i in range(len(df1)):
        for j in range(len(df2)):
            D[i, j] = wasserstein_distance(X[i], Y[j])
    return D

def member_level_wasserstein_matrix(m1, m2, features, c1_col, c2_col):
    c1_vals = sorted(m1[c1_col].dropna().unique())
    c2_vals = sorted(m2[c2_col].dropna().unique())

    D = np.zeros((len(c1_vals), len(c2_vals)), dtype=float)

    for i, c1 in enumerate(c1_vals):
        sub1 = m1[m1[c1_col] == c1]
        for j, c2 in enumerate(c2_vals):
            sub2 = m2[m2[c2_col] == c2]

            d_list = []
            for f in features:
                a = sub1[f].dropna().to_numpy(dtype=float)
                b = sub2[f].dropna().to_numpy(dtype=float)
                if len(a) == 0 or len(b) == 0:
                    continue
                d_list.append(wasserstein_distance(a, b))

            D[i, j] = np.mean(d_list) if d_list else np.nan

    return pd.DataFrame(D, index=c1_vals, columns=c2_vals)

def hungarian_match(distance_df, metric_name, threshold=None):
    D = distance_df.values.copy()

    finite_mask = np.isfinite(D)
    if not finite_mask.any():
        raise ValueError(f"All distances are non-finite for metric: {metric_name}")

    max_finite = np.nanmax(D[finite_mask])
    D[~finite_mask] = max_finite * 10 if np.isfinite(max_finite) else 1e6

    row_ind, col_ind = linear_sum_assignment(D)

    matches = []
    matched_rows = set()
    matched_cols = set()

    for r, c in zip(row_ind, col_ind):
        dist_val = distance_df.iloc[r, c]
        keep = True if threshold is None else (dist_val <= threshold)

        if keep:
            matches.append({
                "cluster_1": distance_df.index[r],
                "cluster_2": distance_df.columns[c],
                "distance": dist_val,
                "metric": metric_name,
                "status": "matched"
            })
            matched_rows.add(distance_df.index[r])
            matched_cols.add(distance_df.columns[c])

    unmatched_rows = [x for x in distance_df.index if x not in matched_rows]
    unmatched_cols = [x for x in distance_df.columns if x not in matched_cols]

    for r in unmatched_rows:
        matches.append({
            "cluster_1": r,
            "cluster_2": np.nan,
            "distance": np.nan,
            "metric": metric_name,
            "status": "unmatched_cluster_1"
        })

    for c in unmatched_cols:
        matches.append({
            "cluster_1": np.nan,
            "cluster_2": c,
            "distance": np.nan,
            "metric": metric_name,
            "status": "unmatched_cluster_2"
        })

    return pd.DataFrame(matches)

def summarize_pair_feature_diffs(df1, df2, features, match_df, metric_name, top_n=8):
    matched = match_df[match_df["status"] == "matched"].copy()
    rows = []

    idx1 = {row[CLUSTER1_ID_COL]: row for _, row in df1.iterrows()}
    idx2 = {row[CLUSTER2_ID_COL]: row for _, row in df2.iterrows()}

    for _, m in matched.iterrows():
        c1 = m["cluster_1"]
        c2 = m["cluster_2"]

        r1 = idx1[c1]
        r2 = idx2[c2]

        diffs = []
        for f in features:
            v1 = r1[f]
            v2 = r2[f]
            diffs.append((f, v1, v2, abs(v1 - v2)))

        diffs_sorted = sorted(diffs, key=lambda x: x[3], reverse=True)
        top_diff = diffs_sorted[:top_n]
        top_sim = sorted(diffs, key=lambda x: x[3])[:top_n]

        for rank, (f, v1, v2, d) in enumerate(top_diff, start=1):
            rows.append({
                "metric": metric_name,
                "cluster_1": c1,
                "cluster_2": c2,
                "pair_distance": m["distance"],
                "type": "most_different",
                "rank": rank,
                "feature": f,
                "cluster_1_value": v1,
                "cluster_2_value": v2,
                "abs_diff": d
            })

        for rank, (f, v1, v2, d) in enumerate(top_sim, start=1):
            rows.append({
                "metric": metric_name,
                "cluster_1": c1,
                "cluster_2": c2,
                "pair_distance": m["distance"],
                "type": "most_similar",
                "rank": rank,
                "feature": f,
                "cluster_1_value": v1,
                "cluster_2_value": v2,
                "abs_diff": d
            })

    return pd.DataFrame(rows)

def draw_heatmap(distance_df, title, save_path):
    plt.figure(figsize=(10, 6))
    plt.imshow(distance_df.values, aspect="auto")
    plt.colorbar(label="Distance")
    plt.xticks(range(len(distance_df.columns)), distance_df.columns, rotation=45)
    plt.yticks(range(len(distance_df.index)), distance_df.index)
    plt.title(title)
    plt.xlabel("cluster_2")
    plt.ylabel("cluster_1")
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()

def draw_profile_heatmap(df, cluster_col, features, title, save_path):
    plt.figure(figsize=(max(12, len(features) * 0.45), max(4, len(df) * 0.6)))
    plt.imshow(df[features].to_numpy(dtype=float), aspect="auto")
    plt.colorbar(label="Feature Value")
    plt.xticks(range(len(features)), features, rotation=90)
    plt.yticks(range(len(df)), [f"{cluster_col}_{x}" for x in df[cluster_col].tolist()])
    plt.title(title)
    plt.xlabel("Features")
    plt.ylabel("Clusters")
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()

def save_distance_outputs(distance_df, metric_name):
    csv_path = os.path.join(OUTPUT_DIR, f"{metric_name}_distance_matrix_202209.csv")
    png_path = os.path.join(OUTPUT_DIR, f"{metric_name}_distance_heatmap_202209.png")

    distance_df.to_csv(csv_path)
    draw_heatmap(distance_df, f"{metric_name} Distance Heatmap", png_path)

def print_match_summary(match_df, metric_name):
    print("\n" + "=" * 70)
    print(f"{metric_name.upper()} MATCH SUMMARY")
    print("=" * 70)

    matched = match_df[match_df["status"] == "matched"].copy()
    if len(matched) == 0:
        print("No matched pairs under threshold.")
    else:
        for _, row in matched.sort_values("distance").iterrows():
            print(f"cluster_1={row['cluster_1']} <-> cluster_2={row['cluster_2']} | distance={row['distance']:.6f}")

    u1 = match_df[match_df["status"] == "unmatched_cluster_1"]["cluster_1"].dropna().tolist()
    u2 = match_df[match_df["status"] == "unmatched_cluster_2"]["cluster_2"].dropna().tolist()

    print(f"Unmatched cluster_1: {u1}")
    print(f"Unmatched cluster_2: {u2}")

# =========================================================
# MAIN
# =========================================================

def main():
    print("Loading profiles...")
    df1, df2 = load_profiles()

    features = detect_common_features(df1, df2)
    print(f"Detected {len(features)} common numeric features.")

    # IMPORTANT:
    # Profiles are assumed to already be transformed/scaled correctly upstream.
    # No extra StandardScaler / joint normalization is applied here.
    df1_used = df1.copy()
    df2_used = df2.copy()

    # Save copies actually used in analysis
    df1_used.to_csv(os.path.join(OUTPUT_DIR, "cluster1_profile_used_202209.csv"), index=False)
    df2_used.to_csv(os.path.join(OUTPUT_DIR, "cluster2_profile_used_202209.csv"), index=False)

    draw_profile_heatmap(
        df1_used, CLUSTER1_ID_COL, features,
        "cluster_1 Profile Heatmap",
        os.path.join(OUTPUT_DIR, "cluster1_profile_heatmap_202209.png")
    )
    draw_profile_heatmap(
        df2_used, CLUSTER2_ID_COL, features,
        "cluster_2 Profile Heatmap",
        os.path.join(OUTPUT_DIR, "cluster2_profile_heatmap_202209.png")
    )

    all_match_results = []
    all_feature_diffs = []

    print("Computing weighted Euclidean...")
    D_we = weighted_euclidean_matrix(df1_used, df2_used, features)
    dist_we = pd.DataFrame(
        D_we,
        index=df1_used[CLUSTER1_ID_COL].tolist(),
        columns=df2_used[CLUSTER2_ID_COL].tolist()
    )
    save_distance_outputs(dist_we, "weighted_euclidean")
    match_we = hungarian_match(dist_we, "weighted_euclidean", THRESHOLDS["weighted_euclidean"])
    match_we.to_csv(os.path.join(OUTPUT_DIR, "weighted_euclidean_matches_202209.csv"), index=False)
    all_match_results.append(match_we)
    all_feature_diffs.append(
        summarize_pair_feature_diffs(df1_used, df2_used, features, match_we, "weighted_euclidean")
    )
    print_match_summary(match_we, "weighted_euclidean")

    print("Computing cosine distance...")
    D_cos = cosine_distance_matrix(df1_used, df2_used, features)
    dist_cos = pd.DataFrame(
        D_cos,
        index=df1_used[CLUSTER1_ID_COL].tolist(),
        columns=df2_used[CLUSTER2_ID_COL].tolist()
    )
    save_distance_outputs(dist_cos, "cosine")
    match_cos = hungarian_match(dist_cos, "cosine", THRESHOLDS["cosine"])
    match_cos.to_csv(os.path.join(OUTPUT_DIR, "cosine_matches_202209.csv"), index=False)
    all_match_results.append(match_cos)
    all_feature_diffs.append(
        summarize_pair_feature_diffs(df1_used, df2_used, features, match_cos, "cosine")
    )
    print_match_summary(match_cos, "cosine")

    print("Computing regularized Mahalanobis...")
    D_mah = regularized_mahalanobis_matrix(df1_used, df2_used, features)
    dist_mah = pd.DataFrame(
        D_mah,
        index=df1_used[CLUSTER1_ID_COL].tolist(),
        columns=df2_used[CLUSTER2_ID_COL].tolist()
    )
    save_distance_outputs(dist_mah, "mahalanobis")
    match_mah = hungarian_match(dist_mah, "mahalanobis", THRESHOLDS["mahalanobis"])
    match_mah.to_csv(os.path.join(OUTPUT_DIR, "mahalanobis_matches_202209.csv"), index=False)
    all_match_results.append(match_mah)
    all_feature_diffs.append(
        summarize_pair_feature_diffs(df1_used, df2_used, features, match_mah, "mahalanobis")
    )
    print_match_summary(match_mah, "mahalanobis")

    if os.path.exists(MEMBERS_1_PATH) and os.path.exists(MEMBERS_2_PATH):
        print("Computing member-level Wasserstein...")
        m1 = pd.read_csv(MEMBERS_1_PATH)
        m2 = pd.read_csv(MEMBERS_2_PATH)

        if CLUSTER1_ID_COL not in m1.columns:
            raise ValueError(f"{CLUSTER1_ID_COL} not found in {MEMBERS_1_PATH}")
        if CLUSTER2_ID_COL not in m2.columns:
            raise ValueError(f"{CLUSTER2_ID_COL} not found in {MEMBERS_2_PATH}")

        member_common = sorted(list(
            (set(m1.select_dtypes(include=[np.number]).columns) &
             set(m2.select_dtypes(include=[np.number]).columns))
            - {CLUSTER1_ID_COL, CLUSTER2_ID_COL}
        ))

        if not member_common:
            raise ValueError("No common numeric member-level features found for Wasserstein.")

        # IMPORTANT:
        # Member-level data is assumed to already be transformed/scaled correctly upstream.
        # No extra StandardScaler is applied here.
        dist_wass = member_level_wasserstein_matrix(
            m1, m2, member_common, CLUSTER1_ID_COL, CLUSTER2_ID_COL
        )
    else:
        print("Member-level files not found. Falling back to centroid-level Wasserstein...")
        D_wass = centroid_wasserstein_matrix(df1_used, df2_used, features)
        dist_wass = pd.DataFrame(
            D_wass,
            index=df1_used[CLUSTER1_ID_COL].tolist(),
            columns=df2_used[CLUSTER2_ID_COL].tolist()
        )

    save_distance_outputs(dist_wass, "wasserstein")
    match_wass = hungarian_match(dist_wass, "wasserstein", THRESHOLDS["wasserstein"])
    match_wass.to_csv(os.path.join(OUTPUT_DIR, "wasserstein_matches_202209.csv"), index=False)
    all_match_results.append(match_wass)

    try:
        all_feature_diffs.append(
            summarize_pair_feature_diffs(df1_used, df2_used, features, match_wass, "wasserstein")
        )
    except Exception:
        pass

    print_match_summary(match_wass, "wasserstein")

    combined_matches = pd.concat(all_match_results, ignore_index=True)
    combined_matches.to_csv(os.path.join(OUTPUT_DIR, "all_metric_matches_combined_202209.csv"), index=False)

    if all_feature_diffs:
        combined_diffs = pd.concat(all_feature_diffs, ignore_index=True)
        combined_diffs.to_csv(os.path.join(OUTPUT_DIR, "all_metric_feature_differences_202209.csv"), index=False)

    summary_rows = []
    for metric_name, mdf in combined_matches.groupby("metric"):
        matched = mdf[mdf["status"] == "matched"].copy()
        if len(matched) > 0:
            summary_rows.append({
                "metric": metric_name,
                "matched_pair_count": len(matched),
                "mean_distance": matched["distance"].mean(),
                "min_distance": matched["distance"].min(),
                "max_distance": matched["distance"].max()
            })
        else:
            summary_rows.append({
                "metric": metric_name,
                "matched_pair_count": 0,
                "mean_distance": np.nan,
                "min_distance": np.nan,
                "max_distance": np.nan
            })

    pd.DataFrame(summary_rows).to_csv(
        os.path.join(OUTPUT_DIR, "metric_summary_202209.csv"),
        index=False
    )

    print("\nDONE.")
    print(f"All outputs saved under: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()