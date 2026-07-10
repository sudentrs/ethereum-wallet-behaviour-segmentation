import pandas as pd
import glob

path = r"C:\Users\sudet\Downloads\dataverse_files\wallet_daily_clean_2022*.csv"

files = glob.glob(path)

dfs = []

for f in files:
    print("Loading", f)
    df = pd.read_csv(f)
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

output = r"C:\Users\sudet\Downloads\dataverse_files\wallet_daily_2022.csv"
merged.to_csv(output, index=False)

print("Saved:", output)