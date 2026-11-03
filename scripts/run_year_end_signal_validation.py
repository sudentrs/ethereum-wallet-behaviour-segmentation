"""Count-only full-cohort signal features, resolution checks and timing nulls.

This is a separate annual descriptive representation, not held-out prediction.
All source rows are validated before joining the historical cohort. Checkpoints
are bound to source/cohort/script hashes; only completed runs get a receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path

import duckdb
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.preprocessing import RobustScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ['active_fraction', 'longest_active_fraction', 'longest_inactive_fraction',
            'switch_fraction', 'peak_count_share', 'daily_count_cv',
            'low_frequency_share', 'medium_frequency_share', 'high_frequency_share',
            'weekly_band_share', 'monthly_band_share', 'peak_power_share', 'spectral_entropy']
TIME = list(range(6))
FREQUENCY = list(range(6, 13))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def save_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)


def holm(p):
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    out = np.empty(len(p))
    out[order] = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return out


def features(counts):
    x = np.asarray(counts, dtype=np.float64)
    n, days = x.shape
    active = x > 0
    run_a = np.zeros(n, dtype=np.int32)
    run_i = run_a.copy()
    best_a = run_a.copy()
    best_i = run_a.copy()
    for j in range(days):
        run_a = (run_a + 1) * active[:, j]
        run_i = (run_i + 1) * ~active[:, j]
        best_a = np.maximum(best_a, run_a)
        best_i = np.maximum(best_i, run_i)
    total = x.sum(axis=1)
    mean = x.mean(axis=1)
    z = np.log1p(x)
    z -= z[:, :1]
    z -= z.mean(axis=1, keepdims=True)
    power = np.abs(np.fft.rfft(z, axis=1)[:, 1:]) ** 2
    mass = power.sum(axis=1)
    norm = np.divide(power, mass[:, None], out=np.zeros_like(power), where=mass[:, None] > 0)
    f = np.fft.rfftfreq(days)[1:]
    entropy = -(norm * np.log2(np.maximum(norm, np.finfo(float).tiny))).sum(axis=1)
    def band(lo, hi):
        return norm[:, (f >= lo) & (f < hi)].sum(axis=1)
    vals = np.column_stack([
        active.mean(axis=1), best_a / days, best_i / days,
        np.count_nonzero(active[:, 1:] != active[:, :-1], axis=1) / (days - 1),
        np.divide(x.max(axis=1), total, out=np.zeros(n), where=total > 0),
        np.divide(x.std(axis=1), mean, out=np.zeros(n), where=mean > 0),
        band(0, 1/60), band(1/60, 1/14), band(1/14, .5 + 1e-9),
        band(1/8, 1/6), band(1/35, 1/25), norm.max(axis=1), entropy])
    assert np.isfinite(vals).all()
    return vals, mass > 0, total


def timing_metrics(counts):
    z = np.log1p(np.asarray(counts, dtype=float))
    z -= z[:, :1]
    z -= z.mean(axis=1, keepdims=True)
    power = np.abs(np.fft.rfft(z, axis=1)[:, 1:]) ** 2
    total = power.sum(axis=1)
    q = np.divide(power, total[:, None], out=np.zeros_like(power), where=total[:, None] > 0)
    f = np.fft.rfftfreq(counts.shape[1])[1:]
    return np.column_stack([q[:, f < 1/60].sum(axis=1), q.max(axis=1),
                            (q * np.log2(np.maximum(q, np.finfo(float).tiny))).sum(axis=1)])


def agreement(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    tab = np.zeros((a.max()+1, b.max()+1), dtype=np.int64)
    np.add.at(tab, (a, b), 1)
    r, c = linear_sum_assignment(-tab)
    return dict(ari=float(adjusted_rand_score(a,b)),
                nmi=float(normalized_mutual_info_score(a,b)),
                matched_agreement=float(tab[r,c].sum()/len(a)))


def build_signals(args, wallets, signature):
    cache = args.cache
    info = cache / 'sources.json'
    if info.exists():
        assert json.loads(info.read_text()) == signature, 'Changed source, cohort or code; use a fresh cache'
    else:
        save_json(info, signature)
    path = cache / 'daily_counts.npy'
    if path.exists():
        signals = np.lib.format.open_memmap(path, mode='r+')
        assert signals.shape == (len(wallets), 365) and signals.dtype == np.uint32
    else:
        signals = np.lib.format.open_memmap(path, mode='w+', dtype=np.uint32, shape=(len(wallets),365))
        signals[:] = 0
        signals.flush()
    cohort = pd.DataFrame({'wallet': wallets, 'idx': np.arange(len(wallets))})
    con = duckdb.connect()
    con.execute("SET threads=4")
    con.execute("SET memory_limit='1GB'")
    con.execute("SET temp_directory='" + (cache/'duckdb_tmp').resolve().as_posix().replace("'", "''") + "'")
    con.register('cohort', cohort)
    for month in range(1,13):
        receipt = cache / f'month_{month:02d}.json'
        if receipt.exists():
            print(f'Month {month}: validated checkpoint', flush=True)
            continue
        source = args.daily / f'wallet_daily_clean_2022{month:02d}.csv'
        print(f'Month {month}: validating and joining {source.name}', flush=True)
        con.execute('DROP TABLE IF EXISTS daily')
        con.execute("""CREATE TEMP TABLE daily AS SELECT
            regexp_replace(lower(trim(wallet)), '^0x', '') AS wallet,
            "date" AS day, tx_count AS tx
            FROM read_csv(?, header=true, columns={'wallet':'VARCHAR','date':'DATE',
            'total_in':'VARCHAR','total_out':'VARCHAR','tx_count':'DOUBLE'})""", [str(source)])
        raw, invalid = con.execute("""SELECT count(*), count(*) FILTER (WHERE
            wallet IS NULL OR NOT regexp_full_match(wallet,'[0-9a-f]{40}') OR day IS NULL
            OR strftime(day,'%Y%m')<>? OR tx IS NULL OR NOT isfinite(tx) OR tx<0
            OR tx<>floor(tx) OR tx>4294967295) FROM daily""", [f'2022{month:02d}']).fetchone()
        assert invalid == 0, f'Invalid daily rows: {invalid}'
        assert con.execute('SELECT 1 FROM daily GROUP BY wallet,day HAVING count(*)>1 LIMIT 1').fetchone() is None
        start = (pd.Timestamp(2022,month,1) - pd.Timestamp(2022,1,1)).days
        stop = start + pd.Timestamp(2022,month,1).days_in_month
        signals[:, start:stop] = 0
        cursor = con.execute("""SELECT c.idx, date_diff('day',DATE '2022-01-01',d.day) AS day,
                                d.tx FROM daily d INNER JOIN cohort c USING(wallet)""")
        eligible = 0
        incidence = 0
        while True:
            chunk = cursor.fetch_df_chunk(64)
            if chunk.empty:
                break
            idx = chunk.idx.to_numpy(dtype=np.int64)
            day = chunk.day.to_numpy(dtype=np.int64)
            tx = chunk.tx.to_numpy(dtype=np.uint32)
            signals[idx,day] = tx
            eligible += len(tx)
            incidence += int(tx.astype(np.uint64).sum())
        signals.flush()
        save_json(receipt, dict(month=month, raw_rows=raw, eligible_rows=eligible,
                               wallet_record_incidence=incidence, validation='format,month,integer_count,unique_wallet_day'))
        print(f'Month {month}: {eligible:,} eligible wallet-days; {incidence:,} count incidence', flush=True)
    con.close()
    return signals


def analyse(args, wallets, signals, signature):
    out, cache = args.out, args.cache
    n = len(wallets)
    feature_path = cache/'signal_features.npy'
    valid_path = cache/'positive_power.npy'
    totals_path = cache/'annual_count_totals.npy'
    if not (cache/'features_complete.json').exists():
        fs = np.lib.format.open_memmap(feature_path, mode='w+', dtype=np.float64, shape=(n,len(FEATURES)))
        valid = np.lib.format.open_memmap(valid_path, mode='w+', dtype=bool, shape=(n,))
        totals = np.lib.format.open_memmap(totals_path, mode='w+', dtype=np.float64, shape=(n,))
        for i in range(0,n,8192):
            j = min(i+8192,n)
            fs[i:j],valid[i:j],totals[i:j] = features(signals[i:j])
            if i % (8192*30) == 0:
                print(f'Signal features {j:,}/{n:,}', flush=True)
        fs.flush(); valid.flush(); totals.flush()
        save_json(cache/'features_complete.json', dict(rows=n, features=FEATURES))
    raw = np.load(feature_path, mmap_mode='r')
    valid = np.load(valid_path)
    totals = np.load(totals_path)
    annual = pd.read_csv(args.wallet_source, usecols=['total_tx'])['total_tx'].to_numpy()
    assert np.array_equal(totals,annual), 'Rebuilt daily counts differ from annual source totals'
    assert valid.any()
    ids = np.flatnonzero(valid)
    print(f'Full cohort {n:,}; positive spectral power {len(ids):,}; totals reconcile exactly', flush=True)
    summary = pd.DataFrame(raw,columns=FEATURES).describe(percentiles=[.25,.5,.75]).T
    summary.to_csv(out/'full_cohort_feature_summary.csv')
    rng = np.random.default_rng(args.seed)
    sample_ids = np.sort(rng.choice(ids,min(args.fit_sample,len(ids)),replace=False))
    eval_ids = np.sort(rng.choice(ids,min(args.eval_sample,len(ids)),replace=False))
    # CV is unbounded; all other features remain in native bounded units.
    transformed = np.array(raw, copy=True)
    transformed[:,5] = np.log1p(transformed[:,5])
    fit_rows, stability, cross, profiles, overlap = [], [], [], [], []
    all_labels = {}
    annual_labels = {k:np.load(args.annual/f'k{k}_seed492_labels.npy') for k in range(2,7)}
    for name, cols in [('time',TIME),('frequency',FREQUENCY)]:
        scaler = RobustScaler().fit(transformed[ids][:,cols])
        matrix = scaler.transform(transformed[:,cols])
        models = {}
        for k in range(2,7):
            for seed in [args.seed,args.seed+1,args.seed+2]:
                label_file = cache/f'{name}_k{k}_seed{seed}_labels.npy'
                model_file = cache/f'{name}_k{k}_seed{seed}.joblib'
                if label_file.exists() and model_file.exists():
                    labels = np.load(label_file)
                    model = joblib.load(model_file)
                else:
                    model = MiniBatchKMeans(n_clusters=k,random_state=seed,n_init=10,
                                            batch_size=8192,max_iter=200).fit(matrix[sample_ids])
                    labels = np.full(n,-1,dtype=np.int16)
                    for i in range(0,len(ids),100000):
                        ix = ids[i:i+100000]
                        labels[ix] = model.predict(matrix[ix])
                    np.save(label_file,labels)
                    joblib.dump(model,model_file)
                models[(k,seed)] = labels
                sizes = np.bincount(labels[ids],minlength=k)
                sil = float(silhouette_score(matrix[eval_ids],labels[eval_ids])) if seed == args.seed else None
                fit_rows.append(dict(representation=name,k=k,seed=seed,silhouette=sil,
                                     min_share=float(sizes.min()/len(ids)),max_share=float(sizes.max()/len(ids)),
                                     fit_sample=len(sample_ids),assigned=len(ids),labels_sha256=sha(label_file)))
                print(f'{name} K{k} seed{seed}: assigned {len(ids):,}; silhouette={sil}',flush=True)
                if seed == args.seed:
                    all_labels[(name,k)] = labels
                    frame = pd.DataFrame(raw[ids],columns=FEATURES)
                    frame['cluster'] = labels[ids]
                    prof = frame.groupby('cluster').median().reset_index()
                    prof.insert(0,'k',k); prof.insert(0,'representation',name)
                    prof['wallets'] = sizes
                    profiles.append(prof)
                    for ak,a in annual_labels.items():
                        cross.append(dict(left=f'annual_k{ak}',right=f'{name}_k{k}',n=len(ids),
                                          **agreement(a[ids],labels[ids])))
                    for ak in [3,5]:
                        tab = pd.crosstab(annual_labels[ak][ids],labels[ids])
                        for a in tab.index:
                            for b in tab.columns:
                                overlap.append(dict(annual_k=ak,representation=name,signal_k=k,
                                                    annual_cluster=int(a),signal_cluster=int(b),wallets=int(tab.loc[a,b]),
                                                    row_share=float(tab.loc[a,b]/tab.loc[a].sum())))
            for a,b in [(args.seed,args.seed+1),(args.seed,args.seed+2),(args.seed+1,args.seed+2)]:
                stability.append(dict(representation=name,k=k,seed_a=a,seed_b=b,
                                      **agreement(models[k,a][ids],models[k,b][ids])))
        joblib.dump(scaler,cache/f'{name}_scaler.joblib')
    for tk in range(2,7):
        for fk in range(2,7):
            cross.append(dict(left=f'time_k{tk}',right=f'frequency_k{fk}',n=len(ids),
                              **agreement(all_labels['time',tk][ids],all_labels['frequency',fk][ids])))
    pd.DataFrame(fit_rows).to_csv(out/'signal_model_resolution.csv',index=False)
    pd.DataFrame(stability).to_csv(out/'signal_seed_stability.csv',index=False)
    pd.DataFrame(cross).to_csv(out/'cross_representation_agreement.csv',index=False)
    pd.DataFrame(overlap).to_csv(out/'annual_signal_overlap.csv',index=False)
    pd.concat(profiles,ignore_index=True).to_csv(out/'signal_cluster_profiles.csv',index=False)
    # Sample from the complete cohort before dropping zero-power signals; retain exclusion count.
    null_ids = np.sort(np.random.default_rng(args.seed+100).choice(n,min(args.null_wallets,n),replace=False))
    null_ids_valid = null_ids[valid[null_ids]]
    sample = np.array(signals[null_ids_valid])
    obs = timing_metrics(sample).mean(axis=0)
    null = np.empty((args.permutations,3))
    null_rng = np.random.default_rng(args.seed+200)
    for b in range(args.permutations):
        permuted = np.take_along_axis(sample,np.argsort(null_rng.random(sample.shape),axis=1),axis=1)
        null[b] = timing_metrics(permuted).mean(axis=0)
        if (b+1)%100 == 0:
            print(f'Timing null {b+1}/{args.permutations}',flush=True)
    tests = pd.DataFrame(dict(metric=['low_frequency_share','peak_power_share','negative_entropy'],
                              observed=obs,null_mean=null.mean(axis=0),null_std=null.std(axis=0,ddof=1),
                              excess=obs-null.mean(axis=0),p=(1+(null>=obs).sum(axis=0))/(args.permutations+1)))
    tests['p_holm_3'] = holm(tests.p)
    tests.to_csv(out/'timing_surrogate_tests.csv',index=False)
    pd.DataFrame(null,columns=tests.metric).to_csv(out/'timing_null_replicates.csv',index=False)
    np.save(cache/'timing_sample_indices.npy',null_ids)
    # Figures are written only from the measured outputs above.
    res = pd.DataFrame(fit_rows)
    stab = pd.DataFrame(stability)
    fig,axes = plt.subplots(1,2,figsize=(7,2.5))
    for name in ['time','frequency']:
        t=res[(res.representation==name)&(res.seed==args.seed)]
        axes[0].plot(t.k,t.silhouette,'o-',label=name)
        t=stab[stab.representation==name].groupby('k').ari.agg(['mean','min','max'])
        axes[1].errorbar(t.index,t['mean'],yerr=[t['mean']-t['min'],t['max']-t['mean']],fmt='o-',label=name)
    axes[0].set(ylabel='Sample silhouette',xlabel='Signal clusters k',xticks=range(2,7))
    axes[1].set(ylabel='Full-population seed ARI',xlabel='Signal clusters k',xticks=range(2,7))
    for ax in axes: ax.legend(fontsize=8); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(out/'signal_resolution_validation.pdf'); plt.close(fig)
    overlap_df=pd.DataFrame(overlap)
    fig,axes=plt.subplots(1,2,figsize=(7,2.6))
    for ax,name in zip(axes,['time','frequency']):
        t=overlap_df[(overlap_df.annual_k==3)&(overlap_df.signal_k==3)&(overlap_df.representation==name)]
        mat=t.pivot(index='annual_cluster',columns='signal_cluster',values='row_share')
        im=ax.imshow(mat,vmin=0,vmax=1,cmap='Blues',aspect='auto')
        for (i,j),v in np.ndenumerate(mat.to_numpy()): ax.text(j,i,f'{v:.2f}',ha='center',va='center',color='white' if v>.6 else 'black')
        ax.set(title=f'Annual K3 vs {name} K3',xlabel='Signal cluster',ylabel='Annual cluster',xticks=range(3),yticks=range(3))
    fig.tight_layout(); fig.savefig(out/'signal_cross_representation.pdf'); plt.close(fig)
    manifest=dict(complete=True,cohort_size=n,positive_power_wallets=len(ids),zero_power_excluded=int((~valid).sum()),
                  seed=args.seed,seeds=[args.seed,args.seed+1,args.seed+2],k_values=list(range(2,7)),
                  features=FEATURES,time_columns=TIME,frequency_columns=FREQUENCY,
                  fit_sample=len(sample_ids),evaluation_sample=len(eval_ids),null_sample_requested=len(null_ids),
                  null_positive_power=len(null_ids_valid),null_zero_power_excluded=int(len(null_ids)-len(null_ids_valid)),
                  permutations=args.permutations,holm_test_count=3,
                  signal='365 calendar-day counts; absent days zero; no pooled amounts',
                  spectral_transform='log1p counts, subtract wallet mean, rFFT, exclude DC, normalize non-DC power',
                  scaling='log1p daily_count_cv only; full eligible population RobustScaler per representation',
                  clustering='sample-trained MiniBatchKMeans; full positive-power population assignment',
                  null='within-wallet daily permutation including zeros; preserves full daily-count histogram',
                  inference='annual descriptive signal organization, not held-out prediction, causality or proven recurring cycles',
                  annual_total_reconciliation='exact for every cohort address',sources=signature,
                  python=platform.python_version(),numpy=np.__version__,sklearn=sklearn.__version__,duckdb=duckdb.__version__)
    manifest['outputs']={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='manifest.json'}
    save_json(out/'manifest.json',manifest)
    print(tests.to_string(index=False),flush=True)
    print('COMPLETE: full-cohort signal validation',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--daily',type=Path,default=ROOT/'tsv and wallet daily/wallet daily clean')
    p.add_argument('--wallet-source',type=Path,default=ROOT/'data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv')
    p.add_argument('--cohort',type=Path,default=ROOT/'results_v3/year_end_2022_full_cohort/cohort_members.csv.gz')
    p.add_argument('--annual',type=Path,default=ROOT/'data/interim/year_end_2022_count_cohort/annual_fits_reproduced')
    p.add_argument('--cache',type=Path,default=ROOT/'data/interim/year_end_2022_signals')
    p.add_argument('--out',type=Path,default=ROOT/'results_v3/year_end_2022_count_cohort/signals')
    p.add_argument('--seed',type=int,default=492)
    p.add_argument('--fit-sample',type=int,default=100000)
    p.add_argument('--eval-sample',type=int,default=3000)
    p.add_argument('--null-wallets',type=int,default=2000)
    p.add_argument('--permutations',type=int,default=999)
    args=p.parse_args()
    args.cache.mkdir(parents=True,exist_ok=True); args.out.mkdir(parents=True,exist_ok=True)
    status=ROOT/'results_v3/year_end_2022_full_cohort/status.json'
    assert json.loads(status.read_text())['included']==2508997
    wallets=pd.read_csv(args.wallet_source,usecols=['wallet'],dtype=str).wallet.str.lower().str.removeprefix('0x')
    members=pd.read_csv(args.cohort,dtype=str)
    print('Cohort columns:',list(members),flush=True)
    member_col='wallet' if 'wallet' in members else 'address'
    historical=members[member_col].str.lower().str.removeprefix('0x')
    assert len(wallets)==2508997 and wallets.is_unique and set(wallets)==set(historical)
    assert wallets.str.fullmatch('[0-9a-f]{40}').all()
    print('Hashing 12 daily sources and cohort provenance',flush=True)
    signature=dict(cohort_sha256=sha(args.cohort),wallet_source_sha256=sha(args.wallet_source),
                   script_sha256=sha(__file__),
                   settings=dict(seed=args.seed,fit_sample=args.fit_sample,eval_sample=args.eval_sample,
                                 null_wallets=args.null_wallets,permutations=args.permutations),
                   annual_labels={str(k):sha(args.annual/f'k{k}_seed492_labels.npy') for k in range(2,7)},
                   daily={str(m):sha(args.daily/f'wallet_daily_clean_2022{m:02d}.csv') for m in range(1,13)})
    with threadpool_limits(limits=4):
        signals=build_signals(args,wallets,signature)
        analyse(args,wallets,signals,signature)


if __name__=='__main__':
    main()
