"""Compare prepared daily amounts with raw and decimals-normalized transfers.

This is a one-month provenance diagnostic on a uniform annual-wallet sample.
It cannot establish economic comparability or replace a token-aware rerun.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-tsv",type=Path,required=True)
    p.add_argument("--daily-csv",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,default=ROOT/"results_v3/token_value_audit")
    p.add_argument("--wallets",type=int,default=2000)
    args=p.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    cohort=pd.read_csv(ROOT/"results/eoa_only_kmeans4/wallet_eoa_only_kmeans_clusters.csv",usecols=["wallet"],dtype=str)
    selected=set(cohort.wallet.sample(min(args.wallets,len(cohort)),random_state=492))
    pieces=[];rows=invalid=0
    for d in pd.read_csv(args.raw_tsv,sep="\t",usecols=["sender","recipient","time","value","token_decimals","token_address"],dtype=str,chunksize=500000):
        rows+=len(d)
        d=d[d.sender.isin(selected)|d.recipient.isin(selected)].copy()
        if d.empty:continue
        amount=pd.to_numeric(d.value,errors="coerce").to_numpy(float)
        decimals=pd.to_numeric(d.token_decimals,errors="coerce").to_numpy(float)
        valid=np.isfinite(amount)&np.isfinite(decimals)&(decimals>=0)&(decimals<=255)&(decimals==np.floor(decimals))
        invalid+=int((~valid).sum());d=d.loc[valid].copy()
        d["raw"]=amount[valid];d["normalized"]=amount[valid]/np.power(10.,decimals[valid])
        d["date"]=pd.to_datetime(d.time,errors="raise").dt.strftime("%Y-%m-%d")
        for side,address in [("in","recipient"),("out","sender")]:
            a=d[d[address].isin(selected)].rename(columns={address:"wallet"})
            a=a.groupby(["wallet","date"])[["raw","normalized"]].sum().reset_index();a["direction"]=side
            pieces.append(a)
    expected=pd.concat(pieces).groupby(["wallet","date","direction"])[["raw","normalized"]].sum().reset_index()
    prepared=[]
    for d in pd.read_csv(args.daily_csv,dtype={"wallet":str},chunksize=1000000):
        d=d[d.wallet.isin(selected)]
        for side in ["in","out"]:
            a=d[["wallet","date",f"total_{side}"]].rename(columns={f"total_{side}":"prepared"});a["direction"]=side
            prepared.append(a)
    actual=pd.concat(prepared)
    if actual.duplicated(["wallet","date","direction"]).any():raise ValueError("Duplicate prepared wallet-day-direction")
    merged=expected.merge(actual,on=["wallet","date","direction"],how="outer",indicator=True)
    matched=merged[merged._merge=="both"].copy()
    nonzero=(matched.raw!=0)|(matched.normalized!=0)|(matched.prepared!=0)
    matched=matched[nonzero]
    for candidate in ["raw","normalized"]:
        matched[f"matches_{candidate}"]=np.isclose(matched.prepared,matched[candidate],rtol=1e-6,atol=1e-9)
    matched["matches_fixed_1e18"]=np.isclose(matched.prepared,matched.raw/1e18,rtol=1e-6,atol=1e-9)
    matched.to_csv(args.out_dir/"wallet_day_comparison.csv",index=False)
    summary=dict(raw_rows_read=rows,sampled_annual_wallets=len(selected),invalid_selected_transfers=invalid,
        informative_matched_rows=len(matched),merge_coverage=merged._merge.value_counts().to_dict(),
        raw_match_fraction=float(matched.matches_raw.mean()),normalized_match_fraction=float(matched.matches_normalized.mean()),
        fixed_1e18_match_fraction=float(matched.matches_fixed_1e18.mean()),
        tolerance="relative 1e-6, absolute 1e-9; float diagnostic only, not an exact accounting audit",
        scope="One supplied month, uniform annual EOA sample; does not establish the units of every historical table or comparability between tokens")
    (args.out_dir/"summary.json").write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)


if __name__=="__main__":main()
