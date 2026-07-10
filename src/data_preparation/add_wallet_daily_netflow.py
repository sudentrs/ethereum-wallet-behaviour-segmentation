import pandas as pd

file = r"C:\Users\sudet\Downloads\dataverse_files\wallet_daily_2022.csv"

df = pd.read_csv(file)

df["net_flow"] = df["total_in"] - df["total_out"]

df.to_csv(
    r"C:\Users\sudet\Downloads\dataverse_files\wallet_daily_2022_netflow.csv",
    index=False
)

print("Saved wallet_daily_2022_netflow.csv")