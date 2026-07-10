import pandas as pd
import glob

files = glob.glob(r"C:\Users\sudet\Downloads\dataverse_files\wallet_norm_2022*.csv")

for f in files:

    print("Processing", f)

    df = pd.read_csv(f)

    # convert time to date
    df["date"] = pd.to_datetime(df["time"]).dt.date

    # separate in/out
    df["in_value"] = df.apply(lambda x: x["value"] if x["direction"]=="in" else 0, axis=1)
    df["out_value"] = df.apply(lambda x: x["value"] if x["direction"]=="out" else 0, axis=1)

    wallet_daily = df.groupby(["wallet","date"]).agg(
        total_in=("in_value","sum"),
        total_out=("out_value","sum"),
        tx_count=("value","count")
    ).reset_index()

    wallet_daily.to_csv(f.replace("wallet_norm_","wallet_daily_"),index=False)