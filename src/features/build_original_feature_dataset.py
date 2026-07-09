import pandas as pd
import numpy as np


# =========================
# 1. FILE PATHS
# =========================
DAILY_COMMON_PATH = "wallet_daily_common_202209.csv"
CLUSTER1_COMMON_PATH = "wallet_kmeans_clusters_common_202209.csv"
CLUSTER2_COMMON_PATH = "202209_interval_clustered_common_202209.csv"

OUTPUT_EVAL_FEATURES = "wallet_evaluation_features_chunked_202209.csv"
OUTPUT_EVAL_WITH_LABELS = "wallet_evaluation_features_with_labels_chunked_202209.csv"

CHUNK_SIZE = 1_000_000


# =========================
# 2. HELPER FUNCTIONS
# =========================
def clean_wallet_series(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def safe_divide(numerator, denominator):
    result = numerator / denominator
    if isinstance(result, pd.Series):
        result = result.replace([np.inf, -np.inf], np.nan).fillna(0)
    elif pd.isna(result) or np.isinf(result):
        result = 0
    return result


# =========================
# 3. LOAD CLUSTER LABELS
# =========================
cluster1 = pd.read_csv(CLUSTER1_COMMON_PATH, dtype={"wallet": str})
cluster2 = pd.read_csv(CLUSTER2_COMMON_PATH, dtype={"wallet": str})

cluster1["wallet"] = clean_wallet_series(cluster1["wallet"])
cluster2["wallet"] = clean_wallet_series(cluster2["wallet"])

cluster1 = cluster1[["wallet", "cluster"]].rename(columns={"cluster": "cluster_1"}).drop_duplicates()
cluster2 = cluster2[["wallet", "cluster"]].rename(columns={"cluster": "cluster_2"}).drop_duplicates()

wallet_universe = set(cluster1["wallet"]).intersection(set(cluster2["wallet"]))

print("\nLABEL FILES LOADED")
print("------------------")
print(f"Cluster1 wallets: {cluster1['wallet'].nunique():,}")
print(f"Cluster2 wallets: {cluster2['wallet'].nunique():,}")
print(f"Wallet universe : {len(wallet_universe):,}")


# =========================
# 4. CHUNKED AGGREGATION
# =========================
# We accumulate per-wallet sufficient statistics
agg_parts = []
chunk_count = 0
total_rows_read = 0

print("\nReading daily data in chunks...")
print("--------------------------------")

for chunk in pd.read_csv(
    DAILY_COMMON_PATH,
    dtype={"wallet": str},
    chunksize=CHUNK_SIZE
):
    chunk_count += 1
    total_rows_read += len(chunk)

    required_cols = ["wallet", "date", "total_in", "total_out", "tx_count"]
    missing = [c for c in required_cols if c not in chunk.columns]
    if missing:
        raise ValueError(f"Daily file missing columns: {missing}")

    chunk["wallet"] = clean_wallet_series(chunk["wallet"])
    chunk = chunk[chunk["wallet"].isin(wallet_universe)].copy()

    chunk["date"] = pd.to_datetime(chunk["date"], errors="coerce")
    if chunk["date"].isna().any():
        raise ValueError(f"Chunk {chunk_count} contains unparseable dates.")

    chunk["tx_count"] = pd.to_numeric(chunk["tx_count"], errors="coerce").fillna(0.0)
    chunk["total_in"] = pd.to_numeric(chunk["total_in"], errors="coerce").fillna(0.0)
    chunk["total_out"] = pd.to_numeric(chunk["total_out"], errors="coerce").fillna(0.0)

    chunk["net_flow"] = chunk["total_in"] - chunk["total_out"]
    chunk["total_flow"] = chunk["total_in"] + chunk["total_out"]

    chunk["in_active"] = (chunk["total_in"] > 0).astype(int)
    chunk["out_active"] = (chunk["total_out"] > 0).astype(int)
    chunk["both_active"] = ((chunk["total_in"] > 0) & (chunk["total_out"] > 0)).astype(int)

    # Squares for variance/std reconstruction
    chunk["tx_count_sq"] = chunk["tx_count"] ** 2
    chunk["total_in_sq"] = chunk["total_in"] ** 2
    chunk["total_out_sq"] = chunk["total_out"] ** 2
    chunk["net_flow_sq"] = chunk["net_flow"] ** 2
    chunk["total_flow_sq"] = chunk["total_flow"] ** 2

    grouped = chunk.groupby("wallet").agg(
        active_days_observed=("date", "count"),
        first_active_date=("date", "min"),
        last_active_date=("date", "max"),

        total_tx=("tx_count", "sum"),
        total_in_sum=("total_in", "sum"),
        total_out_sum=("total_out", "sum"),
        total_net_flow_sum=("net_flow", "sum"),
        total_flow_sum=("total_flow", "sum"),

        max_daily_tx_count=("tx_count", "max"),
        max_daily_total_in=("total_in", "max"),
        max_daily_total_out=("total_out", "max"),
        max_daily_total_flow=("total_flow", "max"),

        tx_count_sq_sum=("tx_count_sq", "sum"),
        total_in_sq_sum=("total_in_sq", "sum"),
        total_out_sq_sum=("total_out_sq", "sum"),
        net_flow_sq_sum=("net_flow_sq", "sum"),
        total_flow_sq_sum=("total_flow_sq", "sum"),

        in_active_days=("in_active", "sum"),
        out_active_days=("out_active", "sum"),
        both_active_days=("both_active", "sum"),
    ).reset_index()

    agg_parts.append(grouped)

    print(
        f"Chunk {chunk_count:>3} processed | "
        f"rows read: {total_rows_read:>10,} | "
        f"wallets in chunk aggregate: {len(grouped):>8,}"
    )


print("\nCombining chunk-level aggregates...")
print("-----------------------------------")

combined = pd.concat(agg_parts, ignore_index=True)

wallet_agg = combined.groupby("wallet").agg(
    active_days_observed=("active_days_observed", "sum"),
    first_active_date=("first_active_date", "min"),
    last_active_date=("last_active_date", "max"),

    total_tx=("total_tx", "sum"),
    total_in_sum=("total_in_sum", "sum"),
    total_out_sum=("total_out_sum", "sum"),
    total_net_flow_sum=("total_net_flow_sum", "sum"),
    total_flow_sum=("total_flow_sum", "sum"),

    max_daily_tx_count=("max_daily_tx_count", "max"),
    max_daily_total_in=("max_daily_total_in", "max"),
    max_daily_total_out=("max_daily_total_out", "max"),
    max_daily_total_flow=("max_daily_total_flow", "max"),

    tx_count_sq_sum=("tx_count_sq_sum", "sum"),
    total_in_sq_sum=("total_in_sq_sum", "sum"),
    total_out_sq_sum=("total_out_sq_sum", "sum"),
    net_flow_sq_sum=("net_flow_sq_sum", "sum"),
    total_flow_sq_sum=("total_flow_sq_sum", "sum"),

    in_active_days=("in_active_days", "sum"),
    out_active_days=("out_active_days", "sum"),
    both_active_days=("both_active_days", "sum"),
).reset_index()


# =========================
# 5. DERIVE FINAL FEATURES
# =========================
wallet_agg["activity_span_days"] = (
    wallet_agg["last_active_date"] - wallet_agg["first_active_date"]
).dt.days + 1

wallet_agg["activity_density"] = safe_divide(
    wallet_agg["active_days_observed"],
    wallet_agg["activity_span_days"]
)

# Means
wallet_agg["avg_daily_tx_count"] = safe_divide(
    wallet_agg["total_tx"],
    wallet_agg["active_days_observed"]
)

wallet_agg["avg_daily_total_in"] = safe_divide(
    wallet_agg["total_in_sum"],
    wallet_agg["active_days_observed"]
)

wallet_agg["avg_daily_total_out"] = safe_divide(
    wallet_agg["total_out_sum"],
    wallet_agg["active_days_observed"]
)

wallet_agg["avg_daily_net_flow"] = safe_divide(
    wallet_agg["total_net_flow_sum"],
    wallet_agg["active_days_observed"]
)

wallet_agg["avg_daily_total_flow"] = safe_divide(
    wallet_agg["total_flow_sum"],
    wallet_agg["active_days_observed"]
)

# Std from sufficient statistics
# var = E[x^2] - (E[x])^2
ex2_tx = safe_divide(wallet_agg["tx_count_sq_sum"], wallet_agg["active_days_observed"])
ex2_in = safe_divide(wallet_agg["total_in_sq_sum"], wallet_agg["active_days_observed"])
ex2_out = safe_divide(wallet_agg["total_out_sq_sum"], wallet_agg["active_days_observed"])
ex2_net = safe_divide(wallet_agg["net_flow_sq_sum"], wallet_agg["active_days_observed"])
ex2_flow = safe_divide(wallet_agg["total_flow_sq_sum"], wallet_agg["active_days_observed"])

wallet_agg["std_daily_tx_count"] = np.sqrt(
    np.maximum(ex2_tx - wallet_agg["avg_daily_tx_count"] ** 2, 0)
)

wallet_agg["std_daily_total_in"] = np.sqrt(
    np.maximum(ex2_in - wallet_agg["avg_daily_total_in"] ** 2, 0)
)

wallet_agg["std_daily_total_out"] = np.sqrt(
    np.maximum(ex2_out - wallet_agg["avg_daily_total_out"] ** 2, 0)
)

wallet_agg["std_daily_net_flow"] = np.sqrt(
    np.maximum(ex2_net - wallet_agg["avg_daily_net_flow"] ** 2, 0)
)

wallet_agg["std_daily_total_flow"] = np.sqrt(
    np.maximum(ex2_flow - wallet_agg["avg_daily_total_flow"] ** 2, 0)
)

# Ratios
wallet_agg["in_active_day_ratio"] = safe_divide(
    wallet_agg["in_active_days"],
    wallet_agg["active_days_observed"]
)

wallet_agg["out_active_day_ratio"] = safe_divide(
    wallet_agg["out_active_days"],
    wallet_agg["active_days_observed"]
)

wallet_agg["both_active_day_ratio"] = safe_divide(
    wallet_agg["both_active_days"],
    wallet_agg["active_days_observed"]
)

wallet_agg["in_out_day_balance"] = safe_divide(
    wallet_agg["in_active_days"] - wallet_agg["out_active_days"],
    wallet_agg["active_days_observed"]
)

# CV and concentration
wallet_agg["tx_count_cv"] = safe_divide(
    wallet_agg["std_daily_tx_count"],
    wallet_agg["avg_daily_tx_count"]
)

wallet_agg["total_flow_cv"] = safe_divide(
    wallet_agg["std_daily_total_flow"],
    wallet_agg["avg_daily_total_flow"]
)

wallet_agg["tx_concentration_ratio"] = safe_divide(
    wallet_agg["max_daily_tx_count"],
    wallet_agg["total_tx"]
)

wallet_agg["flow_concentration_ratio"] = safe_divide(
    wallet_agg["max_daily_total_flow"],
    wallet_agg["total_flow_sum"]
)


# =========================
# 6. SELECT FINAL COLUMNS
# =========================
final_cols = [
    "wallet",
    "active_days_observed",
    "first_active_date",
    "last_active_date",
    "activity_span_days",
    "activity_density",

    "total_tx",
    "total_in_sum",
    "total_out_sum",
    "total_net_flow_sum",
    "total_flow_sum",

    "avg_daily_tx_count",
    "avg_daily_total_in",
    "avg_daily_total_out",
    "avg_daily_net_flow",
    "avg_daily_total_flow",

    "max_daily_tx_count",
    "max_daily_total_in",
    "max_daily_total_out",
    "max_daily_total_flow",

    "std_daily_tx_count",
    "std_daily_total_in",
    "std_daily_total_out",
    "std_daily_net_flow",
    "std_daily_total_flow",

    "in_active_days",
    "out_active_days",
    "both_active_days",

    "in_active_day_ratio",
    "out_active_day_ratio",
    "both_active_day_ratio",
    "in_out_day_balance",

    "tx_count_cv",
    "total_flow_cv",
    "tx_concentration_ratio",
    "flow_concentration_ratio",
]

wallet_eval = wallet_agg[final_cols].copy()


# =========================
# 7. MERGE LABELS
# =========================
wallet_eval_with_labels = (
    wallet_eval
    .merge(cluster1, on="wallet", how="left")
    .merge(cluster2, on="wallet", how="left")
)

missing_c1 = wallet_eval_with_labels["cluster_1"].isna().sum()
missing_c2 = wallet_eval_with_labels["cluster_2"].isna().sum()

print("\nFINAL SUMMARY")
print("-------------")
print(f"Rows in evaluation table   : {len(wallet_eval):,}")
print(f"Unique wallets             : {wallet_eval['wallet'].nunique():,}")
print(f"Number of feature columns  : {len(wallet_eval.columns)}")
print(f"Missing cluster_1 labels   : {missing_c1:,}")
print(f"Missing cluster_2 labels   : {missing_c2:,}")

if missing_c1 > 0 or missing_c2 > 0:
    raise ValueError("Some wallets are missing cluster labels after merge.")

print("\nSample output:")
print(wallet_eval_with_labels.head())


# =========================
# 8. SAVE
# =========================
wallet_eval.to_csv(OUTPUT_EVAL_FEATURES, index=False)
wallet_eval_with_labels.to_csv(OUTPUT_EVAL_WITH_LABELS, index=False)

print("\nFILES SAVED")
print("-----------")
print(OUTPUT_EVAL_FEATURES)
print(OUTPUT_EVAL_WITH_LABELS)