import duckdb
import pandas as pd

con = duckdb.connect()

# load daily wallet dataset
df = con.execute("""
SELECT
    wallet,
    date,
    total_in,
    total_out,
    tx_count,
    (total_in - total_out) AS net_flow
FROM 'wallet_daily_2022.csv'
""").fetchdf()

# convert date
df["date"] = pd.to_datetime(df["date"])

# aggregate wallet features
wallet_features = df.groupby("wallet").agg(

    active_days=("date", "nunique"),

    first_day=("date", "min"),
    last_day=("date", "max"),

    total_tx=("tx_count", "sum"),

    total_in=("total_in", "sum"),
    total_out=("total_out", "sum"),

    avg_tx_size=("net_flow", "mean"),

    flow_volatility=("net_flow", "std"),

    tx_size_volatility=("tx_count", "std"),

    mean_tx_daily=("tx_count", "mean"),
    std_tx_daily=("tx_count", "std")

).reset_index()

# activity span
wallet_features["activity_span"] = (
    wallet_features["last_day"] - wallet_features["first_day"]
).dt.days + 1

# density
wallet_features["activity_density"] = (
    wallet_features["active_days"] /
    wallet_features["activity_span"]
)

# avg tx per day
wallet_features["avg_tx_per_day"] = (
    wallet_features["total_tx"] /
    wallet_features["active_days"]
)

# net flow
wallet_features["net_flow"] = (
    wallet_features["total_in"] -
    wallet_features["total_out"]
)

# ratios
wallet_features["in_out_ratio"] = (
    wallet_features["total_in"] /
    (wallet_features["total_out"] + 1)
)

wallet_features["directionality"] = (
    wallet_features["total_in"] /
    (wallet_features["total_in"] + wallet_features["total_out"] + 1)
)

# burstiness
wallet_features["burstiness"] = (
    (wallet_features["std_tx_daily"] - wallet_features["mean_tx_daily"]) /
    (wallet_features["std_tx_daily"] + wallet_features["mean_tx_daily"] + 1e-9)
)

# remove helper columns
wallet_features = wallet_features.drop(
    columns=["first_day","last_day","mean_tx_daily","std_tx_daily"]
)

wallet_features.to_csv("wallet_behavior_features.csv", index=False)

print(wallet_features.head())