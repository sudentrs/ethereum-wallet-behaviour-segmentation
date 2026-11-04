"""Full-month activity-conditioned network sensitivity on corrected cohort.

Stream raw transfers once to a cohort-only parquet cache. Five partitions use
the same nonself event sample; K3 additionally uses four graph sensitivities.
All 216 upper-tail tests share one Holm family (12 months x 9 x 2 nulls).
Strata are full eligible nonself in/out event counts, not unique-neighbour degree.
"""
from pathlib import Path
import json
import argparse
import hashlib
import numpy as np
import pandas as pd
import duckdb
from numba import njit,prange,set_num_threads
from scripts.run_referee_robustness import ROOT,BASE,DATA,OUT,sha,holm

CACHE=ROOT/'data/interim/referee_network'

@njit(parallel=True)
def null_counts(labels,src,dst,groups,offsets,seeds):
    out=np.zeros((len(seeds),len(labels)),dtype=np.int64)
    for b in prange(len(seeds)):
        np.random.seed(seeds[b]);perm=np.arange(labels.shape[1])
        for g in range(len(offsets)-1):
            lo,hi=offsets[g],offsets[g+1]
            for i in range(hi-lo-1,0,-1):
                j=np.random.randint(i+1)
                a,c=groups[lo+i],groups[lo+j];temp=perm[a];perm[a]=perm[c];perm[c]=temp
        for e in range(len(src)):
            s,t=perm[src[e]],perm[dst[e]]
            for r in range(len(labels)):out[b,r]+=labels[r,s]==labels[r,t]
    return out

def baseline_labels(raw):
    # Fixed descriptive rules; no network/evaluation outcome tunes thresholds.
    cuts=np.quantile(raw.total_tx,[1/3,2/3]);total=np.searchsorted(cuts,raw.total_tx,side='right').astype(np.int8)
    rule=np.where(raw.activity_span_days<=30,0,np.where(raw.active_days_observed>=24,2,1)).astype(np.int8)
    return total,rule,cuts

def make_cache(month,wallets,source):
    path=CACHE/f'{month}.parquet';marker=CACHE/f'{month}.json'
    sig=dict(source_sha256=source['sha256'],wallet_source_sha256=sha(DATA/'wallet_count_activity_features.csv'),
             normalization='lower trim remove 0x',columns='src dst token',version=1)
    if path.exists() and marker.exists() and json.loads(marker.read_text())==sig:return path
    con=duckdb.connect();con.execute('SET threads=3');con.execute("SET memory_limit='1GB'")
    con.execute("SET temp_directory='"+(CACHE/'duckdb_tmp').as_posix()+"'")
    con.register('wallets',pd.DataFrame({'wallet':wallets,'idx':np.arange(len(wallets),dtype=np.int32)}))
    # Audit existing source digest at input boundary; no cache accepted on size alone.
    source_path=ROOT/source['path']
    if sha(source_path)!=source['sha256']:raise ValueError('Raw source hash mismatch '+month)
    q="""COPY (SELECT s.idx AS src,d.idx AS dst,lower(trim(token_address)) AS token
      FROM read_csv(?,delim='\t',header=true,all_varchar=true) e
      JOIN wallets s ON regexp_replace(lower(trim(e.sender)),'^0x','')=s.wallet
      JOIN wallets d ON regexp_replace(lower(trim(e.recipient)),'^0x','')=d.wallet)
      TO ? (FORMAT PARQUET,COMPRESSION ZSTD)"""
    con.execute(q,[str(source_path),str(path)]);con.close()
    marker.write_text(json.dumps(sig,indent=2))
    print(f'network {month} raw eligible cache complete',flush=True)
    return path

def evaluate(labels,src,dst,bins,B,seed):
    endpoints,inv=np.unique(np.concatenate([src,dst]),return_inverse=True)
    s=inv[:len(src)].astype(np.int32);d=inv[len(src):].astype(np.int32);local=labels[:,endpoints]
    observed=np.mean(local[:,s]==local[:,d],axis=1)
    result=[]
    for conditioned in [False,True]:
        group=bins[endpoints] if conditioned else np.zeros(len(endpoints),dtype=int)
        order=np.argsort(group,kind='stable').astype(np.int32)
        offsets=np.r_[0,np.flatnonzero(np.diff(group[order]))+1,len(order)].astype(np.int32)
        seeds=np.random.default_rng(np.random.SeedSequence([seed,int(conditioned)])).integers(0,2**31-1,size=B,dtype=np.int64)
        null=null_counts(local,s,d,order,offsets,seeds)/len(src)
        for j in range(len(labels)):
            result.append(dict(label_index=j,null='activity_stratified' if conditioned else 'unrestricted',
                observed=float(observed[j]),null_mean=float(null[:,j].mean()),null_sd=float(null[:,j].std(ddof=1)),
                excess=float(observed[j]-null[:,j].mean()),p=float((1+(null[:,j]>=observed[j]).sum())/(B+1)),
                endpoint_wallets=len(endpoints),strata=len(offsets)-1,
                shuffleable_wallet_fraction=float(np.sum(np.diff(offsets)[np.diff(offsets)>1])/len(endpoints))))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--permutations',type=int,default=9999);p.add_argument('--sample',type=int,default=50000)
    p.add_argument('--months',nargs='+',default=[f'2022{m:02d}' for m in range(1,13)])
    args=p.parse_args()
    if args.permutations<9999:raise ValueError('216-test family requires 9999 permutations in this protocol')
    OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True);set_num_threads(3)
    raw=pd.read_csv(DATA/'wallet_count_activity_features.csv',dtype={'wallet':str}); wallets=raw.wallet.str.lower().str.removeprefix('0x')
    if not wallets.is_unique:raise ValueError('duplicate wallets')
    total,rule,cuts=baseline_labels(raw)
    labels=np.stack([np.load(DATA/f'annual_fits_reproduced/k{k}_seed492_labels.npy') for k in [3,4,5]]+[total,rule])
    names=['annual_k3','annual_k4','annual_k5','transfer_terciles','span_activity_rule']
    pd.DataFrame([dict(partition=name,cluster=c,n=int(np.sum(y==c)),share=float(np.mean(y==c)))
        for name,y in zip(names,labels) for c in np.unique(y)]).to_csv(OUT/'network_partition_sizes.csv',index=False)
    agreement=[]
    from sklearn.metrics import adjusted_rand_score
    for i in [3,4]:agreement.append(dict(partition=names[i],ari_annual_k3=adjusted_rand_score(labels[0],labels[i])))
    pd.DataFrame(agreement).to_csv(OUT/'network_baseline_agreement.csv',index=False)
    manifest=json.loads((BASE/'network_comparison/manifest.json').read_text());coverage=[];rows=[]
    for source in manifest['raw_sources']:
        month=source['month']; output=OUT/f'network_{month}_tests.csv'; covpath=OUT/f'network_{month}_coverage.json'
        if month not in args.months:continue
        identity=dict(permutations=args.permutations,sample=args.sample,script_sha256=sha(__file__),
                      labels_sha256=[sha(DATA/f'annual_fits_reproduced/k{k}_seed492_labels.npy') for k in [3,4,5]])
        checkpoint=OUT/f'network_{month}_checkpoint.json'
        if output.exists() and checkpoint.exists() and json.loads(checkpoint.read_text())==identity:
            rows+=pd.read_csv(output).to_dict('records');coverage.append(json.loads(covpath.read_text()));continue
        path=make_cache(month,wallets,source)
        con=duckdb.connect();con.execute('SET threads=3');con.execute("SET memory_limit='1GB'")
        con.execute("SET temp_directory='"+(CACHE/'duckdb_tmp').as_posix()+"'")
        con.read_parquet(str(path)).create_view('edges')
        con.execute('CREATE TEMP TABLE nonself AS SELECT * FROM edges WHERE src<>dst')
        eligible=con.execute('SELECT count(*) FROM edges').fetchall()[0][0]
        nonself=con.execute('SELECT count(*) FROM nonself').fetchall()[0][0]
        # Degree here is number of transfer events, with repeated counterparties.
        inbound=np.zeros(len(wallets),dtype=np.int64);outbound=inbound.copy()
        v=con.execute('SELECT src,count(*) FROM nonself GROUP BY src').fetchnumpy();outbound[v['src']]=v['count_star()']
        v=con.execute('SELECT dst,count(*) FROM nonself GROUP BY dst').fetchnumpy();inbound[v['dst']]=v['count_star()']
        bins=(np.floor(np.log2(inbound+1))*64+np.floor(np.log2(outbound+1))).astype(int)
        top_token,token_rows=con.execute('SELECT token,count(*) n FROM nonself GROUP BY token ORDER BY n DESC,token LIMIT 1').fetchall()[0]
        active=np.flatnonzero(inbound+outbound);order=np.lexsort((active,-(inbound[active]+outbound[active])))
        hubs=active[order[:max(1,int(np.ceil(.01*len(active))))]]
        con.register('hubs',pd.DataFrame({'idx':hubs}))
        variants=[('nonself_events','SELECT src,dst FROM nonself',list(range(5))),
            ('all_events','SELECT src,dst FROM edges',[0]),
            ('unique_pairs','SELECT DISTINCT src,dst FROM nonself',[0]),
            ('without_top_token',"SELECT src,dst FROM nonself WHERE token<>'"+top_token.replace("'","''")+"'",[0]),
            ('without_top_1pct_hubs','SELECT src,dst FROM nonself WHERE src NOT IN (SELECT idx FROM hubs) AND dst NOT IN (SELECT idx FROM hubs)',[0])]
        cov=dict(month=month,eligible_events=eligible,nonself_events=nonself,self_events=eligible-nonself,
                 top_token=top_token,top_token_events=token_rows,active_endpoint_wallets=len(active),excluded_hubs=len(hubs),variants={})
        monthly=[]
        for v,(name,query,ids) in enumerate(variants):
            con.execute('CREATE OR REPLACE TEMP TABLE variant AS '+query)
            count=con.execute('SELECT count(*) FROM variant').fetchall()[0][0];cov['variants'][name]=count
            sample=con.execute(f'SELECT * FROM (SELECT * FROM variant ORDER BY src,dst) USING SAMPLE reservoir({args.sample} ROWS) REPEATABLE(492)').fetchdf()
            src=sample.src.to_numpy(dtype=np.int32);dst=sample.dst.to_numpy(dtype=np.int32)
            np.savez_compressed(CACHE/f'{month}_{name}_sample.npz',src=src,dst=dst)
            rr=evaluate(labels[ids],src,dst,bins,args.permutations,int(month)*10+v)
            for r in rr:
                r['partition']=names[ids[r.pop('label_index')]];r.update(month=month,variant=name,sampled_edges=len(src),eligible_edges=count)
            monthly+=rr
            print(f'network {month} {name}: tests complete',flush=True)
        con.close();pd.DataFrame(monthly).to_csv(output,index=False);covpath.write_text(json.dumps(cov,indent=2))
        checkpoint.write_text(json.dumps(identity,indent=2));rows+=monthly;coverage.append(cov)
    # All workers use disjoint months. Only a complete, protocol-matching family
    # receives the global correction and a completion manifest.
    rows=[]
    for source in manifest['raw_sources']:
        month=source['month'];cp=OUT/f'network_{month}_checkpoint.json';fp=OUT/f'network_{month}_tests.csv'
        if not cp.exists() or not fp.exists() or json.loads(cp.read_text())!=identity:
            print('Assigned months complete; waiting for remaining months before global correction.',flush=True)
            return
        rows+=pd.read_csv(fp).to_dict('records')
    frame=pd.DataFrame(rows)
    if len(frame)!=216:raise ValueError('incomplete network family')
    frame['p_holm_216']=holm(frame.p);frame.to_csv(OUT/'network_all_tests.csv',index=False)
    summary=frame.groupby(['partition','variant','null']).agg(mean_excess=('excess','mean'),min_excess=('excess','min'),max_excess=('excess','max'),
        supported=('p_holm_216',lambda x:int((x<.05).sum())),max_adjusted_p=('p_holm_216','max')).reset_index()
    summary.to_csv(OUT/'network_summary.csv',index=False)
    (OUT/'network_manifest.json').write_text(json.dumps(dict(complete=True,tests=216,permutations=args.permutations,sample=args.sample,
        script_sha256=sha(__file__),source_manifest_sha256=sha(BASE/'network_comparison/manifest.json'),
        wallet_source_sha256=sha(DATA/'wallet_count_activity_features.csv'),
        null='Labels shuffled among sampled endpoint wallets, unrestricted or within full eligible nonself monthly log2(in+1),log2(out+1) event-count bins; fixed graph',
        baselines=dict(transfer_tercile_cutpoints=cuts.tolist(),rule='span<=30 days =>0; otherwise active_days>=24 =>2; otherwise1'),
        limitation='Bins approximate activity control, not exact degree or causal adjustment. Unique pairs are sampled from complete eligible monthly pair set. Hub/token sensitivity changes populations. Baseline group shares are not matched.',
        coverage=[json.loads((OUT/f'network_{s["month"]}_coverage.json').read_text()) for s in manifest['raw_sources']],
        sample_sha256={p.name:sha(p) for p in CACHE.glob('*_sample.npz')},
        outputs={'network_all_tests.csv':sha(OUT/'network_all_tests.csv'),'network_summary.csv':sha(OUT/'network_summary.csv')}),indent=2))
    print(summary.to_string(index=False),flush=True)

if __name__=='__main__':main()
