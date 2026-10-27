"""Prepare an activity-stratified exclusion audit offline; never changes cohorts."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def addresses(series):
    result = series.astype(str).str.strip().str.lower().str.removeprefix("0x")
    result = "0x" + result
    if not result.str.fullmatch(r"0x[0-9a-f]{40}").all():
        raise ValueError("Invalid address; refusing to silently drop rows")
    if result.duplicated().any():
        raise ValueError("Duplicate addresses")
    return result


def draw(frame, per_stratum, seed):
    """SRS without replacement within fixed, interpretable activity bands."""
    frame = frame.sort_values("address").copy()
    frame["activity_stratum"] = pd.cut(
        frame.total_tx, [-np.inf, 2, 10, np.inf],
        labels=["low_le_2", "medium_3_to_10", "high_gt_10"]
    ).astype(str)
    parts = []
    for _, group in frame.groupby("activity_stratum", sort=True):
        n = min(per_stratum, len(group))
        part = group.sample(n=n, random_state=seed).copy()
        part["population_n"] = len(group)
        part["sample_n"] = n
        part["inclusion_probability"] = n / len(group)
        part["sampling_weight"] = len(group) / n
        parts.append(part)
    if not parts:
        raise ValueError("Empty exclusion population")
    return pd.concat(parts, ignore_index=True).sort_values("address")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="results_v3/historical_exclusion_audit_design")
    parser.add_argument("--per-stratum", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20221020)
    args = parser.parse_args()
    if args.per_stratum < 1:
        parser.error("per-stratum must be positive")
    output = ROOT / args.output_dir
    if output.exists():
        raise SystemExit("Use a new output directory; existing audits are never overwritten")
    raw_path = ROOT / "data/processed/wallet_kmeans6_expanded_daily_features.csv"
    raw = pd.read_csv(raw_path, usecols=["wallet", "total_tx"], dtype={"wallet": str})
    raw["address"] = addresses(raw.wallet)
    raw.total_tx = pd.to_numeric(raw.total_tx, errors="raise")
    if not np.isfinite(raw.total_tx).all() or (raw.total_tx < 0).any():
        raise ValueError("Missing or invalid activity")
    inputs = [raw_path, Path(__file__).resolve()]
    retained = None
    for k in (4, 5, 6):
        path = ROOT / f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv"
        cohort = set(addresses(pd.read_csv(path, usecols=["wallet"], dtype=str).wallet))
        if retained is not None and cohort != retained:
            raise ValueError("K4/K5/K6 cohorts differ")
        retained = cohort
        inputs.append(path)
    if not retained.issubset(set(raw.address)):
        raise ValueError("Retained wallets missing from raw population")
    excluded = raw.loc[~raw.address.isin(retained), ["address", "total_tx"]].copy()
    sample = draw(excluded, args.per_stratum, args.seed)
    evidence_path = ROOT / "data/interim/excluded_code_type_audit/historical_origination_audit.csv"
    evidence = pd.read_csv(evidence_path)
    evidence["address"] = addresses(evidence.address)
    if not set(evidence.address).issubset(set(excluded.address)):
        raise ValueError("Prior excluded audit contains addresses outside exclusion population")
    inputs.append(evidence_path)
    # Draw from the entire exclusion population BEFORE joining prior evidence.
    columns = [c for c in ["address", "status", "transaction_hash", "block_number",
                           "timestamp_utc", "historical_group", "months_with_code"] if c in evidence]
    sample = sample.merge(evidence[columns], how="left", on="address", validate="one_to_one")
    sample["evidence_status"] = np.where(
        sample.status.eq("verified_top_level_sender_in_2022"),
        "positive_2022_origination", "unresolved")
    sample["historical_code_status"] = "pending_month_end_review"
    strata = sample.groupby("activity_stratum").agg(
        population_n=("population_n", "first"), sample_n=("sample_n", "first"),
        cached_positive_n=("evidence_status", lambda x: int(x.eq("positive_2022_origination").sum())))
    output.mkdir(parents=True)
    sample.to_csv(output / "sample.csv", index=False)
    strata.to_csv(output / "stratum_design.csv")
    evidence[columns].to_csv(output / "previous_evidence_inventory.csv", index=False)
    settings = {
        "seed": args.seed, "per_stratum": args.per_stratum,
        "raw_addresses": len(raw), "retained_addresses": len(retained),
        "excluded_addresses": len(excluded), "sample_addresses": len(sample),
        "known_positive_addresses_in_previous_audit": int(evidence.status.eq("verified_top_level_sender_in_2022").sum()),
        "cached_positive_addresses_in_probability_sample": int(sample.evidence_status.eq("positive_2022_origination").sum()),
        "rpc_calls": 0,
        "inputs_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in inputs},
    }
    (output / "design.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in settings.items() if k != "inputs_sha256"}, indent=2))


if __name__ == "__main__":
    main()
