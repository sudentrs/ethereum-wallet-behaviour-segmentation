"""Later-period prediction of next-month participation from frozen monthly states.

Train on active wallets in Jan-May pairs; evaluate Jul-Nov pairs. Compare
state-only frequency predictions with constant and count-based logistic baselines.
This evaluates monthly count states, not the original annual pooled-value roles.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir",type=Path,default=ROOT/"results_v3/monthly_count_validation")
    p.add_argument("--out-dir",type=Path,default=ROOT/"results_v3/participation_task")
    args=p.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    cohort=pd.read_csv(ROOT/"results/eoa_only_kmeans4/wallet_eoa_only_kmeans_clusters.csv",usecols=["wallet"],dtype=str)
    index=pd.Index(cohort.wallet.str.removeprefix("0x"))
    with np.load(args.input_dir/"monthly_states.npz") as z:
        states={k:z[f"k{k}"] for k in [4,5,6]}
    train=[];test=[]
    for j in list(range(5))+list(range(6,11)):
        month=f"2022{j+1:02d}"
        f=pd.read_csv(args.input_dir/f"monthly_features_{month}.csv.gz",dtype={"wallet":str})
        if j<5:f=f.sample(min(50000,len(f)),random_state=492+j)
        idx=index.get_indexer(f.wallet)
        if (idx<0).any():raise ValueError("Cohort mismatch")
        f=f[["tx_per_calendar_day","active_day_fraction"]].copy()
        f["target"]=(states[4][idx,j+1]>=0).astype(int)
        for k in states:f[f"k{k}"]=states[k][idx,j]
        f["month"]=month
        (train if j<5 else test).append(f)
    training=pd.concat(train,ignore_index=True)
    cols=["tx_per_calendar_day","active_day_fraction"]
    def features(d):
        a=d[cols].to_numpy(float);a[:,0]=np.log1p(a[:,0]);return a
    clf=LogisticRegression(max_iter=1000,random_state=492).fit(features(training),training.target)
    rates={k:training.groupby(f"k{k}").target.agg(["sum","count"]) for k in states}
    results=[]
    for d in test:
        base=float(training.target.mean());y=d.target.to_numpy()
        predictions={"constant_training_prevalence":np.full(len(y),base),
                     "activity_logistic":clf.predict_proba(features(d))[:,1]}
        for k,r in rates.items():predictions[f"k{k}_state_only"]=d[f"k{k}"].map((r["sum"]+1)/(r["count"]+2)).fillna(base).to_numpy()
        for name,q in predictions.items():
            results.append(dict(month=d.month.iloc[0],model=name,n=len(y),prevalence=y.mean(),
                brier=brier_score_loss(y,q),log_loss=log_loss(y,q,labels=[0,1]),
                roc_auc=roc_auc_score(y,q) if len(np.unique(y))>1 else np.nan))
    pd.DataFrame(results).to_csv(args.out_dir/"monthly_prediction_scores.csv",index=False)
    (args.out_dir/"manifest.json").write_text(json.dumps(dict(task="Next-month activity conditional on current-month activity",
        training_month_pairs="Jan-Feb through May-Jun",evaluation_month_pairs="Jul-Aug through Nov-Dec",
        training_rows=len(training),training_sampling="up to 50000 active wallets per month, uniform",
        limitations="Retrospective annual EOA cohort; wallets recur between training and evaluation. Tests generalize in time within this cohort, not to unseen people. No population-wide inactivity prediction. This task evaluates new monthly count states and does not independently validate annual pooled-value roles."),indent=2))


if __name__=="__main__":
    with threadpool_limits(limits=4):main()
