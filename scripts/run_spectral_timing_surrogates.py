"""Test spectral timing organization against within-wallet daily permutations.

Uniform wallet sample; shuffle all 365 daily counts including zeros. This
preserves transaction counts, active days and daily count magnitudes exactly.
Tests concern population-mean spectral summaries, not individual periodicity.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_temporal_validation_v2 import holm

ROOT=Path(__file__).resolve().parents[1]


def spectral(x):
    z=np.log1p(x); z-=z.mean(axis=1,keepdims=True)
    power=np.abs(np.fft.rfft(z,axis=1)[:,1:])**2
    total=power.sum(axis=1,keepdims=True)
    norm=np.divide(power,total,out=np.zeros_like(power),where=total>0)
    freq=np.fft.rfftfreq(x.shape[1],d=1)[1:]
    ent=-np.sum(norm*np.log2(np.maximum(norm,np.finfo(float).tiny)),axis=1)
    return np.column_stack([norm[:,freq<1/60].sum(axis=1),norm.max(axis=1),-ent]),total.ravel()>0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir",type=Path,required=True)
    p.add_argument("--wallets",type=int,default=500)
    p.add_argument("--permutations",type=int,default=999)
    p.add_argument("--seed",type=int,default=492)
    p.add_argument("--out-dir",type=Path,default=ROOT/"results_v3/spectral_surrogates")
    args=p.parse_args()
    if args.wallets<10 or args.permutations<99:p.error("At least 10 wallets and 99 permutations")
    args.out_dir.mkdir(parents=True,exist_ok=True)
    cohort=pd.read_csv(ROOT/"results/eoa_only_kmeans4/wallet_eoa_only_kmeans_clusters.csv",usecols=["wallet"],dtype=str)
    wallets=pd.Index(cohort.wallet.sample(min(args.wallets,len(cohort)),random_state=args.seed).str.removeprefix("0x"))
    days=pd.date_range("2022-01-01","2022-12-31").strftime("%Y-%m-%d")
    signal=np.zeros((len(wallets),365))
    for m in range(1,13):
        path=args.data_dir/f"wallet_daily_clean_2022{m:02d}.csv"
        for d in pd.read_csv(path,usecols=["wallet","date","tx_count"],dtype={"wallet":str},chunksize=1000000):
            d.wallet=d.wallet.str.removeprefix("0x")
            d=d[d.wallet.isin(wallets)]
            if len(d):
                wi=wallets.get_indexer(d.wallet); di=days.get_indexer(d.date)
                if (di<0).any():raise ValueError("Dates outside 2022")
                v=pd.to_numeric(d.tx_count,errors="raise").to_numpy(float)
                if not np.isfinite(v).all() or (v<0).any():raise ValueError("Invalid counts")
                np.add.at(signal,(wi,di),v)
        print(f"Timing surrogate inputs: month {m}",flush=True)
    obs,valid=spectral(signal)
    if not valid.any():raise ValueError("No positive-power signals")
    signal=signal[valid];obs=obs[valid].mean(axis=0)
    rng=np.random.default_rng(args.seed);null=[]
    for _ in range(args.permutations):
        perm=np.take_along_axis(signal,np.argsort(rng.random(signal.shape),axis=1),axis=1)
        metrics,_=spectral(perm);null.append(metrics.mean(axis=0))
    null=np.asarray(null)
    rows=[]
    for j,name in enumerate(["low_frequency_share","peak_share","negative_entropy"]):
        rows.append(dict(metric=name,wallets=len(signal),observed_mean=obs[j],null_mean=null[:,j].mean(),
            effect=obs[j]-null[:,j].mean(),p=(1+np.sum(null[:,j]>=obs[j]))/(args.permutations+1)))
    result=pd.DataFrame(rows);result["p_holm"]=holm(result.p)
    result.to_csv(args.out_dir/"timing_surrogate_tests.csv",index=False)
    pd.DataFrame(null,columns=[r["metric"] for r in rows]).to_csv(args.out_dir/"null_replicates.csv",index=False)
    (args.out_dir/"manifest.json").write_text(json.dumps(dict(seed=args.seed,permutations=args.permutations,
        sampled_wallets=len(wallets),positive_power_wallets=int(valid.sum()),zero_power_excluded=int((~valid).sum()),
        observed_days=365,transform="log1p then subtract wallet mean; exclude DC; normalize by total non-DC power",
        null="Within-wallet permutation of all daily counts including zeros; full histogram preserved",
        inference="Three upper-tail tests on sample-mean summaries; negative entropy tests concentration; no claim of recurring cycles or independent population coverage"),indent=2))
    print(result.to_string(index=False),flush=True)


if __name__=="__main__":main()
