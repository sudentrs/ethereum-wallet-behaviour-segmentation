"""Find and verify positive 2022 transaction-origination evidence for excluded samples.

No indexed match is an unresolved result, not evidence of no transactions.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone

import pandas as pd

from historical_monthly_code_check import ROOT, RPC, rpc_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", default="data/interim/excluded_code_type_audit/excluded_address_audit.csv")
    parser.add_argument("--output-dir", default="data/interim/excluded_code_type_audit")
    parser.add_argument("--blocks-csv", default="data/interim/historical_monthly_code_2022/month_end_blocks.csv")
    args = parser.parse_args()
    output = ROOT / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    input_path = ROOT / args.input_csv
    addresses = pd.read_csv(input_path)
    if addresses.address.duplicated().any() or not addresses.address.str.fullmatch(r"0x[0-9a-f]{40}").all():
        raise ValueError("Invalid or duplicate sample addresses")
    if "months_with_code" in addresses:
        addresses = addresses.sort_values("months_with_code", kind="stable")
    identity_path = output / "origination_sample_identity.json"
    identity = {"input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(), "year": 2022}
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError("Sample identity changed; use a new output directory")
    identity_path.write_text(json.dumps(identity, indent=2))
    blocks = pd.read_csv(ROOT / args.blocks_csv)
    if blocks.month.tolist() != [f"2022-{month:02d}" for month in range(1, 13)]:
        raise ValueError("Expected all twelve 2022 month-end blocks")
    end = int(blocks.iloc[-1].block_number)
    rpc = RPC(rpc_url(), 0.3)
    if rpc.call("eth_chainId", []) != "0x1":
        raise RuntimeError("Expected Ethereum Mainnet")
    # Locate the last block before 2022 without assuming a particular block number.
    lo, hi = 0, int(blocks.iloc[0].block_number)
    boundary = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp())
    while lo < hi:
        mid = (lo + hi + 1) // 2
        header = rpc.call("eth_getBlockByNumber", [hex(mid), False])
        if int(header["timestamp"], 16) < boundary:
            lo = mid
        else:
            hi = mid - 1
    start = lo + 1
    cache_dir = output / "origination_evidence"
    cache_dir.mkdir(exist_ok=True)
    records = []
    for i, item in enumerate(addresses.itertuples(index=False), 1):
        path = cache_dir / f"{item.address}.json"
        if path.exists():
            record = json.loads(path.read_text())
        else:
            record = {"address": item.address, "from_block": start, "to_block": end,
                      "checked_at_utc": datetime.now(timezone.utc).isoformat(),
                      "status": "no_indexed_external_match_unresolved"}
            response = rpc.call("alchemy_getAssetTransfers", [{
                "fromBlock": hex(start), "toBlock": hex(end),
                "fromAddress": item.address, "category": ["external"],
                "excludeZeroValue": False, "maxCount": "0x1", "order": "asc"}])
            transfers = response.get("transfers")
            if not isinstance(transfers, list):
                raise RuntimeError("Invalid transfer index response")
            if transfers:
                tx_hash = transfers[0]["hash"]
                tx = rpc.call("eth_getTransactionByHash", [tx_hash])
                receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
                number = int(tx["blockNumber"], 16)
                header = rpc.call("eth_getBlockByNumber", [tx["blockNumber"], False])
                timestamp = int(header["timestamp"], 16)
                if (tx["from"].lower() != item.address.lower() or
                        not start <= number <= end or
                        not boundary <= timestamp < int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp()) or
                        tx["hash"].lower() != tx_hash.lower() or
                        tx["blockHash"] != header["hash"] or
                        tx_hash not in header["transactions"] or
                        receipt["blockHash"] != header["hash"] or
                        receipt["transactionHash"] != tx["hash"] or
                        int(tx.get("r", "0x0"), 16) == 0 or int(tx.get("s", "0x0"), 16) == 0):
                    raise RuntimeError("Transaction evidence validation failed")
                codes = rpc.batch([("eth_getCode", [item.address, hex(number - 1)]),
                                   ("eth_getCode", [item.address, hex(number)])])
                record.update(status="verified_top_level_sender_in_2022",
                              transaction_hash=tx_hash, block_number=number,
                              timestamp_utc=datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                              transaction_type=tx.get("type"), nonce=int(tx["nonce"], 16),
                              receipt_status=receipt.get("status"),
                              empty_code_before_block=codes[0] == "0x",
                              empty_code_after_block=codes[1] == "0x",
                              transaction=tx, receipt=receipt, header=header,
                              code_before_block=codes[0], code_after_block=codes[1])
            path.write_text(json.dumps(record, indent=2))
        records.append({k: v for k, v in record.items() if k not in
                        {"transaction", "receipt", "header", "code_before_block", "code_after_block"}})
        print(f"{i}/{len(addresses)} {item.address}: {record['status']}", flush=True)
        pd.DataFrame(records).to_csv(output / "origination_progress.csv", index=False)
    evidence = pd.DataFrame(records)
    overlap = (set(addresses.columns) & set(evidence.columns)) - {"address"}
    result = addresses.drop(columns=sorted(overlap)).merge(evidence, on="address", validate="one_to_one")
    result.to_csv(output / "historical_origination_audit.csv", index=False)
    groups = [c for c in ["historical_group", "current_code_type", "status"] if c in result]
    summary = result.groupby(groups, dropna=False).size().rename("addresses").reset_index()
    summary.to_csv(output / "origination_summary.csv", index=False)
    (output / "ORIGINATION_SEARCH_COMPLETE").write_text(identity["input_sha256"] + "\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
