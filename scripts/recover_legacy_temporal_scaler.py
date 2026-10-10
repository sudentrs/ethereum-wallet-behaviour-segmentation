"""Recover the mixed-population annual scaler referenced by legacy temporal code.

Compute exact full-population quantiles using the original transform function.
Never substitute this for the EOA-only feature-space scaler; the two differ.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/features'))
from robust_scale_expanded_features import transform_series


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-features',type=Path,default=ROOT/'data/processed/wallet_kmeans6_expanded_daily_features.csv')
    p.add_argument('--out',type=Path,default=ROOT/'results_v2/temporal_k4_k5_k6/legacy_mixed_annual_scaling_stats.csv')
    args=p.parse_args()
    columns=pd.read_csv(ROOT/'data/processed/wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled_scaling_stats.csv').feature.tolist()
    print('Reading full annual mixed-population features for exact legacy quantiles',flush=True)
    raw=pd.read_csv(args.raw_features,usecols=columns)
    rows=[]
    for c in columns:
        values,kind=transform_series(c,raw.pop(c))
        q25,median,q75=values.quantile([.25,.5,.75])
        rows.append(dict(feature=c,median=median,q25=q25,q75=q75,iqr=q75-q25,transform_type=kind))
        print(f'Recovered {c}',flush=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out,index=False)
    print(f'Saved exact legacy scaler: {args.out}',flush=True)


if __name__=='__main__': main()
