import pandas as pd
from collections import defaultdict
import numpy as np
from datetime import datetime

# === INPUT ===
FILE = "C:/Users/sudet/Downloads/202108/202108.tsv"
chunks = pd.read_csv(FILE, sep="\t", chunksize=250_000, dtype=str, low_memory=True)

# === STORAGE ===

# Global features
tx_count = defaultdict(int)
total_value = defaultdict(float)
unique_tokens = defaultdict(set)
unique_counterparties = defaultdict(set)

# Daily-level tracking (needed for clustering + state detection)
daily_sent = defaultdict(lambda: defaultdict(float))
daily_received = defaultdict(lambda: defaultdict(float))

# Timestamps storage for event windows
timestamps = defaultdict(list)

# === WINDOW CONSTANTS ===
fork = pd.Timestamp("2021-08-05")

pre_start  = fork - pd.Timedelta(days=3)
pre_end    = fork - pd.Timedelta(days=1)

post_start = fork + pd.Timedelta(days=1)
post_end   = fork + pd.Timedelta(days=3)

print("\nStarting processing...\n")

# === PROCESS TSV IN CHUNKS ===
for i, df_chunk in enumerate(chunks):
    print(f"Processing chunk {i}...")

    df_chunk["time"] = pd.to_datetime(df_chunk["time"], errors="coerce")
    df_chunk["value"] = pd.to_numeric(df_chunk["value"], errors="coerce").fillna(0)
    df_chunk["token_decimals"] = pd.to_numeric(df_chunk["token_decimals"], errors="coerce").fillna(18)

    # Normalize token values:
    df_chunk["norm_value"] = df_chunk["value"] / (10 ** df_chunk["token_decimals"])

    for row in df_chunk.itertuples():
        sender = row.sender
        recipient = row.recipient
        token = row.token_address
        val = row.norm_value
        t = row.time
        day = t.date()

        # Global aggregation
        tx_count[sender] += 1
        tx_count[recipient] += 1

        total_value[sender] += val
        total_value[recipient] += val

        unique_tokens[sender].add(token)
        unique_tokens[recipient].add(token)

        unique_counterparties[sender].add(recipient)
        unique_counterparties[recipient].add(sender)

        # Track daily directional flow
        daily_sent[sender][day] += val
        daily_received[recipient][day] += val

        # Store timestamp for pre/event/post window flags
        timestamps[sender].append(t)
        timestamps[recipient].append(t)

print("\nFinished reading file, now computing final tables...\n")

# === BUILD FEATURE TABLE ===

wallets = list(tx_count.keys())

df_feat = pd.DataFrame({
    "address": wallets,
    "tx_count": [tx_count[w] for w in wallets],
    "total_value": [total_value[w] for w in wallets],
    "unique_tokens": [len(unique_tokens[w]) for w in wallets],
    "unique_counterparties": [len(unique_counterparties[w]) for w in wallets],
})

# === EVENT WINDOW BINARY FEATURES ===

df_feat["tx_pre3"] = [sum((t >= pre_start) & (t <= pre_end) for t in timestamps[w]) for w in wallets]
df_feat["tx_event"] = [sum(t.date() == fork.date() for t in timestamps[w]) for w in wallets]
df_feat["tx_post3"] = [sum((t >= post_start) & (t <= post_end) for t in timestamps[w]) for w in wallets]

# === BUILD DAILY STATE LABELS (b / s / bs / 0) ===

state_labels = {}
THRESH = 0.01  # like paper threshold (directionality sensitivity)

for w in wallets:
    state_labels[w] = {}
    all_days = sorted(set(list(daily_sent[w].keys()) + list(daily_received[w].keys())))
    
    for d in all_days:
        sent = daily_sent[w].get(d, 0)
        recv = daily_received[w].get(d, 0)

        if sent == 0 and recv == 0:
            state_labels[w][d] = "0"  # inactive
        else:
            directionality = (recv - sent) / max(recv + sent, 1e-9)

            if directionality > THRESH:
                state_labels[w][d] = "b"  # net accumulation
            elif directionality < -THRESH:
                state_labels[w][d] = "s"  # selling behavior
            else:
                state_labels[w][d] = "bs" # mixed activity

df_feat.to_csv("wallet_features_august.csv", index=False)

import pickle
pickle.dump(state_labels, open("wallet_state_labels.pkl", "wb"))

print("\nExport complete:")
print(" ✔ wallet_features_august.csv")
print(" ✔ wallet_state_labels.pkl (for clustering / SVN)\n")
