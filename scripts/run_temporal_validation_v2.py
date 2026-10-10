"""Professor guide Items 8, 10, 9; preserve the original monthly assignment.

Reconstruct absent wallet states from complete wallet-hash daily partitions,
using the original feature builder, annual scaling and median prototypes.
Use --permutations 99 for smoke results and 999 for publication inputs.
No annualisation is silently introduced: the chosen guide path is limitation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "temporal"))
from eoa_k5_temporal_validation import (derive_features, load_scaling_stats,
    nearest_centroid_assignments, scale_monthly_features)

MONTHS = [f"2022{m:02d}" for m in range(1, 13)]
LIMITATION = ("Monthly states are assigned with prototypes and scaling fitted on full-year "
    "features. Features that sum over the observation window (counts, totals and active days) "
    "are smaller in a single month, which may bias monthly assignments toward lower-activity "
    "roles. Transition results should be read with this caveat.")


def aggregate_frame(d, by_month=False):
    """Same sufficient statistics as aggregate_daily_features, within one wallet bucket."""
    d = d.copy()
    d["date"] = pd.to_datetime(d["date"], errors="raise")
    for c in ["tx_count", "total_in", "total_out"]:
        d[c] = pd.to_numeric(d[c], errors="raise").fillna(0.)
    d["net_flow"] = d.total_in - d.total_out
    d["total_flow"] = d.total_in + d.total_out
    for name, mask in [("in_active", d.total_in > 0), ("out_active", d.total_out > 0),
                       ("both_active", (d.total_in > 0) & (d.total_out > 0))]:
        d[name] = mask.astype(np.int8)
    agg = dict(active_days_observed=("date", "count"), first_active_date=("date", "min"),
               last_active_date=("date", "max"), total_tx=("tx_count", "sum"))
    for name, prefix in [("total_in", "total_in"), ("total_out", "total_out"),
                         ("net_flow", "total_net_flow"), ("total_flow", "total_flow")]:
        agg[prefix + "_sum"] = (name, "sum")
    for name in ["tx_count", "total_in", "total_out", "total_flow"]:
        agg["max_daily_" + name] = (name, "max")
    for name in ["tx_count", "total_in", "total_out", "net_flow", "total_flow"]:
        d[name + "_sq"] = d[name] ** 2
        agg[name + "_sq_sum"] = (name + "_sq", "sum")
    for name in ["in", "out", "both"]:
        agg[name + "_active_days"] = (name + "_active", "sum")
    keys = ["wallet"]
    if by_month:
        d["_month"] = d.date.dt.month - 1
        keys.append("_month")
    grouped = d.groupby(keys, sort=False).agg(**agg).reset_index()
    features = derive_features(grouped)
    if by_month:
        features["_month"] = grouped["_month"].to_numpy()
    return features


def holm(p):
    p = np.asarray(p, dtype=float)
    result = np.full(len(p), np.nan)
    valid = np.flatnonzero(np.isfinite(p))
    order = valid[np.argsort(p[valid])]
    result[order] = np.minimum(1., np.maximum.accumulate(p[order] * np.arange(len(order), 0, -1)))
    return result


def transition_stats(a, b, k):
    counts = np.bincount(a.astype(np.int64) * k + b, minlength=k*k).reshape(k, k)
    n = int(counts.sum())
    if not n:
        return counts, np.nan, np.nan, np.nan
    obs = float(np.trace(counts) / n)
    exp = float(counts.sum(1) @ counts.sum(0).astype(float) / n**2)
    return counts, obs, exp, (obs-exp)/(1-exp) if exp < 1 else np.nan


def return_null(s0, s1, s2, k, B, rng):
    """Inputs already restricted to switchers, as in the professor pseudocode."""
    if not len(s0):
        return np.full(B, np.nan), np.nan
    groups = [np.flatnonzero(s1 == g) for g in np.unique(s1)]
    expected_count = 0.
    for idx in groups:
        expected_count += np.bincount(s0[idx], minlength=k) @ np.bincount(s2[idx], minlength=k).astype(float) / len(idx)
    null = np.empty(B)
    for rep in range(B):
        matches = sum(np.count_nonzero(s0[idx] == rng.permutation(s2[idx])) for idx in groups)
        null[rep] = matches / len(s0)
    return null, expected_count / len(s0)


def fingerprint(paths):
    rows = []
    for p in paths:
        st = p.stat()
        rows.append([str(p.resolve()), st.st_size, st.st_mtime_ns])
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def reconstruct_bucket(path, models, stats, columns):
    d = pd.read_csv(path, dtype={"wallet": str, "date": str})
    d["wallet"] = d.wallet.str.strip().str.lower()
    if d[["wallet", "date"]].duplicated().any():
        raise ValueError(f"Duplicate wallet-day in {path}")
    wallets = pd.Index(d.wallet.unique())
    month_column = d.date.str.slice(0,7).str.replace("-", "", regex=False)
    if not month_column.isin(MONTHS).all():
        raise ValueError("Daily partitions contain dates outside 2022")
    states = {k: np.full((len(wallets),12), -1, dtype=np.int8) for k in models}
    features = aggregate_frame(d, by_month=True)
    scaled = scale_monthly_features(features, stats, columns)
    idx = wallets.get_indexer(scaled.wallet)
    month_idx = features["_month"].to_numpy(dtype=np.int8)
    for k, model in models.items():
        assigned = nearest_centroid_assignments(scaled, model, columns)
        states[k][idx, month_idx] = assigned.monthly_state.to_numpy(np.int8)
    return wallets, len(d), states


def initialise_bucket_worker(models, stats, columns):
    global BUCKET_MODELS, BUCKET_STATS, BUCKET_COLUMNS
    BUCKET_MODELS, BUCKET_STATS, BUCKET_COLUMNS = models, stats, columns


def run_bucket_worker(path):
    return reconstruct_bucket(path, BUCKET_MODELS, BUCKET_STATS, BUCKET_COLUMNS)


def reconstruct(args, out):
    files = sorted(args.daily_partitions.glob("wallet_daily_bucket_*.csv"))
    if not files:
        raise FileNotFoundError(f"No daily wallet partitions: {args.daily_partitions}")
    models = {k: pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/cluster_feature_medians_robust_scaled.csv", index_col=0) for k in [4,5,6]}
    model_paths = [ROOT / f"results/eoa_only_kmeans{k}/cluster_feature_medians_robust_scaled.csv" for k in models]
    signature = fingerprint(files + model_paths + [args.scaling_stats, Path(__file__)])
    cache = out / "reconstructed_monthly_states.npz"
    meta_path = out / "reconstruction_manifest.json"
    if cache.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta["input_fingerprint"] == signature:
            print("Using verified reconstruction cache", flush=True)
            with np.load(cache) as z:
                return {k: z[f"k{k}"].copy() for k in models}, meta
    stats = load_scaling_stats(args.scaling_stats)
    columns = list(models[5].columns)
    if set(columns) != set(stats) or any(list(m.columns) != columns for m in models.values()):
        raise ValueError("Prototype and scaling feature columns disagree")
    parts = {k: [] for k in models}
    raw_rows = 0
    all_wallets = set()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=initialise_bucket_worker,
                             initargs=(models,stats,columns)) as pool:
        for i, (wallets, nrows, states) in enumerate(pool.map(run_bucket_worker,files)):
            if any(w in all_wallets for w in wallets):
                raise ValueError("A wallet occurs in multiple hash buckets")
            all_wallets.update(wallets)
            raw_rows += nrows
            for k in models:
                parts[k].append(states[k])
            if i % 16 == 0 or i == len(files)-1:
                print(f"Reconstruction {i+1}/{len(files)} buckets; rows={raw_rows:,}", flush=True)
    matrices = {k: np.concatenate(parts[k]) for k in models}
    sizes = pd.read_csv(ROOT / "results/eoa_only_kmeans5/cluster_sizes.csv")
    if len(all_wallets) != int(sizes.wallet_count.sum()):
        raise ValueError("Reconstructed wallet universe differs from annual EOA universe")
    checks = []
    for k, states in matrices.items():
        old = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/temporal_validation/monthly_behavior_state_summary.csv", dtype={"month": str})
        for j, month in enumerate(MONTHS):
            ref = old.set_index("month").loc[month]
            vals = states[:, j]
            counts = np.bincount(vals[vals >= 0], minlength=k)
            n = int(counts.sum())
            max_diff = max(abs(counts[c]/n - ref[f"state_C{c}_share"]) for c in range(k))
            checks.append(dict(k=k, month=month, reconstructed_active_wallets=n,
                legacy_active_wallets=int(ref.active_wallets_assigned), max_state_share_difference=max_diff))
            if n != int(ref.active_wallets_assigned) or max_diff > 1e-6:
                pd.DataFrame(checks).to_csv(out / "reconstruction_checks.csv", index=False)
                raise ValueError(f"Reconstruction does not reproduce legacy states: K{k}, {month}, share difference={max_diff}")
    pd.DataFrame(checks).to_csv(out / "reconstruction_checks.csv", index=False)
    meta = dict(input_fingerprint=signature, wallet_count=len(all_wallets), daily_rows=raw_rows,
        bucket_count=len(files), months=MONTHS, assignment_method="unannualised monthly features; annual scaler; annual median prototypes",
        scaling_stats=str(args.scaling_stats.resolve()), reconstruction_share_tolerance=1e-6)
    np.savez_compressed(cache, **{f"k{k}": v for k,v in matrices.items()})
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return matrices, meta


def analyse(matrices, B, seed, out):
    diagnostics, pairs, triples, summaries, matrix_rows = [], [], [], [], []
    for k, states in matrices.items():
        sizes = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/cluster_sizes.csv").set_index("cluster")
        annual = sizes.wallet_count / sizes.wallet_count.sum()
        for j, month in [(None,"ALL_WALLET_MONTHS")] + list(enumerate(MONTHS)):
            vals = states.ravel() if j is None else states[:,j]
            counts = np.bincount(vals[vals >= 0], minlength=k)
            for c in range(k):
                diagnostics.append(dict(k=k, month=month, state=c, annual_wallet_count=int(sizes.loc[c,"wallet_count"]),
                    annual_share=annual.loc[c], monthly_state_count=int(counts[c]), active_wallet_months=int(counts.sum()),
                    monthly_share=counts[c]/counts.sum(), share_difference=counts[c]/counts.sum()-annual.loc[c],
                    scaling_decision="retain_original_assignments_add_limitation"))
        total_matrix = np.zeros((k,k), dtype=np.int64)
        kpairs, ktriples = [], []
        for j in range(11):
            a,b = states[:,j], states[:,j+1]
            valid = (a>=0)&(b>=0)
            counts, obs, exp, kap = transition_stats(a[valid],b[valid],k)
            total_matrix += counts
            row = dict(k=k, month_from=MONTHS[j], month_to=MONTHS[j+1], n_wallets=int(valid.sum()),
                self_transition_count=int(np.trace(counts)), observed_self_transition=obs,
                expected_self_transition=exp, observed_minus_chance=obs-exp, cohen_kappa=kap)
            kpairs.append(row)
            # Check every cell, not just the pooled percentage, against the old output.
            old = pd.read_csv(ROOT / f"results/eoa_only_kmeans{k}/temporal_validation/monthly_state_transition_counts_long.csv", dtype={"from_month":str,"to_month":str})
            ref = old[(old.from_month==MONTHS[j])&(old.to_month==MONTHS[j+1])]
            expected_matrix = np.zeros((k,k), dtype=np.int64)
            for r in ref.itertuples(): expected_matrix[r.from_state,r.to_state] = r.wallet_count
            if not np.array_equal(counts,expected_matrix):
                raise ValueError(f"Legacy pair transition mismatch K{k} {MONTHS[j]}")
        for j in range(10):
            a,b,c = states[:,j],states[:,j+1],states[:,j+2]
            present = (a>=0)&(b>=0)&(c>=0)
            switchers = present & (a!=b)
            s0,s1,s2 = a[switchers],b[switchers],c[switchers]
            rng = np.random.default_rng(np.random.SeedSequence([seed,k,j]))
            null, exact = return_null(s0,s1,s2,k,B,rng)
            obs = np.mean(s0==s2) if len(s0) else np.nan
            exceed = int(np.sum(null>=obs)) if len(s0) else None
            row = dict(k=k, month_start=MONTHS[j], month_middle=MONTHS[j+1], month_end=MONTHS[j+2],
                n_wallets=int(present.sum()), n_initial_switchers=len(s0), n_returned=int(np.sum(s0==s2)),
                observed_return=obs, null_mean=float(np.mean(null)), exact_null_expectation=exact,
                null_std=float(np.std(null,ddof=1)), null_q025=float(np.quantile(null,.025)), null_q975=float(np.quantile(null,.975)),
                observed_minus_null=obs-float(np.mean(null)), null_exceedances=exceed,
                p_value_upper=(1+exceed)/(B+1) if exceed is not None else np.nan,
                permutations=B, seed=seed, at_permutation_resolution=exceed==0)
            ktriples.append(row)
            print(f"K{k} {MONTHS[j]} return={obs:.4f} null={np.mean(null):.4f} p={row['p_value_upper']}",flush=True)
        adjusted = holm([r["p_value_upper"] for r in ktriples])
        for r,p in zip(ktriples,adjusted): r["p_holm"] = p
        n = sum(r["n_wallets"] for r in kpairs)
        obs = sum(r["self_transition_count"] for r in kpairs)/n
        exp = sum(r["n_wallets"]*r["expected_self_transition"] for r in kpairs)/n
        ns = sum(r["n_initial_switchers"] for r in ktriples)
        summaries.append(dict(k=k, transition_observations=n, observed_self_transition=obs,
            expected_self_transition=exp, cohen_kappa=(obs-exp)/(1-exp),
            two_step_switcher_observations=ns, observed_return=sum(r["n_returned"] for r in ktriples)/ns,
            weighted_null_return=sum(r["null_mean"]*r["n_initial_switchers"] for r in ktriples)/ns,
            two_step_significant_triples_raw=sum(r["p_value_upper"]<.05 for r in ktriples),
            two_step_significant_triples_holm=sum(r["p_holm"]<.05 for r in ktriples),
            total_triples=len(ktriples), permutations=B))
        for src in range(k):
            for dst in range(k):
                matrix_rows.append(dict(k=k, from_state=src, to_state=dst,
                    count=int(total_matrix[src,dst]), probability=total_matrix[src,dst]/total_matrix[src].sum()))
        pairs.extend(kpairs); triples.extend(ktriples)
    dfs = {}
    for name, rows in [("monthly_state_diagnostic",diagnostics),("self_transition_chance",pairs),
                       ("two_step_stratified",triples),("temporal_summary",summaries),("transition_matrix",matrix_rows)]:
        dfs[name] = pd.DataFrame(rows)
        dfs[name].to_csv(out / f"{name}.csv",index=False)
    return dfs


def report(dfs,args,meta):
    out = args.out_dir
    summary = dfs["temporal_summary"]
    network = pd.read_csv(ROOT / "results_v2/network_k4_k5_k6_B999/network_summary.csv")
    decision = pd.read_csv(ROOT / "results_v2/k4_k5_k6_decision/k4_k5_k6_decision_table_B999.csv")
    table3 = decision.merge(summary,on="k",validate="one_to_one")
    table3["internal_metrics_status"] = "legacy seed means; Person 2 must supply silhouette mean +/- sampling SD and DB"
    table3["interpretation"] = "K5 descriptive seed-stable taxonomy; compare chance-corrected temporal and network evidence; scaling caveat applies"
    table3.to_csv(out / "table_iii_temporal_inputs.csv",index=False)
    summary.to_csv(out / "table_vii_temporal_inputs.csv",index=False)
    dfs["two_step_stratified"].query("k == 5").to_csv(out / "table_viii_k5_inputs.csv",index=False)
    pooled = dfs["monthly_state_diagnostic"].query("month == 'ALL_WALLET_MONTHS'")
    r5 = summary.set_index("k").loc[5]
    text = ["# Temporal validation V2: professor Items 8, 10, 9", "",
        "## Scope and decision", "",
        "All K4/K5/K6 tests use the original monthly assignment method. Old results are untouched. "
        "Monthly states were reconstructed from complete wallet-hash daily partitions because the large legacy assignment CSVs are absent locally. "
        "Reconstruction must match all 36 monthly compositions (tolerance 1e-6), active-wallet counts and all 33 pair transition count matrices exactly before outputs are accepted.","",
        "Decision: retain original assignments and add the Item 8 limitation. Annualisation is not applied. "
        "The annual/monthly window mismatch exists in the code; composition differences are diagnostic, not causal proof of bias. "
        "Annual shares use all annual EOAs; monthly shares use active wallet-months, so activity selection also changes composition. "
        "A future annualisation decision requires professor review and recomputation of every temporal quantity.","",LIMITATION,"",
        "## Annual versus pooled monthly shares", "",pooled[["k","state","annual_share","monthly_share","share_difference"]].to_markdown(index=False),"",
        "## Chance-corrected persistence and return summary", "",summary.to_markdown(index=False),"",
        "## Methods", "",
        "Pairs include only wallets present in both adjacent calendar months; absence is missing, not a state. "
        "Expected agreement is the dot product of the pair-specific state marginals. Annual observed and expected rates "
        "are weighted by pair sample size, then kappa=(observed-expected)/(1-expected). This is not the mean of monthly kappas.","",
        "Triples include only wallets present in all three consecutive months, then restrict to s0 != s1 before any shuffling. "
        "Shuffle s2 only within the same s1 group among those switchers. This preserves the selected cohort's middle-to-final margins. "
        "Compute upper-tail p=(1+exceedances)/(B+1). Holm adjusts the ten triple tests separately for each k; raw results are also retained. "
        "Wallets recur across windows; no independence or unique-wallet interpretation of the pooled observation counts is claimed. "
        "Pooled return is descriptive; there is no invented pooled permutation p-value.","",
        f"B={args.permutations}; root seed={args.seed}; reproducible independent streams use SeedSequence([seed,k,triple_index]). "
        "Zero exceedances give the minimum attainable Monte Carlo p=1/(B+1); this does not identify the true tail probability. "
        "The analytical conditional-null expectation is also saved as an implementation check.","",
        "## Paper replacements and table handoff", "",
        "Append to Section IV-F: "+LIMITATION,"",
        f"Sections IV-F / V-E: The overall K5 self-transition rate is {100*r5.observed_self_transition:.2f}%, "
        f"compared with {100*r5.expected_self_transition:.2f}% expected under independent consecutive states "
        f"with the observed pair-specific marginals (Cohen's kappa={r5.cohen_kappa:.4f}). "
        "Rates are weighted by the number of wallets observed in each pair and are subject to the monthly-scaling limitation.","",
        "Section IV-G: To test whether the initial state carries information about the final state beyond the middle state, "
        "we restrict to wallets observed in three consecutive months that changed state in the first transition. "
        f"We permute final states within middle-state strata using B={args.permutations} permutations and report upper-tail "
        "Monte Carlo p-values and Holm correction across ten triples per k. "
        "This test cannot fully separate temporary excursions from stable differences between wallets, including regular alternation.","",
        f"Section V-F: K5 returns to its initial state in {100*r5.observed_return:.2f}% of eligible switcher observations, "
        f"versus a weighted conditional-null mean of {100*r5.weighted_null_return:.2f}%. "
        f"{int(r5.two_step_significant_triples_raw)}/10 triples are significant before correction and "
        f"{int(r5.two_step_significant_triples_holm)}/10 after Holm correction. "
        "Report these as conditional return evidence, with the scaling caveat and wallet-heterogeneity limitation; do not claim proven temporary excursions.","",
        "Table III: merge temporal inputs with Person 2's final internal metrics; show observed (chance), kappa and raw/Holm significant triples. "
        "Table VII: use the weighted summary plus the existing state-level matrix; add chance agreement and kappa. "
        "Table VIII: use table_viii_k5_inputs.csv, with B, null mean, effect, raw and adjusted p-values.","",
        "No LaTeX manuscript exists in this checkout; these are replacement text and table inputs, not edits to a final manuscript. "
        "Table V and final model-selection wording remain with Person 2 / joint integration. "
        "Send claim-changing results to the professor before finalising claims; no message has been sent automatically.","",
        "## Reproduction", "", "```powershell", "python scripts/run_temporal_validation_v2.py --permutations 99 --out-dir results_v2/temporal_k4_k5_k6_smoke", "python scripts/run_temporal_validation_v2.py --permutations 999", "```", "",
        "Local reconstruction cache is ignored by Git; compact CSVs and provenance manifest are retained. "
        f"Source daily rows={meta['daily_rows']:,}; annual wallets={meta['wallet_count']:,}; buckets={meta['bucket_count']}."]
    (out / "temporal_validation_v2_summary.md").write_text("\n".join(text),encoding="utf-8")
    (out / "paper_replacement_paragraphs.md").write_text("\n".join(text[text.index("## Paper replacements and table handoff"):text.index("## Reproduction")]),encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--daily-partitions",type=Path,default=ROOT / "results/full_eoa_temporal_signal_streaming_k5/daily_wallet_partitions")
    p.add_argument("--scaling-stats",type=Path,default=ROOT / "results_v2/temporal_k4_k5_k6/legacy_mixed_annual_scaling_stats.csv")
    p.add_argument("--out-dir",type=Path,default=ROOT / "results_v2/temporal_k4_k5_k6")
    p.add_argument("--permutations",type=int,default=999)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--workers",type=int,default=4)
    args = p.parse_args()
    if args.permutations < 2: p.error("Need at least two permutations")
    if args.workers < 1: p.error("Need at least one worker")
    args.out_dir.mkdir(parents=True,exist_ok=True)
    matrices, meta = reconstruct(args,args.out_dir)
    dfs = analyse(matrices,args.permutations,args.seed,args.out_dir)
    report(dfs,args,meta)
    print(dfs["temporal_summary"].to_string(index=False),flush=True)


if __name__ == "__main__":
    main()
