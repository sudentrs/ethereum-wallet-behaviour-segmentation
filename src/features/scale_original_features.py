import pandas as pd
import numpy as np
from pathlib import Path
import os

# =========================================================
# SETTINGS
# =========================================================
INPUT_FILE = "wallet_evaluation_features_with_labels_chunked_202209.csv"
OUTPUT_FILE = "wallet_evaluation_features_robust_scaled_chunked_202209.csv"
STATS_FILE = "wallet_feature_robust_scaling_stats_202209.csv"
MEMMAP_FILE = "wallet_eval_transformed_memmap_202209.dat"

CHUNKSIZE = 100_000
DTYPE = np.float32

# Feature olmayan kolonlar
NON_FEATURE_COLS = {
    "wallet",
    "first_active_date",
    "last_active_date",
    "cluster_1",
    "cluster_2",
}

# Bounded / ratio feature'lar:
# genelde log uygulanmaz, sadece robust scale edilir
DO_NOT_LOG_COLS = {
    "in_out_ratio",
    "directionality",
    "flow_concentration_ratio",
}

# Signed transform uygulanacak kolonlar:
# negatif / pozitif olabilen flow tipleri
SIGNED_KEYWORDS = [
    "net_flow",
    "net",
    "imbalance",
    "balance"
]

# Positive skewed transform uygulanacak kolonlar
POSITIVE_LOG_KEYWORDS = [
    "count", "tx", "amount", "volume", "flow", "value",
    "days", "span", "avg", "max", "sum", "total"
]

# =========================================================
# HELPERS
# =========================================================
def is_feature_col(col: str) -> bool:
    return col not in NON_FEATURE_COLS

def should_use_signed_log(col_name: str) -> bool:
    c = col_name.lower()

    if col_name in DO_NOT_LOG_COLS:
        return False

    if not is_feature_col(col_name):
        return False

    if "ratio" in c or "share" in c or "fraction" in c or "concentration" in c:
        return False

    return any(k in c for k in SIGNED_KEYWORDS)

def should_use_positive_log(col_name: str) -> bool:
    c = col_name.lower()

    if col_name in DO_NOT_LOG_COLS:
        return False

    if not is_feature_col(col_name):
        return False

    if should_use_signed_log(col_name):
        return False

    if "ratio" in c or "share" in c or "fraction" in c or "concentration" in c:
        return False

    return any(k in c for k in POSITIVE_LOG_KEYWORDS)

def signed_log1p_array(x: np.ndarray) -> np.ndarray:
    return np.sign(x) * np.log1p(np.abs(x))

def apply_column_transform(series: pd.Series, col_name: str) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")

    if should_use_signed_log(col_name):
        return pd.Series(
            signed_log1p_array(s.to_numpy(dtype=np.float64)),
            index=s.index
        )

    if should_use_positive_log(col_name):
        arr = s.to_numpy(dtype=np.float64)
        mask = ~np.isnan(arr)
        if mask.any():
            min_val = np.nanmin(arr)
            # pozitif/log-uygun değilse olduğu gibi bırak
            if min_val >= 0:
                arr[mask] = np.log1p(arr[mask])
        return pd.Series(arr, index=s.index)

    return s

# =========================================================
# PASS 0: DISCOVER FEATURES + COUNT ROWS
# =========================================================
print("PASS 0: Discovering feature columns and row count...")

sample = pd.read_csv(INPUT_FILE, nrows=5000)

numeric_cols = sample.select_dtypes(include=[np.number]).columns.tolist()
feature_cols = [c for c in numeric_cols if c not in NON_FEATURE_COLS]

n_rows = 0
for chunk in pd.read_csv(INPUT_FILE, chunksize=CHUNKSIZE):
    n_rows += len(chunk)

n_features = len(feature_cols)

print(f"Total rows      : {n_rows}")
print(f"Feature columns : {n_features}")
print("Feature list:")
print(feature_cols)

signed_cols = [c for c in feature_cols if should_use_signed_log(c)]
positive_log_cols = [c for c in feature_cols if should_use_positive_log(c)]
raw_cols = [c for c in feature_cols if c not in signed_cols and c not in positive_log_cols]

print("\nSigned-log columns:")
print(signed_cols)

print("\nPositive log1p columns:")
print(positive_log_cols)

print("\nRaw / only robust-scale columns:")
print(raw_cols)

# =========================================================
# PASS 1: TRANSFORM AND STORE IN MEMMAP
# =========================================================
print("\nPASS 1: Transforming features and storing in memmap...")

memmap_path = Path(MEMMAP_FILE)
if memmap_path.exists():
    memmap_path.unlink()

X_mm = np.memmap(
    MEMMAP_FILE,
    dtype=DTYPE,
    mode="w+",
    shape=(n_rows, n_features)
)

row_start = 0

for i, chunk in enumerate(pd.read_csv(INPUT_FILE, chunksize=CHUNKSIZE)):
    work = chunk.copy()

    transformed_cols = []
    for col in feature_cols:
        transformed = apply_column_transform(work[col], col)
        transformed_cols.append(transformed.to_numpy(dtype=DTYPE))

    block = np.column_stack(transformed_cols).astype(DTYPE, copy=False)

    row_end = row_start + len(chunk)
    X_mm[row_start:row_end, :] = block
    row_start = row_end

    if (i + 1) % 5 == 0:
        print(f"  transformed chunks: {i + 1}")

X_mm.flush()

# =========================================================
# PASS 2: ROBUST STATS (MEDIAN / IQR)
# =========================================================
print("\nPASS 2: Computing robust scaling statistics from memmap...")

X_mm = np.memmap(
    MEMMAP_FILE,
    dtype=DTYPE,
    mode="r",
    shape=(n_rows, n_features)
)

medians = np.zeros(n_features, dtype=np.float64)
q25 = np.zeros(n_features, dtype=np.float64)
q75 = np.zeros(n_features, dtype=np.float64)
iqr = np.zeros(n_features, dtype=np.float64)

for j in range(n_features):
    col = np.array(X_mm[:, j], dtype=np.float64)  # column extraction
    med = np.nanmedian(col)
    p25 = np.nanpercentile(col, 25)
    p75 = np.nanpercentile(col, 75)
    scale = p75 - p25

    if not np.isfinite(scale) or scale == 0:
        scale = 1.0

    medians[j] = med
    q25[j] = p25
    q75[j] = p75
    iqr[j] = scale

    if (j + 1) % 10 == 0 or (j + 1) == n_features:
        print(f"  processed features: {j + 1}/{n_features}")

stats_df = pd.DataFrame({
    "feature": feature_cols,
    "median": medians,
    "q25": q25,
    "q75": q75,
    "iqr": iqr,
    "transform_type": [
        "signed_log1p" if c in signed_cols
        else "log1p" if c in positive_log_cols
        else "raw"
        for c in feature_cols
    ]
})

stats_df.to_csv(STATS_FILE, index=False)

print("\nRobust stats saved:")
print(STATS_FILE)

# =========================================================
# PASS 3: APPLY ROBUST SCALING AND WRITE FINAL CSV
# =========================================================
print("\nPASS 3: Writing final robust-scaled output...")

output_path = Path(OUTPUT_FILE)
if output_path.exists():
    output_path.unlink()

median_map = dict(zip(feature_cols, medians))
iqr_map = dict(zip(feature_cols, iqr))

first_write = True

for i, chunk in enumerate(pd.read_csv(INPUT_FILE, chunksize=CHUNKSIZE)):
    work = chunk.copy()

    for col in feature_cols:
        s = apply_column_transform(work[col], col)
        s = pd.to_numeric(s, errors="coerce")
        work[col] = (s - median_map[col]) / iqr_map[col]

    work.to_csv(
        OUTPUT_FILE,
        mode="w" if first_write else "a",
        header=first_write,
        index=False
    )
    first_write = False

    if (i + 1) % 5 == 0:
        print(f"  written chunks: {i + 1}")

print("\nDONE")
print(f"Output file : {OUTPUT_FILE}")
print(f"Stats file  : {STATS_FILE}")

# =========================================================
# OPTIONAL CLEANUP
# =========================================================
# Eğer memmap dosyasını saklamak istemezsen aç:
# os.remove(MEMMAP_FILE)
# print(f"Removed temp memmap: {MEMMAP_FILE}")