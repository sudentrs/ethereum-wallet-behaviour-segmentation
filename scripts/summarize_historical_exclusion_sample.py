"""Design-weighted snapshot estimates with exact finite-population intervals."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
from scipy.stats import hypergeom

ROOT = Path(__file__).resolve().parents[1]


def population_interval(N, n, x, tail):
    """Invert hypergeometric tails; return possible population success counts."""
    lo, hi = x, N - n + x
    while lo < hi:
        mid = (lo + hi) // 2
        if hypergeom.sf(x - 1, N, mid, n) >= tail:
            hi = mid
        else:
            lo = mid + 1
    lower = lo
    lo, hi = x, N - n + x
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if hypergeom.cdf(x, N, mid, n) >= tail:
            lo = mid
        else:
            hi = mid - 1
    return lower, lo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/interim/historical_exclusion_probability_audit")
    parser.add_argument("--output-dir", default="results_v3/historical_exclusion_audit_results")
    parser.add_argument("--origination-dir", default="data/interim/historical_exclusion_probability_origination")
    args = parser.parse_args()
    source = ROOT / args.input_dir
    frame = pd.read_csv(source / "address_results.csv")
    output = ROOT / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    groups = list(frame.groupby("activity_stratum"))
    population = sum(int(g.population_n.iloc[0]) for _, g in groups)
    rows = []
    # Two binary bounding outcomes per stratum, two tails each. Bonferroni
    # coverage >=95% simultaneously even when unresolved outcomes remain.
    tail = 0.05 / (4 * len(groups))
    for name, group in groups:
        N, n = int(group.population_n.iloc[0]), len(group)
        if n != int(group.sample_n.iloc[0]) or group.population_n.nunique() != 1:
            raise ValueError("Incomplete or inconsistent probability sample")
        x = int(group.snapshot_outcome.eq("empty_all_12_month_ends").sum())
        u = int(group.snapshot_outcome.eq("unresolved").sum())
        lower, _ = population_interval(N, n, x, tail)
        _, upper = population_interval(N, n, x + u, tail)
        rows.append({"activity_stratum": name, "population_n": N, "sample_n": n,
                     "empty_all_month_ends_n": x, "unresolved_n": u,
                     "weighted_lower_contribution": N * x / n,
                     "weighted_upper_contribution": N * (x + u) / n,
                     "confidence_lower_population_count": lower,
                     "confidence_upper_population_count": upper})
    result = pd.DataFrame(rows)
    lower = result.weighted_lower_contribution.sum() / population
    upper = result.weighted_upper_contribution.sum() / population
    report = {
        "estimand": "Share of excluded addresses with empty code at all 12 observed 2022 month-end blocks",
        "excluded_population_n": population, "sample_n": len(frame),
        "snapshot_checks_complete": bool(frame.observed_months.eq(12).all()),
        "unresolved_outcomes_n": int(result.unresolved_n.sum()),
        "weighted_identification_lower": lower, "weighted_identification_upper": upper,
        "point_estimate_if_outcomes_resolved": lower if result.unresolved_n.sum() == 0 else None,
        "confidence_95_lower": result.confidence_lower_population_count.sum() / population,
        "confidence_95_upper": result.confidence_upper_population_count.sum() / population,
        "interval_method": "Exact hypergeometric inversion per stratum and bounding outcome; Bonferroni simultaneous 95% conservative interval",
        "limitations": ["Snapshot code-free status is not continuous EOA identity.",
                        "Origination evidence is a separate outcome.",
                        "Excluded-population audit does not validate retained addresses.",
                        "No cohort or manuscript changed."]}
    evidence_inputs = [source / "address_results.csv", source / "address_month_cache.csv",
                       source / "month_end_blocks.csv", source / "sample_identity.json"]
    origination_path = ROOT / args.origination_dir / "historical_origination_audit.csv"
    if origination_path.exists():
        evidence_inputs.append(origination_path)
        origination = pd.read_csv(origination_path)
        if set(origination.address) != set(frame.address) or origination.address.duplicated().any():
            raise ValueError("Origination sample differs from snapshot sample")
        evidence_columns = [c for c in ["address", "status", "transaction_hash", "block_number",
                            "timestamp_utc", "empty_code_before_block", "empty_code_after_block"]
                            if c in origination]
        combined = frame.merge(origination[evidence_columns], on="address", validate="one_to_one")
        combined.to_csv(output / "address_evidence.csv", index=False)
        positive = combined.status.eq("verified_top_level_sender_in_2022")
        report["origination_verified_n"] = int(positive.sum())
        report["origination_unresolved_n"] = int((~positive).sum())
        report["weighted_confirmed_origination_share"] = float(
            combined.loc[positive, "sampling_weight"].sum() / population)
        report["origination_note"] = (
            "Weighted confirmed share is a proof-yield estimate and lower identification bound, "
            "not a point estimate of all historically EOA-active addresses. Nonmatches remain unresolved. "
            "Evidence was verified through one provider, not independent signature recovery.")
        report["origination_positive_and_all_month_ends_empty_n"] = int(
            (positive & combined.snapshot_outcome.eq("empty_all_12_month_ends")).sum())
        pd.crosstab(combined.snapshot_outcome, combined.status).to_csv(output / "evidence_cross_tab.csv")
        combined.groupby(["activity_stratum", "snapshot_outcome", "status"], dropna=False).agg(
            addresses=("address", "size"), weighted_addresses=("sampling_weight", "sum")
        ).to_csv(output / "evidence_by_stratum.csv")
    report["evidence_sha256"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in evidence_inputs}
    # Keep the compact code observations and pinned blocks shareable in Git.
    for path in evidence_inputs:
        if path.parent == source and path.resolve() != (output / path.name).resolve():
            shutil.copyfile(path, output / path.name)
    result.to_csv(output / "stratum_estimates.csv", index=False)
    (output / "estimates.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    text = ["# Historical exclusion audit: month-end snapshot outcome", "",
            report["estimand"], "",
            f"Excluded population: {population:,}; probability sample: {len(frame):,}.",
            f"Unresolved outcomes: {report['unresolved_outcomes_n']}.",
            f"Weighted identification bounds: {100*lower:.4f}% to {100*upper:.4f}%.",
            f"Conservative 95% interval allowing sampling uncertainty: {100*report['confidence_95_lower']:.4f}% to {100*report['confidence_95_upper']:.4f}%.", "",
            report["interval_method"], "", *report["limitations"], "",
            "Do not interpret these numbers as a transaction-originator error rate or as proof of year-long EOA status."]
    if "origination_verified_n" in report:
        text += ["", "## Transaction origination", "",
                 f"Verified positive 2022 transaction originators: {report['origination_verified_n']}; unresolved: {report['origination_unresolved_n']}.",
                 f"Weighted confirmed-origination share: {100*report['weighted_confirmed_origination_share']:.4f}%.",
                 f"Positives also empty at all twelve month ends: {report['origination_positive_and_all_month_ends_empty_n']}.",
                 report["origination_note"], "", "## Decision", "",
                 "The discrepancy is not limited to the original 33 cases. Do not present the present-day code filter as verified historical EOA filtering. The sample supports a substantial mismatch under the explicit month-end snapshot definition. It does not identify every affected address.",
                 "Preserve the existing baseline; construct a versioned historical cohort before rewriting paper results. Resolve K4/K6 model reconstruction and evaluate feature-representation limitations separately. Repeat annual, temporal and network analyses on a corrected cohort if that becomes the paper's primary population."]
    (output / "README.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
