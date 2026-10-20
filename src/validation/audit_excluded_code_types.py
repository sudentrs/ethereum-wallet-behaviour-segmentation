"""Audit current code types at a pinned block; never modifies cohort labels."""
import json
from datetime import datetime, timezone

import pandas as pd

from historical_monthly_code_check import ROOT, RPC, rpc_url


def main():
    output = ROOT / "data/interim/excluded_code_type_audit"
    output.mkdir(parents=True, exist_ok=True)
    frames = []
    for name in ("historical_monthly_code_2022", "historical_monthly_code_2022_sample2"):
        frame = pd.read_csv(ROOT / "data/interim" / name / "address_summary.csv")
        frame = frame.loc[frame.baseline_type.eq("contract")].copy()
        frame["source_sample"] = name
        frames.append(frame)
    addresses = pd.concat(frames, ignore_index=True)
    if addresses.address.duplicated().any() or len(addresses) != 120:
        raise RuntimeError("Expected 120 distinct excluded addresses")
    rpc = RPC(rpc_url(), 0.5)
    if rpc.call("eth_chainId", []) != "0x1":
        raise RuntimeError("Expected Ethereum Mainnet")
    block = rpc.call("eth_getBlockByNumber", ["latest", False])
    metadata = {"audit_time_utc": datetime.now(timezone.utc).isoformat(),
                "block_number": int(block["number"], 16), "block_hash": block["hash"]}
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2))
    rows = []
    for start in range(0, len(addresses), 20):
        batch = addresses.address.tolist()[start:start + 20]
        codes = rpc.batch([("eth_getCode", [address, block["number"]]) for address in batch])
        for address, code in zip(batch, codes):
            raw = bytes.fromhex(code.removeprefix("0x"))
            delegated = len(raw) == 23 and raw[:3] == bytes.fromhex("ef0100")
            kind = "empty_code" if not raw else "eip7702_delegation" if delegated else "other_nonempty_code"
            rows.append({"address": address, "current_code_type": kind,
                         "current_code_bytes": len(raw), "current_code_prefix": code[:48],
                         "delegation_target": "0x" + raw[3:].hex() if delegated else "",
                         "audit_block": metadata["block_number"]})
        print(f"Audited {len(rows)}/120", flush=True)
    result = addresses.merge(pd.DataFrame(rows), on="address", validate="one_to_one")
    result["historical_group"] = result.months_with_code.map(
        lambda n: "no_code_all_month_ends" if n == 0 else "code_all_month_ends" if n == 12 else "code_some_month_ends")
    result.to_csv(output / "excluded_address_audit.csv", index=False)
    summary = result.groupby(["historical_group", "current_code_type"]).size().rename("addresses").reset_index()
    summary.to_csv(output / "summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
