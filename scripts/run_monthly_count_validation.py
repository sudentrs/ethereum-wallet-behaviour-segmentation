"""Frozen, count-only monthly state validation; annual labels define the EOA cohort only.

Fit preprocessing and prototypes on January-June, then evaluate July-December.
Monthly labels have their own meaning and must not be matched to annual role IDs.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import sys
from pathlib import Path

import joblib
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import RobustScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_temporal_validation_v2 import holm, return_null, transition_stats

MONTHS = [f"2022{m:02d}" for m in range(1, 13)]
FEATURES = ["tx_per_calendar_day", "active_day_fraction", "tx_per_active_day",
            "daily_count_cv", "peak_count_share", "span_fraction"]


def month_features(path, cohort_parquet, month):
    """Aggregate one wallet-day source without retaining chunk-level copies in RAM."""
    days = calendar.monthrange(int(month[:4]), int(month[4:]))[1]
    con = duckdb.connect()
    try:
        a = con.execute("""
            WITH daily AS (
                SELECT lower(trim(wallet)) AS wallet, "date" AS day,
                       tx_count::DOUBLE AS tx_count
                FROM read_csv_auto(?, header=true,
                    columns={'wallet':'VARCHAR', 'date':'DATE',
                             'total_in':'DOUBLE', 'total_out':'DOUBLE',
                             'tx_count':'DOUBLE'})
            ), eligible AS (
                SELECT d.* FROM daily AS d
                INNER JOIN read_parquet(?) AS c USING (wallet)
                WHERE d.tx_count > 0
            )
            SELECT wallet, count(*) AS n, sum(tx_count) AS total,
                   sum(tx_count * tx_count) AS squares, max(tx_count) AS peak,
                   min(day) AS first, max(day) AS last
            FROM eligible
            GROUP BY wallet
        """, [str(path), str(cohort_parquet)]).fetchdf()
    finally:
        con.close()
    if a.empty:
        raise ValueError(f"No eligible activity in {path}")
    a = a.set_index("wallet")
    if (a.n > days).any():
        raise ValueError("More active observations than days; verify unique wallet-day input")
    mean = a.total / days
    std = np.sqrt(np.maximum(0, a.squares / days - mean ** 2))
    out = pd.DataFrame(index=a.index)
    out["tx_per_calendar_day"] = a.total / days
    out["active_day_fraction"] = a.n / days
    out["tx_per_active_day"] = a.total / a.n
    out["daily_count_cv"] = std / mean
    out["peak_count_share"] = a.peak / a.total
    out["span_fraction"] = ((a["last"] - a["first"]).dt.days + 1) / days
    return out.reset_index()


def transform(frame):
    x = frame[FEATURES].to_numpy(dtype=float)
    x[:, [0, 2, 3]] = np.log1p(x[:, [0, 2, 3]])
    if not np.isfinite(x).all():
        raise ValueError("Invalid monthly features")
    return x


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument("--cohort", type=Path, default=ROOT / "results/eoa_only_kmeans4/wallet_eoa_only_kmeans_clusters.csv")
    p.add_argument("--out-dir", type=Path, default=ROOT / "results_v3/monthly_count_validation")
    p.add_argument("--permutations", type=int, default=999)
    p.add_argument("--seed", type=int, default=492)
    p.add_argument("--sample-per-month", type=int, default=20000)
    p.add_argument("--chunksize", type=int, default=1000000)
    p.add_argument("--k-values", default="4,5,6",
                   help="Comma-separated monthly state resolutions; separate from annual labels.")
    args = p.parse_args()
    if args.permutations < 99 or args.sample_per_month < 100:
        p.error("Use at least 99 permutations and 100 training rows per month")
    k_values = [int(value) for value in args.k_values.split(",") if value.strip()]
    if not k_values or min(k_values) < 2:
        p.error("k-values must contain integers >= 2")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    cohort = pd.read_csv(args.cohort, usecols=["wallet"], dtype=str).wallet
    cohort = cohort.str.lower().str.strip().str.removeprefix("0x")
    if cohort.duplicated().any():
        raise ValueError("Duplicate cohort wallets")
    cohort_digest = hashlib.sha256("\n".join(sorted(cohort)).encode()).hexdigest()
    cohort_parquet = args.out_dir / "cohort_wallets.parquet"
    if not cohort_parquet.exists():
        pd.DataFrame({"wallet": cohort}).to_parquet(cohort_parquet, index=False)
    source = []
    samples = []
    for month in MONTHS:
        path = args.data_dir / f"wallet_daily_clean_{month}.csv"
        stat = path.stat()
        sig = hashlib.sha256(f"{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}:{cohort_digest}:{Path(__file__).read_bytes()!r}".encode()).hexdigest()
        cache = args.out_dir / f"monthly_features_{month}.csv.gz"
        marker = cache.with_suffix(".signature")
        if not cache.exists() or not marker.exists() or marker.read_text() != sig:
            f = month_features(path, cohort_parquet, month)
            f.to_csv(cache, index=False, compression="gzip")
            marker.write_text(sig)
        else:
            f = pd.read_csv(cache, dtype={"wallet": str})
        if month <= "202206":
            samples.append(f.sample(min(len(f), args.sample_per_month), random_state=args.seed + int(month)))
        source.append(dict(month=month, path=str(path.resolve()), size=stat.st_size,
                           mtime_ns=stat.st_mtime_ns, active_wallets=len(f)))
        print(f"{month}: {len(f):,} active EOA wallets", flush=True)
    train = pd.concat(samples, ignore_index=True)
    scaler = RobustScaler().fit(transform(train))
    x = scaler.transform(transform(train))
    models = {k: MiniBatchKMeans(n_clusters=k, n_init=10, random_state=args.seed,
                                batch_size=4096).fit(x) for k in k_values}
    joblib.dump(dict(scaler=scaler, models=models, features=FEATURES), args.out_dir / "frozen_monthly_models.joblib")
    states = {k: np.full((len(cohort), 12), -1, dtype=np.int8) for k in models}
    index = pd.Index(cohort)
    profiles, coverage = [], []
    for j, month in enumerate(MONTHS):
        f = pd.read_csv(args.out_dir / f"monthly_features_{month}.csv.gz", dtype={"wallet": str})
        idx = index.get_indexer(f.wallet)
        if (idx < 0).any():
            raise ValueError("Feature cache contains wallets outside cohort")
        z = scaler.transform(transform(f))
        for k, model in models.items():
            label = model.predict(z)
            states[k][idx, j] = label
            temp = f.assign(state=label).groupby("state")[FEATURES].median().reset_index()
            temp["k"], temp["month"] = k, month
            profiles.append(temp)
        coverage.append(dict(month=month, active=len(f), absent=len(cohort)-len(f), cohort=len(cohort)))
    np.savez_compressed(args.out_dir / "monthly_states.npz", **{f"k{k}": a for k,a in states.items()})
    pd.DataFrame(coverage).to_csv(args.out_dir / "monthly_coverage.csv", index=False)
    pd.concat(profiles).to_csv(args.out_dir / "monthly_role_profiles.csv", index=False)
    pairs, triples, entropy = [], [], []
    for k, a in states.items():
        pooled = np.zeros((k,k), dtype=np.int64)
        # Only held-out July-December windows support confirmatory temporal claims.
        for j in range(6, 11):
            valid = (a[:,j]>=0) & (a[:,j+1]>=0)
            counts, obs, exp, kap = transition_stats(a[valid,j], a[valid,j+1], k)
            pooled += counts
            pairs.append(dict(k=k, month_from=MONTHS[j], month_to=MONTHS[j+1],
                              n=int(valid.sum()), observed=obs, chance=exp, kappa=kap))
        for j in range(6, 10):
            valid = (a[:,j]>=0)&(a[:,j+1]>=0)&(a[:,j+2]>=0)&(a[:,j]!=a[:,j+1])
            s0,s1,s2 = a[valid,j],a[valid,j+1],a[valid,j+2]
            null, expected = return_null(s0,s1,s2,k,args.permutations,
                np.random.default_rng(np.random.SeedSequence([args.seed,k,j])))
            obs = float(np.mean(s0 == s2)) if len(s0) else np.nan
            triples.append(dict(k=k, month_start=MONTHS[j], n_switchers=len(s0), observed=obs,
                null_mean=float(np.mean(null)), exact_expectation=expected,
                p=(1+int(np.sum(null>=obs)))/(args.permutations+1) if len(s0) else np.nan))
        probs = np.divide(pooled, pooled.sum(axis=1, keepdims=True),
                          out=np.zeros_like(pooled, dtype=float), where=pooled.sum(axis=1, keepdims=True)>0)
        pd.DataFrame(probs).to_csv(args.out_dir / f"k{k}_heldout_transition_matrix.csv", index=False)
        rowp = pooled.sum(1) / max(1, pooled.sum())
        marginal = pooled.sum(0) / max(1, pooled.sum())
        h = lambda q: -float(np.sum(q[q>0]*np.log2(q[q>0])))
        conditional = sum(rowp[i]*h(probs[i]) for i in range(k))
        entropy.append(dict(k=k, next_state_entropy=h(marginal), conditional_entropy=conditional,
                            entropy_reduction=1-conditional/h(marginal) if h(marginal)>0 else np.nan))
        fig,ax = plt.subplots(figsize=(5,4))
        im=ax.imshow(probs,vmin=0,vmax=1,cmap="viridis")
        ax.set(xlabel="Next monthly state",ylabel="Current monthly state",title=f"K{k}: frozen monthly model, Jul-Dec")
        ax.set_xticks(range(k)); ax.set_yticks(range(k))
        for i in range(k):
            for j in range(k):
                ax.text(j,i,f"{probs[i,j]:.2f}",ha="center",va="center",color="white" if probs[i,j]<.5 else "black")
        fig.colorbar(im,ax=ax); fig.tight_layout()
        fig.savefig(args.out_dir / f"k{k}_heldout_transition_matrix.pdf"); plt.close(fig)
    t = pd.DataFrame(triples)
    t["p_holm_all_12_tests"] = holm(t.p)
    t.to_csv(args.out_dir / "heldout_two_step_returns.csv", index=False)
    pd.DataFrame(pairs).to_csv(args.out_dir / "heldout_persistence.csv", index=False)
    pd.DataFrame(entropy).to_csv(args.out_dir / "heldout_entropy.csv", index=False)
    manifest = dict(training_months=MONTHS[:6], evaluation_months=MONTHS[6:],
        cohort_size=len(cohort), cohort_sha256=hashlib.sha256(args.cohort.read_bytes()).hexdigest(),
        k_values=k_values,
        features=FEATURES, seed=args.seed, permutations=args.permutations,
        source=source, feature_units="counts only; no token amounts", absence="missing, not a state",
        interpretation="Monthly state IDs are separate from annual IDs. Training samples are balanced by month, not by wallet. Daily inputs must be unique wallet-day rows. Held-out evaluation fixes models but is conditional on the retrospectively defined annual EOA cohort.")
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Completed frozen monthly validation", flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
