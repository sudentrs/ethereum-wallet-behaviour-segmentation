import pandas as pd

input_file = r"C:\Users\sudet\Downloads\dataverse_files\202212.tsv\202212.tsv"
output_file = r"C:\Users\sudet\Downloads\dataverse_files\wallet_202212.csv"

chunksize = 100000
first = True

for chunk in pd.read_csv(input_file, sep="\t", chunksize=chunksize, dtype=str):

    sender_df = pd.DataFrame({
        "wallet": chunk["sender"],
        "time": chunk["time"],
        "token": chunk["token_symbol"],
        "direction": "out",
        "value": chunk["value"]
    })

    recipient_df = pd.DataFrame({
        "wallet": chunk["recipient"],
        "time": chunk["time"],
        "token": chunk["token_symbol"],
        "direction": "in",
        "value": chunk["value"]
    })

    result = pd.concat([sender_df, recipient_df])

    result.to_csv(
        output_file,
        mode="a",
        header=first,
        index=False
    )

    first = False