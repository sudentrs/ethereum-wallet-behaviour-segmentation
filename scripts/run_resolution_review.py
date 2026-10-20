"""Reproducible sample diagnostics and full-cohort cross-resolution overlap.

The sweep is exploratory and is not a retrospective proof that K4-K6 are optimal.
"""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score, davies_bouldin_score
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--features",type=Path,default=ROOT/"wallet_eoa_only_kmeans6_features_robust_scaled/wallet_eoa_only_kmeans6_features_robust_scaled.csv")
    p.add_argument("--out-dir",type=Path,default=ROOT/"results_v3/resolution_review")
    p.add_argument("--sample-size",type=int,default=20000)
    p.add_argument("--seeds",type=int,nargs="+",default=[492,493,494,495,496])
    args=p.parse_args()
    if args.sample_size<100 or len(args.seeds)<2:
        p.error("Need at least 100 wallets and two seeds")
    out=args.out_dir; out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(492)
    reservoir=None; seen=0
    # Uniform priority reservoir across all input rows, not a prefix sample.
    for d in pd.read_csv(args.features,chunksize=100000,dtype={"wallet":str}):
        d["_priority"]=rng.random(len(d)); seen+=len(d)
        reservoir=d if reservoir is None else pd.concat([reservoir,d],ignore_index=True)
        reservoir=reservoir.nsmallest(args.sample_size,"_priority")
    sample=reservoir.drop(columns="_priority").reset_index(drop=True)
    cols=[c for c in sample.columns if c not in {"wallet","cluster","old_cluster","k_cluster"}]
    x=sample[cols].to_numpy(float)
    if not np.isfinite(x).all(): raise ValueError("Non-finite feature values")
    sample.to_csv(out/"diagnostic_sample.csv.gz",index=False,compression="gzip")
    rows=[]; labels={}
    for k in range(2,11):
        runs=[]
        for seed in args.seeds:
            model=MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=4096,random_state=seed)
            y=model.fit_predict(x); runs.append(y)
            sizes=np.bincount(y,minlength=k)/len(y)
            rows.append(dict(k=k,seed=seed,silhouette=silhouette_score(x,y,sample_size=min(2000,len(x)),random_state=492),
                davies_bouldin=davies_bouldin_score(x,y),min_share=sizes.min(),max_share=sizes.max(),inertia=model.inertia_))
        labels[k]=runs[0]
        print(f"Sweep K{k} complete",flush=True)
    raw=pd.DataFrame(rows); raw.to_csv(out/"sweep_runs.csv",index=False)
    summary=raw.groupby("k").agg(silhouette_mean=("silhouette","mean"),silhouette_sd=("silhouette","std"),
        db_mean=("davies_bouldin","mean"),db_sd=("davies_bouldin","std"),min_share=("min_share","min"))
    stability=[]; sensitivity=[]
    activity=[c for c in cols if c in {"active_days_observed","activity_span_days","activity_density","total_tx","avg_daily_tx_count","max_daily_tx_count","std_daily_tx_count","tx_count_cv","tx_concentration_ratio"}]
    value=[c for c in cols if any(v in c for v in ["total_in","total_out","flow"])]
    groups={"value":value,"activity":activity,"other":[c for c in cols if c not in set(value+activity)]}
    for k in [4,5,6]:
        runs=[MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=4096,random_state=s).fit_predict(x) for s in args.seeds]
        for i,j in combinations(range(len(runs)),2):
            stability.append(dict(k=k,kind="seed_pair",replicate_a=i,replicate_b=j,ari=adjusted_rand_score(runs[i],runs[j])))
        for seed in args.seeds:
            rr=np.random.default_rng(seed); fit=rr.choice(len(x),int(.8*len(x)),replace=False)
            m=MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=4096,random_state=seed).fit(x[fit])
            stability.append(dict(k=k,kind="subsample_80_percent",replicate_a=seed,replicate_b=492,ari=adjusted_rand_score(labels[k],m.predict(x))))
        equal=x.copy()
        for group in groups.values():
            if group: equal[:,[cols.index(c) for c in group]]/=np.sqrt(len(group))
        variants={"equal_group_distance_weight":equal,"count_only":sample[activity].to_numpy(float)}
        for name,z in variants.items():
            yy=MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=4096,random_state=492).fit_predict(z)
            sensitivity.append(dict(k=k,representation=name,ari=adjusted_rand_score(labels[k],yy),nmi=normalized_mutual_info_score(labels[k],yy)))
        for name,model in [("full_kmeans",KMeans(n_clusters=k,n_init=10,random_state=492)),
                           ("diagonal_gmm",GaussianMixture(n_components=k,covariance_type="diag",n_init=3,random_state=492))]:
            yy=model.fit_predict(x)
            sensitivity.append(dict(k=k,representation=name,ari=adjusted_rand_score(labels[k],yy),nmi=normalized_mutual_info_score(labels[k],yy)))
    pd.DataFrame(stability).to_csv(out/"stability_replicates.csv",index=False)
    pd.DataFrame(sensitivity).to_csv(out/"representation_algorithm_sensitivity.csv",index=False)
    summary.to_csv(out/"sweep_summary.csv")
    fig,axes=plt.subplots(1,2,figsize=(9,3.5))
    axes[0].errorbar(summary.index,summary.silhouette_mean,yerr=summary.silhouette_sd,marker="o")
    axes[1].errorbar(summary.index,summary.db_mean,yerr=summary.db_sd,marker="o")
    for ax,title in zip(axes,["Silhouette (higher)","Davies-Bouldin (lower)"]):
        ax.set(xlabel="Number of clusters",title=title); ax.set_xticks(range(2,11))
    fig.tight_layout(); fig.savefig(out/"k2_k10_diagnostics.pdf"); plt.close(fig)
    full={}
    for k in [4,5,6]:
        d=pd.read_csv(ROOT/f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv",dtype={"wallet":str})
        if d.wallet.duplicated().any():raise ValueError("Duplicate wallet labels")
        full[k]=d.set_index("wallet").cluster
    overlaps=[]
    for a,b in combinations([4,5,6],2):
        d=pd.concat([full[a].rename("a"),full[b].rename("b")],axis=1)
        if d.isna().any().any():raise ValueError("Candidate cohorts differ")
        tab=pd.crosstab(d.a,d.b); tab.to_csv(out/f"k{a}_k{b}_overlap_counts.csv")
        row=tab.div(tab.sum(1),axis=0); row.to_csv(out/f"k{a}_k{b}_overlap_row_shares.csv")
        overlaps.append(dict(k_a=a,k_b=b,n=len(d),ari=adjusted_rand_score(d.a,d.b),nmi=normalized_mutual_info_score(d.a,d.b)))
        fig,ax=plt.subplots(figsize=(5,4)); im=ax.imshow(row,cmap="Blues",vmin=0,vmax=1)
        ax.set(xlabel=f"K{b} role",ylabel=f"K{a} role",title="Cross-resolution overlap (row fractions)")
        ax.set_xticks(range(b));ax.set_yticks(range(a))
        for i in range(a):
            for j in range(b):ax.text(j,i,f"{row.iloc[i,j]:.2f}",ha="center",va="center",color="white" if row.iloc[i,j]>.55 else "black")
        fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(out/f"k{a}_k{b}_overlap.pdf");plt.close(fig)
    pd.DataFrame(overlaps).to_csv(out/"cross_resolution_summary.csv",index=False)
    (out/"manifest.json").write_text(json.dumps(dict(sample_wallets=len(x),population_rows=seen,seeds=args.seeds,
        reference_seed=args.seeds[0],reference_selection="prespecified first seed, not best observed run",feature_columns=cols,
        feature_file=str(args.features.resolve()),sample_sha256=hashlib.sha256(sample.to_csv(index=False).encode()).hexdigest(),
        interpretation="Exploratory sample diagnostics; not full-population algorithm comparisons. Input scaling was previously fitted on the annual population. Seed SD is variability across fits on one diagnostic sample, not a population confidence interval. Count-only excludes token amounts and direction inferred from amounts. Group weighting uses disjoint value/activity/other groups, not causal attribution."),indent=2),encoding="utf-8")


if __name__=="__main__":
    with threadpool_limits(limits=4):main()
