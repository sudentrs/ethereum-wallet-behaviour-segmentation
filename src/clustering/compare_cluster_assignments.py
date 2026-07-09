import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment

# =========================================================
# SETTINGS
# =========================================================
CLUSTER_1_PROFILE_FILE = "cluster_1_profiles_202209.csv"
CLUSTER_2_PROFILE_FILE = "cluster_2_profiles_202209.csv"

CLUSTER_1_SIZES_FILE = "cluster_1_sizes_202209.csv"   # optional, only for reference if needed
CLUSTER_2_SIZES_FILE = "cluster_2_sizes_202209.csv"   # optional, only for reference if needed

DIST_MATRIX_FILE = "cluster_centroid_distance_matrix_202209.csv"
MATCHING_FILE = "cluster_matching_results_202209.csv"
FEATURE_DIFF_FILE = "matched_cluster_feature_differences_202209.csv"

DIST_HEATMAP_FILE = "centroid_distance_heatmap_202209.png"
PROFILE_HEATMAP_1_FILE = "cluster_1_profile_heatmap_202209.png"
PROFILE_HEATMAP_2_FILE = "cluster_2_profile_heatmap_202209.png"

CLUSTER_1_COL = "cluster_1"
CLUSTER_2_COL = "cluster_2"

TOP_N_DIFFERENT = 8
TOP_N_SIMILAR = 8

# =========================================================
# LOAD
# =========================================================
print("Loading profile tables...")

c1 = pd.read_csv(CLUSTER_1_PROFILE_FILE)
c2 = pd.read_csv(CLUSTER_2_PROFILE_FILE)

feature_cols_1 = [c for c in c1.columns if c != CLUSTER_1_COL]
feature_cols_2 = [c for c in c2.columns if c != CLUSTER_2_COL]

if feature_cols_1 != feature_cols_2:
    raise ValueError("Feature columns do not match between cluster_1 and cluster_2 profile tables.")

feature_cols = feature_cols_1

print(f"Feature count: {len(feature_cols)}")
print(f"cluster_1 clusters: {len(c1)}")
print(f"cluster_2 clusters: {len(c2)}")

# =========================================================
# MATRICES
# =========================================================
X1 = c1[feature_cols].to_numpy(dtype=float)
X2 = c2[feature_cols].to_numpy(dtype=float)

cluster1_ids = c1[CLUSTER_1_COL].tolist()
cluster2_ids = c2[CLUSTER_2_COL].tolist()

# =========================================================
# DISTANCE MATRIX
# =========================================================
print("\nComputing Euclidean distance matrix...")
dist_matrix = cdist(X1, X2, metric="euclidean")

dist_df = pd.DataFrame(
    dist_matrix,
    index=[f"cluster_1_{cid}" for cid in cluster1_ids],
    columns=[f"cluster_2_{cid}" for cid in cluster2_ids]
)

dist_df.to_csv(DIST_MATRIX_FILE)
print(f"Saved: {DIST_MATRIX_FILE}")

# =========================================================
# HUNGARIAN MATCHING
# =========================================================
print("\nRunning Hungarian matching...")
row_ind, col_ind = linear_sum_assignment(dist_matrix)

match_rows = []
matched_c1 = set()
matched_c2 = set()

for r, c in zip(row_ind, col_ind):
    match_rows.append({
        "cluster_1": cluster1_ids[r],
        "cluster_2": cluster2_ids[c],
        "distance": float(dist_matrix[r, c])
    })
    matched_c1.add(cluster1_ids[r])
    matched_c2.add(cluster2_ids[c])

match_df = pd.DataFrame(match_rows).sort_values("distance").reset_index(drop=True)
match_df.to_csv(MATCHING_FILE, index=False)
print(f"Saved: {MATCHING_FILE}")

unmatched_c1 = [cid for cid in cluster1_ids if cid not in matched_c1]
unmatched_c2 = [cid for cid in cluster2_ids if cid not in matched_c2]

print("\nBest matches:")
print(match_df)

print("\nUnmatched cluster_1 clusters:", unmatched_c1)
print("Unmatched cluster_2 clusters:", unmatched_c2)

# =========================================================
# FEATURE DIFFERENCE ANALYSIS FOR MATCHED PAIRS
# =========================================================
print("\nAnalyzing feature-level similarities and differences for matched pairs...")

c1_indexed = c1.set_index(CLUSTER_1_COL)
c2_indexed = c2.set_index(CLUSTER_2_COL)

feature_diff_rows = []

for _, row in match_df.iterrows():
    c1_id = row["cluster_1"]
    c2_id = row["cluster_2"]
    pair_distance = row["distance"]

    v1 = c1_indexed.loc[c1_id, feature_cols].astype(float)
    v2 = c2_indexed.loc[c2_id, feature_cols].astype(float)

    diff = (v1 - v2).abs()
    signed_diff = v1 - v2

    diff_df = pd.DataFrame({
        "feature": feature_cols,
        "cluster_1_value": v1.values,
        "cluster_2_value": v2.values,
        "signed_difference": signed_diff.values,
        "absolute_difference": diff.values
    }).sort_values("absolute_difference", ascending=False).reset_index(drop=True)

    # En farklı feature'lar
    top_diff = diff_df.head(TOP_N_DIFFERENT).copy()
    top_diff["rank_type"] = "most_different"
    top_diff["rank"] = np.arange(1, len(top_diff) + 1)
    top_diff["cluster_1"] = c1_id
    top_diff["cluster_2"] = c2_id
    top_diff["pair_distance"] = pair_distance

    # En benzer feature'lar
    top_sim = diff_df.sort_values("absolute_difference", ascending=True).head(TOP_N_SIMILAR).copy()
    top_sim["rank_type"] = "most_similar"
    top_sim["rank"] = np.arange(1, len(top_sim) + 1)
    top_sim["cluster_1"] = c1_id
    top_sim["cluster_2"] = c2_id
    top_sim["pair_distance"] = pair_distance

    feature_diff_rows.append(top_diff)
    feature_diff_rows.append(top_sim)

feature_diff_all = pd.concat(feature_diff_rows, ignore_index=True)

feature_diff_all = feature_diff_all[
    [
        "cluster_1", "cluster_2", "pair_distance",
        "rank_type", "rank", "feature",
        "cluster_1_value", "cluster_2_value",
        "signed_difference", "absolute_difference"
    ]
]

feature_diff_all.to_csv(FEATURE_DIFF_FILE, index=False)
print(f"Saved: {FEATURE_DIFF_FILE}")

# =========================================================
# HEATMAP: CENTROID DISTANCE MATRIX
# =========================================================
print("\nDrawing centroid distance heatmap...")

plt.figure(figsize=(10, 6))
plt.imshow(dist_matrix, aspect="auto")
plt.colorbar(label="Euclidean Distance")
plt.xticks(
    ticks=np.arange(len(cluster2_ids)),
    labels=[f"c2_{cid}" for cid in cluster2_ids],
    rotation=45
)
plt.yticks(
    ticks=np.arange(len(cluster1_ids)),
    labels=[f"c1_{cid}" for cid in cluster1_ids]
)
plt.title("Centroid Distance Heatmap")
plt.xlabel("cluster_2")
plt.ylabel("cluster_1")
plt.tight_layout()
plt.savefig(DIST_HEATMAP_FILE, dpi=300, bbox_inches="tight")
plt.close()

print(f"Saved: {DIST_HEATMAP_FILE}")

# =========================================================
# HEATMAP: PROFILE TABLES
# =========================================================
print("\nDrawing profile heatmaps...")

def save_profile_heatmap(df, cluster_col, out_file, title):
    plot_df = df.set_index(cluster_col)[feature_cols]

    plt.figure(figsize=(16, max(4, len(plot_df) * 0.8)))
    plt.imshow(plot_df.to_numpy(dtype=float), aspect="auto")
    plt.colorbar(label="Scaled Feature Value")
    plt.xticks(
        ticks=np.arange(len(feature_cols)),
        labels=feature_cols,
        rotation=90
    )
    plt.yticks(
        ticks=np.arange(len(plot_df.index)),
        labels=[f"{cluster_col}_{idx}" for idx in plot_df.index]
    )
    plt.title(title)
    plt.xlabel("Features")
    plt.ylabel("Clusters")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()

save_profile_heatmap(
    c1,
    CLUSTER_1_COL,
    PROFILE_HEATMAP_1_FILE,
    "cluster_1 Profile Heatmap"
)

save_profile_heatmap(
    c2,
    CLUSTER_2_COL,
    PROFILE_HEATMAP_2_FILE,
    "cluster_2 Profile Heatmap"
)

print(f"Saved: {PROFILE_HEATMAP_1_FILE}")
print(f"Saved: {PROFILE_HEATMAP_2_FILE}")

# =========================================================
# CONSOLE SUMMARY
# =========================================================
print("\n==============================")
print("MATCHED PAIR SUMMARY")
print("==============================")

for _, row in match_df.iterrows():
    c1_id = row["cluster_1"]
    c2_id = row["cluster_2"]
    dist_val = row["distance"]

    print(f"\nPair: cluster_1={c1_id} <-> cluster_2={c2_id} | distance={dist_val:.4f}")

    pair_rows = feature_diff_all[
        (feature_diff_all["cluster_1"] == c1_id) &
        (feature_diff_all["cluster_2"] == c2_id)
    ]

    print("  Most different features:")
    sub_diff = pair_rows[pair_rows["rank_type"] == "most_different"].sort_values("rank")
    for _, r in sub_diff.iterrows():
        print(
            f"    {int(r['rank'])}. {r['feature']} | "
            f"c1={r['cluster_1_value']:.4f}, c2={r['cluster_2_value']:.4f}, "
            f"|diff|={r['absolute_difference']:.4f}"
        )

    print("  Most similar features:")
    sub_sim = pair_rows[pair_rows["rank_type"] == "most_similar"].sort_values("rank")
    for _, r in sub_sim.iterrows():
        print(
            f"    {int(r['rank'])}. {r['feature']} | "
            f"c1={r['cluster_1_value']:.4f}, c2={r['cluster_2_value']:.4f}, "
            f"|diff|={r['absolute_difference']:.4f}"
        )

print("\nDONE")
print("\nGenerated files:")
print(f"- {DIST_MATRIX_FILE}")
print(f"- {MATCHING_FILE}")
print(f"- {FEATURE_DIFF_FILE}")
print(f"- {DIST_HEATMAP_FILE}")
print(f"- {PROFILE_HEATMAP_1_FILE}")
print(f"- {PROFILE_HEATMAP_2_FILE}")