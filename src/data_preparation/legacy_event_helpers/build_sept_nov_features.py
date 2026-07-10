import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

# ======================================================
# CONFIG
# ======================================================

PARQUET_DIRS = [
    "processed/202209",
    "processed/202210"
]

OUTPUT_FILE = "wallet_features_sept_oct_2022.csv"

WETH_SYMBOLS = {"WETH"}

WINDOW_LENGTH_DAYS = 20
WINDOW_SHIFT_DAYS = 7

START_DATE = pd.Timestamp("2022-09-01", tz="UTC")
END_DATE   = pd.Timestamp("2022-10-31", tz="UTC")

# ======================================================
# LOAD DATA (ALL MONTHS)
# ======================================================

print("Loading processed parquet data (Sept-Oct)...")

df = pd.concat(
    [pd.read_parquet(d) for d in PARQUET_DIRS],
    ignore_index=True
)

# Restrict strictly to pre-event window
df = df[(df["time"] >= START_DATE) & (df["time"] <= END_DATE)]

print(f"Total rows loaded: {len(df):,}")

# ======================================================
# PREPARE FLOWS
# ======================================================

# Identify ETH-equivalent transfers (WETH)
df["is_weth"] = df["token_symbol"].isin(WETH_SYMBOLS)

# Inflows (ETH accumulation)
inflows = df[df["is_weth"]].copy()
inflows["wallet"] = inflows["recipient"]
inflows["eth_flow"] = inflows["value_decimal"]

# Outflows (ETH reduction)
outflows = df[df["is_weth"]].copy()
outflows["wallet"] = outflows["sender"]
outflows["eth_flow"] = -outflows["value_decimal"]

eth_flows = pd.concat(
    [
        inflows[["wallet", "time", "eth_flow"]],
        outflows[["wallet", "time", "eth_flow"]],
    ],
    ignore_index=True
)

# All-token activity (for magnitudo)
df["wallet"] = df["sender"]
all_activity = df[["wallet", "time", "value_decimal"]]

# ======================================================
# BUILD ROLLING WINDOWS
# ======================================================

windows = []
current_start = START_DATE

while current_start + timedelta(days=WINDOW_LENGTH_DAYS) <= END_DATE:
    windows.append(
        (current_start, current_start + timedelta(days=WINDOW_LENGTH_DAYS))
    )
    current_start += timedelta(days=WINDOW_SHIFT_DAYS)

print(f"Rolling windows created: {len(windows)}")

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

    # --------------------------------------------------
    # 1. Signed turnover (net ETH inflow)
    # --------------------------------------------------

    signed_turnover = eth_win.groupby("wallet")["eth_flow"].sum()

    # --------------------------------------------------
    # 2. Magnitudo (ETH concentration)
    # --------------------------------------------------

    eth_volume = (
        eth_win
        .assign(abs_eth=eth_win["eth_flow"].abs())
        .groupby("wallet")["abs_eth"]
        .sum()
    )

    total_volume = (
        all_win
        .groupby("wallet")["value_decimal"]
        .sum()
    )

    magnitudo = eth_volume / total_volume
    magnitudo = magnitudo.replace([np.inf, -np.inf], 1.0).fillna(0.0)

    # --------------------------------------------------
    # 3. Max exposure (max cumulative ETH position)
    # --------------------------------------------------

    eth_win_sorted = eth_win.sort_values("time")
    eth_win_sorted["cum_eth"] = (
        eth_win_sorted
        .groupby("wallet")["eth_flow"]
        .cumsum()
    )

    max_exposure = eth_win_sorted.groupby("wallet")["cum_eth"].max()

    # --------------------------------------------------
    # Combine features
    # --------------------------------------------------

    features = pd.DataFrame(
        {
            "signed_turnover": signed_turnover,
            "magnitudo": magnitudo,
            "max_exposure": max_exposure,
        }
    ).fillna(0.0)

    # Normalize signed_turnover and max_exposure to [-1, 1]
    for col in ["signed_turnover", "max_exposure"]:
        max_abs = features[col].abs().max()
        if max_abs > 0:
            features[col] = features[col] / max_abs

    features["window_start"] = w_start
    features["window_end"]   = w_end

    feature_rows.append(features.reset_index())

# ======================================================
# SAVE OUTPUT
# ======================================================

feature_df = pd.concat(feature_rows, ignore_index=True)
feature_df.to_csv(OUTPUT_FILE, index=False)

print("\n=== DONE ===")
print(f"Feature table saved to {OUTPUT_FILE}")
print(f"Total rows: {len(feature_df):,}")
