import pandas as pd
from pathlib import Path
from datetime import timedelta

# ======================================================
# CONFIG
# ======================================================

PARQUET_DIR = "erc20_clean_parquet"
OUTPUT_FILE = "wallet_features_july2021.csv"

WETH_SYMBOLS = {"WETH"}

WINDOW_LENGTH_DAYS = 20
WINDOW_SHIFT_DAYS = 7

START_DATE = pd.Timestamp("2021-07-01", tz="UTC")
END_DATE   = pd.Timestamp("2021-07-31", tz="UTC")

# ======================================================
# LOAD DATA
# ======================================================

print("Loading processed ERC-20 data...")
df = pd.read_parquet(PARQUET_DIR)

df = df[(df["time"] >= START_DATE) & (df["time"] <= END_DATE)]
print(f"Rows in July: {len(df):,}")

# ======================================================
# PREPARE FLOWS
# ======================================================

df["is_weth"] = df["token_symbol"].isin(WETH_SYMBOLS)

# Inflows
inflows = df[df["is_weth"]].copy()
inflows["wallet"] = inflows["recipient"]
inflows["eth_flow"] = inflows["value_decimal"]

# Outflows
outflows = df[df["is_weth"]].copy()
outflows["wallet"] = outflows["sender"]
outflows["eth_flow"] = -outflows["value_decimal"]

eth_flows = pd.concat([
    inflows[["wallet", "time", "eth_flow"]],
    outflows[["wallet", "time", "eth_flow"]]
])

# All-token activity (for magnitudo)
df["wallet"] = df["sender"]
all_activity = df[["wallet", "time", "value_decimal"]]

# ======================================================
# BUILD ROLLING WINDOWS
# ======================================================

windows = []
current_start = START_DATE

while current_start + timedelta(days=WINDOW_LENGTH_DAYS) <= END_DATE:
    windows.append((
        current_start,
        current_start + timedelta(days=WINDOW_LENGTH_DAYS)
    ))
    current_start += timedelta(days=WINDOW_SHIFT_DAYS)

print(f"Rolling windows: {len(windows)}")

# ======================================================
# FEATURE CONSTRUCTION
# ======================================================

feature_rows = []

for w_start, w_end in windows:
    print(f"Processing window {w_start.date()} → {w_end.date()}")

    eth_win = eth_flows[
        (eth_flows["time"] >= w_start) &
        (eth_flows["time"] <  w_end)
    ]

    all_win = all_activity[
        (all_activity["time"] >= w_start) &
        (all_activity["time"] <  w_end)
    ]

    # 1. Signed turnover (net ETH inflow)
    signed_turnover = eth_win.groupby("wallet")["eth_flow"].sum()

    # 2. Magnitudo (ETH volume / total volume)
    eth_volume = eth_win.assign(
        abs_eth_flow=eth_win["eth_flow"].abs()
    ).groupby("wallet")["abs_eth_flow"].sum()

    total_volume = all_win.groupby("wallet")["value_decimal"].sum()

    magnitudo = (eth_volume / total_volume).fillna(0)

    # 3. Max exposure (max cumulative ETH position)
    eth_win_sorted = eth_win.sort_values("time")
    eth_win_sorted["cum_eth"] = eth_win_sorted.groupby("wallet")["eth_flow"].cumsum()
    max_exposure = eth_win_sorted.groupby("wallet")["cum_eth"].max()

    features = pd.DataFrame({
        "signed_turnover": signed_turnover,
        "magnitudo": magnitudo,
        "max_exposure": max_exposure
    }).fillna(0)

    # Normalize to [-1, 1]
    for col in ["signed_turnover", "max_exposure"]:
        max_abs = features[col].abs().max()
        if max_abs > 0:
            features[col] = features[col] / max_abs

    features["window_start"] = w_start
    features["window_end"]   = w_end

    feature_rows.append(features.reset_index())

# ======================================================
# SAVE
# ======================================================

feature_df = pd.concat(feature_rows, ignore_index=True)
feature_df.to_csv(OUTPUT_FILE, index=False)

print("\n=== DONE ===")
print(f"Feature table saved to {OUTPUT_FILE}")
print(f"Rows: {len(feature_df):,}")
