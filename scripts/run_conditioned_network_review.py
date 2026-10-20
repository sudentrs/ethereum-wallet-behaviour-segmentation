"""Monthly sampled-edge full-mixing and degree-stratified wallet-label nulls.

Coverage and degree strata use all non-self transfers with two labelled EOAs.
Uniform priority sampling retains at most 50,000 transfer events per month.
Conditioning uses logarithmic in/out transfer-count bins, not exact degrees.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_temporal_validation_v2 import holm

ROOT=Path(__file__).resolve().parents[1]


def measures(y,src,dst,k):
    m=np.bincount(y[src]*k+y[dst],minlength=k*k).reshape(k,k).astype(float)
    prob=m/m.sum();expected=prob.sum(1)[:,None]*prob.sum(0)[None,:]
    mask=prob>0
    mi=float(np.sum(prob[mask]*np.log2(prob[mask]/expected[mask])))
    return np.array([np.trace(prob),mi])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-root",type=Path,required=True)
    p.add_argument("--months",nargs="+",default=[f"2022{m:02d}" for m in range(1,13)])
    p.add_argument("--out-dir",type=Path,default=ROOT/"results_v3/conditioned_network")
    p.add_argument("--sample-edges",type=int,default=50000)
    p.add_argument("--permutations",type=int,default=999)
    p.add_argument("--seed",type=int,default=492)
    args=p.parse_args()
    if args.permutations<99:p.error("At least 99 permutations")
    args.out_dir.mkdir(parents=True,exist_ok=True)
    labs={}
    for k in [4,5,6]:
        d=pd.read_csv(ROOT/f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv",dtype={"wallet":str})
        d.wallet=d.wallet.str.removeprefix("0x")
        if d.wallet.duplicated().any():raise ValueError("Duplicate cohort wallet")
        labs[k]=d.set_index("wallet").cluster
    wallets=labs[4].index
    for k in [5,6]:
        labs[k]=labs[k].reindex(wallets)
        if labs[k].isna().any():raise ValueError("Cohort mismatch")
    n=len(wallets);results=[];coverage=[]
    for month in args.months:
        path=args.raw_root/f"{month}.tsv"/f"{month}.tsv"
        if not path.is_file():path=args.raw_root/f"{month}.tsv"
        srcs=[];dsts=[];prior=[];ind=np.zeros(n,dtype=np.int64);out=np.zeros(n,dtype=np.int64)
        rng=np.random.default_rng(np.random.SeedSequence([args.seed,int(month)]))
        raw=eligible=nonself=0
        for d in pd.read_csv(path,sep="\t",usecols=["sender","recipient"],dtype=str,chunksize=500000):
            raw+=len(d)
            s=wallets.get_indexer(d.sender.str.lower().str.removeprefix("0x"))
            t=wallets.get_indexer(d.recipient.str.lower().str.removeprefix("0x"))
            nonself+=int(np.sum(d.sender.to_numpy()!=d.recipient.to_numpy()))
            valid=(s>=0)&(t>=0)&(s!=t);s=s[valid];t=t[valid];eligible+=len(s)
            out+=np.bincount(s,minlength=n);ind+=np.bincount(t,minlength=n)
            srcs.extend(s.tolist());dsts.extend(t.tolist());prior.extend(rng.random(len(s)).tolist())
            if len(srcs)>args.sample_edges:
                ix=np.argpartition(prior,args.sample_edges-1)[:args.sample_edges]
                srcs=np.asarray(srcs)[ix].tolist();dsts=np.asarray(dsts)[ix].tolist();prior=np.asarray(prior)[ix].tolist()
        if not eligible:raise ValueError(f"No eligible edges: {month}")
        src=np.asarray(srcs);dst=np.asarray(dsts)
        endpoints, inverse=np.unique(np.concatenate([src,dst]),return_inverse=True)
        local_src,local_dst=inverse[:len(src)],inverse[len(src):]
        # Shuffle all participating wallet labels, including unsampled endpoints.
        active=np.flatnonzero((ind+out)>0)
        bins=np.floor(np.log2(ind[active]+1)).astype(int)*64+np.floor(np.log2(out[active]+1)).astype(int)
        strata=[active[bins==b] for b in np.unique(bins)]
        groups=[("unrestricted",[active]),("in_out_activity_bins",strata)]
        coverage.append(dict(month=month,raw_transfers=raw,nonself_transfers=nonself,
            two_labelled_eoa_nonself=eligible,coverage_of_raw=eligible/raw,coverage_of_nonself=eligible/nonself,
            sampled_edges=len(src),active_eoas=len(active),strata=len(strata),singleton_strata=sum(len(g)==1 for g in strata)))
        for k in [4,5,6]:
            y=labs[k].to_numpy(dtype=int);observed=measures(y,src,dst,k)
            for null_name,grps in groups:
                rng=np.random.default_rng(np.random.SeedSequence([args.seed,int(month),k,int(null_name!="unrestricted")]))
                draws=[]
                for g in grps:
                    positions=np.flatnonzero(np.isin(endpoints,g))
                    if len(positions):draws.append((positions,np.bincount(y[g],minlength=k)))
                null=np.empty((args.permutations,2))
                for b in range(args.permutations):
                    yy=np.empty(len(endpoints),dtype=int)
                    for positions,pool in draws:
                        counts=rng.multivariate_hypergeometric(pool,len(positions))
                        yy[positions]=rng.permutation(np.repeat(np.arange(k),counts))
                    null[b]=measures(yy,local_src,local_dst,k)
                for j,metric in enumerate(["same_role_ratio","role_mixing_mutual_information_bits"]):
                    results.append(dict(month=month,k=k,null=null_name,metric=metric,
                        observed=observed[j],null_mean=null[:,j].mean(),effect=observed[j]-null[:,j].mean(),
                        p=(1+np.sum(null[:,j]>=observed[j]))/(args.permutations+1)))
            print(f"Conditioned network {month} K{k} complete",flush=True)
        pd.DataFrame(coverage).to_csv(args.out_dir/"monthly_coverage.csv",index=False)
        pd.DataFrame(results).to_csv(args.out_dir/"monthly_tests_partial.csv",index=False)
    frame=pd.DataFrame(results);frame["p_holm_within_k_null_metric"]=np.nan
    for _,g in frame.groupby(["k","null","metric"]):
        frame.loc[g.index,"p_holm_within_k_null_metric"]=holm(g.p)
    frame.to_csv(args.out_dir/"monthly_tests.csv",index=False)
    (args.out_dir/"manifest.json").write_text(json.dumps(dict(months=args.months,permutations=args.permutations,
        seed=args.seed,sample_edges=args.sample_edges,
        null="Wallet labels permuted among full-month eligible EOA endpoints; conditioned variant preserves label counts within joint floor(log2(in_event_count+1)),floor(log2(out_event_count+1)) strata",
        scope="Full-month transfer-count coverage; tests use a uniform transfer-event sample. Event counts are not unique-neighbour degree. MI tests any role interaction structure including cross-role mixing. Holm separately within k/null/metric over months; no joint claim across all families. Exact-degree effects can remain within bins."),indent=2))


if __name__=="__main__":main()
