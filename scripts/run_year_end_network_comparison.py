"""Compare annual K2--K6 and K3 seed sensitivity on identical monthly edges."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.apply_network_holm_correction import holm
MONTHS = [f'2022{m:02d}' for m in range(1, 13)]
RUNS = [(k, 492) for k in range(2, 7)] + [(3, 493), (3, 494)]


@lru_cache(maxsize=1)
def compiled_counts():
    try:
        from numba import njit, prange, set_num_threads
        set_num_threads(4)
    except ImportError:
        return None
    @njit(parallel=True,cache=False)
    def count(local,src,dst,permutations):
        counts=np.zeros((len(local),len(permutations)),dtype=np.int64)
        for r in prange(len(permutations)):
            for edge in range(len(src)):
                a,b=permutations[r,src[edge]],permutations[r,dst[edge]]
                for j in range(len(local)):
                    counts[j,r] += local[j,a]==local[j,b]
        return counts
    return count


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def sample_update(sample, src, dst, rng, limit):
    """Uniform priority sample of eligible rows, including repeated transfers."""
    scores = rng.random(len(src))
    if sample is not None:
        scores = np.concatenate([sample[0], scores])
        src = np.concatenate([sample[1], src])
        dst = np.concatenate([sample[2], dst])
    if len(scores) > limit:
        keep = np.argpartition(scores, limit-1)[:limit]
        scores, src, dst = scores[keep], src[keep], dst[keep]
    return scores, src, dst


def compare_null(labels, src, dst, permutations, seed, accelerated=True):
    """Common wallet permutations preserve each run's endpoint-label composition."""
    endpoints, inverse = np.unique(np.concatenate([src, dst]), return_inverse=True)
    s, d = inverse[:len(src)], inverse[len(src):]
    local = labels[:, endpoints]
    observed = np.mean(local[:, s] == local[:, d], axis=1)
    rng = np.random.default_rng(seed)
    null = np.empty((len(labels), permutations))
    counter=compiled_counts() if accelerated else None
    if counter is None:
        for i in range(permutations):
            perm = rng.permutation(len(endpoints))
            for j, values in enumerate(local):
                shuffled = values[perm]
                null[j, i] = np.mean(shuffled[s] == shuffled[d])
    else:
        for start in range(0,permutations,32):
            end=min(start+32,permutations)
            perms=np.stack([rng.permutation(len(endpoints)).astype(np.int32) for _ in range(start,end)])
            null[:,start:end]=counter(local,s.astype(np.int32),d.astype(np.int32),perms)/len(src)
            if end%1024==0:
                print(f'  shared permutations: {end}/{permutations}',flush=True)
    mean = null.mean(axis=1)
    std = null.std(axis=1, ddof=1)
    return observed, mean, std, (1+(null >= observed[:, None]).sum(axis=1))/(permutations+1)


def stream_month(path, wallets, labels, sample_edges, seed, temp_dir):
    import duckdb
    con = duckdb.connect()
    con.execute('SET threads=4')
    con.execute("SET memory_limit='1GB'")
    con.execute("SET temp_directory='"+str(temp_dir).replace('\\','/').replace("'","''")+"'")
    con.register('wallet_order', pd.DataFrame({'wallet':wallets, 'idx':np.arange(len(wallets),dtype=np.int32)}))
    rng = np.random.default_rng(seed)
    sample = None
    raw = eligible = 0
    adjacency = [np.zeros((k,k),dtype=np.int64) for k, _ in RUNS]
    try:
        reader = con.execute("""
            WITH edges AS (
                SELECT regexp_replace(lower(trim(sender)), '^0x', '') AS sender,
                       regexp_replace(lower(trim(recipient)), '^0x', '') AS recipient
                FROM read_csv(?, delim='\t', header=true, all_varchar=true)
            )
            SELECT s.idx AS src, d.idx AS dst FROM edges e
            LEFT JOIN wallet_order s ON e.sender=s.wallet
            LEFT JOIN wallet_order d ON e.recipient=d.wallet
        """, [str(path)])
        if hasattr(reader,'to_arrow_reader'):
            reader=reader.to_arrow_reader(1_000_000)
        else:
            reader=reader.fetch_record_batch(1_000_000)
        for batch in reader:
            raw += len(batch)
            src = batch.column(0).fill_null(-1).to_numpy()
            dst = batch.column(1).fill_null(-1).to_numpy()
            valid = (src>=0)&(dst>=0)
            src, dst = src[valid], dst[valid]
            eligible += len(src)
            for j, (k, _) in enumerate(RUNS):
                a, b = labels[j,src].astype(np.int64), labels[j,dst]
                adjacency[j] += np.bincount(a*k+b,minlength=k*k).reshape(k,k)
            sample = sample_update(sample,src,dst,rng,sample_edges)
            if raw % 5_000_000 == 0:
                print(f'{path.parent.name}: read {raw:,}; eligible {eligible:,}',flush=True)
    finally:
        con.close()
    if not eligible:
        raise ValueError(f'No within-cohort edges in {path}')
    return raw, eligible, sample, adjacency


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-root',type=Path,required=True)
    p.add_argument('--wallet-source',type=Path,required=True)
    p.add_argument('--fit-dir',type=Path,required=True)
    p.add_argument('--out-dir',type=Path,required=True)
    p.add_argument('--cache-dir',type=Path,default=ROOT/'data/interim/year_end_network_comparison')
    p.add_argument('--sample-edges',type=int,default=200000)
    p.add_argument('--permutations',type=int,default=9999)
    p.add_argument('--seed',type=int,default=492)
    args = p.parse_args()
    if args.sample_edges < 1 or args.permutations < 99:
        p.error('Positive sample size and at least 99 permutations required')
    if 84/(args.permutations+1) > .05:
        p.error('84-test Holm family needs at least 1679 permutations to reach 0.05; use 9999')
    args.out_dir.mkdir(parents=True,exist_ok=True)
    args.cache_dir.mkdir(parents=True,exist_ok=True)
    wallets = pd.read_csv(args.wallet_source,usecols=['wallet'],dtype=str).wallet.str.lower().str.removeprefix('0x')
    cohort = pd.read_csv(ROOT/'results_v3/year_end_2022_full_cohort/cohort_members.csv.gz',dtype=str).wallet
    if wallets.duplicated().any() or set(wallets)!=set(cohort):
        raise ValueError('Wallet source must contain precisely the corrected cohort')
    label_arrays, label_manifest = [], []
    for k, seed in RUNS:
        path=args.fit_dir/f'k{k}_seed{seed}_labels.npy'
        a=np.load(path)
        if a.shape!=(len(wallets),) or not np.isin(a,np.arange(k)).all():
            raise ValueError(f'Invalid K{k} seed{seed} labels')
        label_arrays.append(a.astype(np.int8))
        label_manifest.append(dict(k=k,seed=seed,path=str(path),sha256=sha256(path)))
    labels=np.stack(label_arrays)
    archived_path=ROOT/'results_v3/year_end_2022_count_cohort/annual/archived_pre_validation/annual_artifact_manifest.json'
    if not archived_path.exists():
        archived_path=ROOT/'results_v3/year_end_2022_count_cohort/annual/annual_artifact_manifest.json'
    archived=json.loads(archived_path.read_text())
    expected={(r['k'],r['seed']):r['labels_sha256'] for r in archived['runs']}
    for item in label_manifest:
        item['archived_sha256']=expected[item['k'],item['seed']]
        item['matches_archived']=item['sha256']==item['archived_sha256']
    identity=dict(wallet_source_sha256=sha256(args.wallet_source),labels=label_manifest,
                  sample_edges=args.sample_edges,permutations=args.permutations,seed=args.seed,
                  script_sha256=sha256(Path(__file__)))
    all_rows, sources = [], []
    manifest=dict(identity,complete=False,months=MONTHS,test_count=84,
                  null='Wallet-label permutation among sampled endpoint wallets; fixed directed transfer rows, self-transfers retained',
                  scope='Within-cohort edges only; no degree-preserving rewiring or causal interpretation',
                  common_samples=True,common_permutations=True,python=platform.python_version(),numpy=np.__version__)
    (args.out_dir/'manifest.json').write_text(json.dumps(manifest,indent=2))
    for month in MONTHS:
        path=args.raw_root/f'{month}.tsv'/f'{month}.tsv'
        if not path.is_file():
            path=args.raw_root/f'{month}.tsv'
        source=dict(month=month,path=str(path),bytes=path.stat().st_size,sha256=sha256(path))
        sources.append(source)
        signature=dict(identity,raw_sha256=source['sha256'])
        marker=args.cache_dir/f'{month}.json'
        cached=args.cache_dir/f'{month}.csv'
        if marker.exists() and cached.exists() and json.loads(marker.read_text())==signature:
            rows=pd.read_csv(cached).to_dict('records')
            print(f'{month}: reusing verified cached comparison',flush=True)
        else:
            print(f'{month}: streaming shared eligible-edge sample',flush=True)
            raw, eligible, sample, matrices=stream_month(path,wallets,labels,args.sample_edges,
                np.random.SeedSequence([args.seed,int(month),0]), args.cache_dir/'duckdb_tmp')
            order=np.argsort(sample[0])
            src,dst=sample[1][order],sample[2][order]
            np.savez_compressed(args.cache_dir/f'{month}_sample.npz',src=src,dst=dst)
            observed,mean,std,pvalue=compare_null(labels,src,dst,args.permutations,
                np.random.SeedSequence([args.seed,int(month),1]))
            rows=[]
            for j,(k,seed) in enumerate(RUNS):
                matrix=matrices[j]
                pd.DataFrame(matrix).to_csv(args.out_dir/f'{month}_k{k}_seed{seed}_adjacency.csv')
                delta=observed[j]-mean[j]
                rows.append(dict(month=month,k=k,label_seed=seed,raw_rows=raw,eligible_rows=eligible,
                    coverage=eligible/raw,sample_edges=len(src),exact_same_ratio=np.trace(matrix)/eligible,
                    observed=observed[j],null_mean=mean[j],null_std=std[j],excess=delta,
                    standardized_effect=delta/std[j] if std[j]>0 else np.nan,p_raw=pvalue[j]))
            pd.DataFrame(rows).to_csv(cached,index=False)
            marker.write_text(json.dumps(signature,indent=2))
        all_rows.extend(rows)
        pd.DataFrame(all_rows).to_csv(args.out_dir/'summary_partial.csv',index=False)
        print(f'{month}: finished {len(all_rows)}/84 tests',flush=True)
    summary=pd.DataFrame(all_rows)
    if len(summary)!=84 or summary[['month','k','label_seed']].duplicated().any():
        raise ValueError('Incomplete comparison')
    summary['p_holm_84']=holm(summary.p_raw.to_numpy())
    target=args.out_dir/'network_comparison.csv'
    summary.to_csv(target,index=False)
    manifest.update(complete=True,raw_sources=sources,summary_sha256=sha256(target))
    (args.out_dir/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Completed 84 comparisons with shared monthly samples and Holm correction.',flush=True)


if __name__=='__main__':
    # Support invocation both as a module and as a script from the repo root.
    main()
