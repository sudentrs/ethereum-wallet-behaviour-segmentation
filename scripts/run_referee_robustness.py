"""Corrected-cohort resampling, algorithm, participation and signal controls.

Exploratory additions: no claim of preregistration or independent ground truth.
Run stages independently; outputs never overwrite the archived primary fits.
"""
from pathlib import Path
import argparse
import json
import hashlib
import calendar
import platform

import numpy as np
import pandas as pd
import joblib
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import MiniBatchKMeans, KMeans
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, roc_auc_score, brier_score_loss, log_loss
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results_v3/year_end_2022_count_cohort'
OUT=BASE/'referee_extension'
DATA=ROOT/'data/interim/year_end_2022_count_cohort'
MONTHLY=ROOT/'data/interim/year_end_2022_monthly_k3_validated_ordered'
SIGNAL=ROOT/'data/interim/year_end_2022_signals'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()

def holm(p):
    p=np.asarray(p); order=np.argsort(p); q=np.empty(len(p))
    q[order]=np.minimum(1,np.maximum.accumulate(p[order]*np.arange(len(p),0,-1)))
    return q

def matched_jaccard(a,b,k):
    t=np.bincount(a*k+b,minlength=k*k).reshape(k,k)
    r,c=linear_sum_assignment(-t)
    return {int(i):float(t[i,j]/(t[i].sum()+t[:,j].sum()-t[i,j])) for i,j in zip(r,c)}

def block_shuffle(x,block,rng):
    """Independently reorder circular-origin blocks, preserving every daily value."""
    if block==1:return np.take_along_axis(x,np.argsort(rng.random(x.shape),axis=1),axis=1)
    days=x.shape[1];offset=rng.integers(days,size=(len(x),1))
    shifted=np.take_along_axis(x,(np.arange(days)[None,:]-offset)%days,axis=1)
    # A shared key within each block and stable sorting retain within-block order,
    # including the short final block. Independent keys order blocks per wallet.
    keys=rng.random((len(x),int(np.ceil(days/block))))
    order=np.argsort(keys[:,np.arange(days)//block],axis=1,kind='stable')
    return np.take_along_axis(shifted,order,axis=1)

def save_manifest(stage,settings,inputs):
    files={p.name:sha(p) for p in OUT.glob(stage+'*') if p.is_file() and not p.name.endswith('manifest.json')
           and p.name!='participation_pooled_scores.csv'}
    d=dict(complete=True,stage=stage,settings=settings,inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},outputs=files,
           script_sha256=sha(__file__),python=platform.python_version(),numpy=np.__version__,sklearn=__import__('sklearn').__version__)
    (OUT/f'{stage}_manifest.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')

def annual(replicates=30):
    path=DATA/'wallet_count_activity_scaled.npy'; x=np.load(path,mmap_mode='r'); n=len(x)
    rng=np.random.default_rng(70492); order=rng.permutation(n)
    evaluation=order[:50000]; pool=order[50000:]; fit=pool[:100000]
    np.savez_compressed(OUT/'annual_samples.npz',evaluation=evaluation,reference_fit=fit)
    ref={k:np.load(DATA/f'annual_fits_reproduced/k{k}_seed492_labels.npy')[evaluation] for k in range(2,7)}
    rows=[]; jac=[]; sample_refs={}
    for k in range(2,7):
        m=MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=8192,max_iter=200,random_state=492).fit(x[fit])
        sample_refs[k]=m.predict(x[evaluation])
        for r in range(replicates):
            ix=np.random.default_rng(80492+r).choice(pool,100000,replace=False)
            # Fixed optimizer seed isolates training-subset perturbation conditional on scaling.
            m=MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=8192,max_iter=200,random_state=492).fit(x[ix])
            y=m.predict(x[evaluation]); j=matched_jaccard(ref[k],y,k)
            rows.append(dict(k=k,replicate=r,ari_annual=adjusted_rand_score(ref[k],y),
                             ari_sample_reference=adjusted_rand_score(sample_refs[k],y),min_jaccard=min(j.values())))
            jac.extend(dict(k=k,replicate=r,reference_cluster=c,jaccard=v) for c,v in j.items())
        pd.DataFrame(rows).to_csv(OUT/'annual_resampling.csv',index=False)
        pd.DataFrame(jac).to_csv(OUT/'annual_cluster_jaccard.csv',index=False)
        print(f'annual resampling K{k}: {replicates} fits',flush=True)
    groups=[[0,3,4,5,6],[1,2,14,15],[7,8,9,10,11,12,13]]
    weights=np.ones(16)
    for g in groups:weights[g]=1/np.sqrt(len(g))
    variants=[]
    for k in [3,4,5]:
        for seed in [492,493,494]:
            models=[('minibatch',MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=8192,max_iter=200,random_state=seed),False),
                    ('equal_family_weight',MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=8192,max_iter=200,random_state=seed),True),
                    ('batch_kmeans',KMeans(n_clusters=k,n_init=10,max_iter=300,random_state=seed),False),
                    ('diagonal_gmm',GaussianMixture(n_components=k,covariance_type='diag',n_init=3,max_iter=300,random_state=seed),False)]
            for name,m,weighted in models:
                w=weights if weighted else np.ones(16)
                m.fit(x[fit]*w); y=m.predict(x[evaluation]*w)
                variants.append(dict(k=k,seed=seed,variant=name,ari_annual=adjusted_rand_score(ref[k],y),
                    ari_sample_reference=adjusted_rand_score(sample_refs[k],y),nmi_annual=normalized_mutual_info_score(ref[k],y),
                    converged=bool(getattr(m,'converged_',True))))
            print(f'annual algorithms K{k} seed{seed}',flush=True)
    pd.DataFrame(variants).to_csv(OUT/'annual_algorithms.csv',index=False)
    save_manifest('annual',dict(replicates=replicates,fit_size=100000,evaluation_size=50000,
        resampling='independent 100k subsets excluding fixed evaluation; optimizer seed fixed; annual full-cohort scaler retained',
        limitation='conditional on one full-cohort representation; reference annual labels saw evaluation features; diagnostic not prediction',
        groups=groups),[path,DATA/'annual_fits_reproduced/k3_seed492_labels.npy'])

def participation():
    cohort=pd.read_csv(ROOT/'results_v3/year_end_2022_full_cohort/cohort_members.csv.gz',dtype=str).wallet
    index=pd.Index(cohort.str.lower().str.removeprefix('0x')); n=len(index)
    if not index.is_unique:raise ValueError('duplicate cohort')
    with np.load(MONTHLY/'monthly_states.npz') as z: states={k:z[f'k{k}'] for k in range(2,7)}
    if states[3].shape!=(n,12):raise ValueError('state/cohort alignment')
    # Producer assigns against cohort CSV order; parquet order need not agree.
    activity=states[3]>=0
    pairs=[]; matrix=np.zeros((4,4),dtype=np.int64); state_rows=[]
    for j in range(6,11):
        a=states[3][:,j]; b=states[3][:,j+1]
        aa=np.where(a<0,3,a); bb=np.where(b<0,3,b)
        matrix+=np.bincount(aa*4+bb,minlength=16).reshape(4,4)
        seen_before=activity[:,:j].any(1)
        for name,mask in [('all_currently_inactive',a<0),('previously_seen_inactive',(a<0)&seen_before),
                          ('not_yet_seen_in_2022',(a<0)&~seen_before),('currently_active',a>=0)]:
            pairs.append(dict(month_from=j+1,group=name,n=int(mask.sum()),next_active=int(np.sum(mask&(b>=0))),
                              next_activity_rate=float(np.mean(b[mask]>=0))))
        for s in range(3):
            mask=a==s
            state_rows.append(dict(month_from=j+1,state=s,n=int(mask.sum()),inactivity_rate=float(np.mean(b[mask]<0)),
                                   same_active_state_rate=float(np.mean(b[mask]==s))))
    pd.DataFrame(pairs).to_csv(OUT/'participation_inactivity.csv',index=False)
    pd.DataFrame(state_rows).to_csv(OUT/'participation_state_exit.csv',index=False)
    pd.DataFrame(matrix,index=['0','1','2','inactive'],columns=['0','1','2','inactive']).to_csv(OUT/'participation_transition_counts.csv')
    pd.DataFrame(matrix/matrix.sum(1,keepdims=True),index=['0','1','2','inactive'],columns=['0','1','2','inactive']).to_csv(OUT/'participation_transition_probabilities.csv')
    # Relearn monthly state vocabulary on Jan-Mar only; supervised Jan-May pairs
    # and Jul-Nov evaluation never influence the learned scaler/centroids.
    samples=[]; frames=[]
    cols=['tx_per_calendar_day','active_day_fraction','tx_per_active_day','daily_count_cv','peak_count_share','span_fraction']
    for j in range(12):
        f=pd.read_csv(MONTHLY/f'monthly_features_2022{j+1:02d}.csv.gz',dtype={'wallet':str})
        idx=index.get_indexer(f.wallet)
        if (idx<0).any() or not np.array_equal(np.sort(idx),np.flatnonzero(activity[:,j])):raise ValueError('active state alignment')
        frames.append((f,idx))
        if j<3:samples.append(f.sample(min(20000,len(f)),random_state=91492+j))
    def transform(f):
        a=f[cols].to_numpy(float);a[:,[0,2,3]]=np.log1p(a[:,[0,2,3]]);return a
    scaler=RobustScaler().fit(transform(pd.concat(samples))); trainx=scaler.transform(transform(pd.concat(samples)))
    models={k:MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=4096,max_iter=100,random_state=492).fit(trainx) for k in range(2,7)}
    joblib.dump(dict(scaler=scaler,models=models),OUT/'participation_early_models.joblib')
    train=[]; tests=[]
    for j,(f,idx) in enumerate(frames):
        if j==11 or j==5:continue
        if j<5:
            sel=np.random.default_rng(92492+j).choice(len(f),min(50000,len(f)),replace=False); f=f.iloc[sel];idx=idx[sel]
        z=scaler.transform(transform(f)); d=f[cols].copy()
        for k,m in models.items():d[f'k{k}']=m.predict(z)
        d['target']=activity[idx,j+1].astype(int);d['wallet_idx']=idx;d['month']=j+1
        (train if j<5 else tests).append(d)
    training=pd.concat(train,ignore_index=True); y=training.target.to_numpy(); base=y.mean()
    # Same rows across models; state vocabulary learned before all test outcomes.
    def feats(d,kind):
        a=transform(d)
        if kind=='activity':return a[:,:2]
        if kind=='all_count':return a
        return np.column_stack([a,np.eye(3)[d.k3.to_numpy()]])
    classifiers={}
    for kind in ['activity','all_count','all_count_plus_k3']:
        sc=StandardScaler().fit(feats(training,kind));m=LogisticRegression(max_iter=1000,random_state=492).fit(sc.transform(feats(training,kind)),y)
        classifiers[kind]=(sc,m)
    nonlinear=HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,l2_regularization=1,random_state=492).fit(feats(training,'all_count'),y)
    rates={k:training.groupby(f'k{k}').target.agg(['sum','count']) for k in range(2,7)}
    score_rows=[]; ci_rows=[]
    # Fixed wallet-level Poisson bootstrap shared over months for paired score differences.
    bootstrap_rng=np.random.default_rng(93492); mult=np.empty((200,n),dtype=np.uint8)
    for r in range(200):mult[r]=bootstrap_rng.poisson(1,size=n).astype(np.uint8)
    contrasts=[('all_count_plus_k3','all_count'),('k3_state_only','activity'),('k3_state_only','nonlinear_count')]
    loss_delta=np.zeros((200,2*len(contrasts))); weight_total=np.zeros(200)
    point_delta=np.zeros(2*len(contrasts)); total=0
    train_ids=np.unique(training.wallet_idx)
    for d in tests:
        yy=d.target.to_numpy(); predictions={'constant':np.full(len(d),base)}
        for kind,(sc,m) in classifiers.items():predictions[kind]=m.predict_proba(sc.transform(feats(d,kind)))[:,1]
        predictions['nonlinear_count']=nonlinear.predict_proba(feats(d,'all_count'))[:,1]
        for k,r in rates.items():predictions[f'k{k}_state_only']=d[f'k{k}'].map((r['sum']+1)/(r['count']+2)).to_numpy()
        unseen=~np.isin(d.wallet_idx,train_ids)
        for group,mask in [('all',np.ones(len(d),dtype=bool)),('not_in_supervised_training',unseen)]:
            for name,q in predictions.items():
                if not mask.any():continue
                score_rows.append(dict(month=int(d.month.iloc[0]),group=group,model=name,n=int(mask.sum()),
                    prevalence=float(yy[mask].mean()),brier=brier_score_loss(yy[mask],q[mask]),
                    log_loss=log_loss(yy[mask],q[mask],labels=[0,1]),auc=roc_auc_score(yy[mask],q[mask])))
        differences=[]
        for left,right in contrasts:
            a=np.clip(predictions[right],1e-12,1-1e-12);b=np.clip(predictions[left],1e-12,1-1e-12)
            differences.extend([(b-yy)**2-(a-yy)**2,
                -(yy*np.log(b)+(1-yy)*np.log1p(-b))+(yy*np.log(a)+(1-yy)*np.log1p(-a))])
        delta=np.column_stack(differences)
        point_delta+=delta.sum(0);total+=len(d)
        for start in range(0,200,10):
            w=mult[start:start+10,d.wallet_idx.to_numpy()].astype(float)
            loss_delta[start:start+10]+=w@delta;weight_total[start:start+10]+=w.sum(1)
        print(f'participation prediction month {d.month.iloc[0]}',flush=True)
    for j in range(2*len(contrasts)):
        name=['brier','log_loss'][j%2];left,right=contrasts[j//2];dist=loss_delta[:,j]/weight_total
        ci_rows.append(dict(metric=name,contrast=left+' minus '+right,difference=point_delta[j]/total,
                            lower=float(np.quantile(dist,.025)),upper=float(np.quantile(dist,.975)),wallet_bootstraps=200))
    pd.DataFrame(score_rows).to_csv(OUT/'participation_prediction_scores.csv',index=False)
    pd.DataFrame(ci_rows).to_csv(OUT/'participation_prediction_intervals.csv',index=False)
    save_manifest('participation',dict(cohort_order='cohort_members.csv.gz',state_fit_months='Jan-Mar',
        supervised_fit_pairs='Jan-Feb through May-Jun',evaluation_pairs='Jul-Aug through Nov-Dec',
        training_rows=len(training),uncertainty='200 paired wallet-level Poisson bootstrap replicates; conditional on fitted models',
        limitation='Retrospective year-end cohort, same year, observed ERC20 activity only; unseen subgroup excludes supervised sample, not necessarily state-fit sample'),
        [MONTHLY/'monthly_states.npz',ROOT/'results_v3/year_end_2022_full_cohort/cohort_members.csv.gz'])

def spectral():
    def metrics(x):
        z=np.log1p(x);z-=z.mean(1,keepdims=True)
        power=np.abs(np.fft.rfft(z,axis=1)[:,1:])**2;total=power.sum(1)
        q=np.divide(power,total[:,None],out=np.zeros_like(power),where=total[:,None]>0)
        f=np.fft.rfftfreq(365)[1:]
        entropy=-(q*np.log2(np.maximum(q,np.finfo(float).tiny))).sum(1)
        return np.column_stack([q[:,f<1/60].sum(1),q.max(1),-entropy]),total>0
    counts=np.load(SIGNAL/'daily_counts.npy',mmap_mode='r')
    ids=np.load(SIGNAL/'timing_sample_indices.npy'); x=np.asarray(counts[ids],dtype=float)
    obs,valid=metrics(x);x=x[valid];obs=obs[valid].mean(0)
    rows=[]; allnull={}
    for block in [1,7,30]:
        rng=np.random.default_rng(94492+block); null=np.empty((999,3))
        for b in range(999):
            z=block_shuffle(x,block,rng)
            vals,_=metrics(z);null[b]=vals.mean(0)
        allnull[f'block{block}']=null
        for j,name in enumerate(['low_frequency_share','peak_power_share','negative_entropy']):
            rows.append(dict(block_days=block,metric=name,n=len(x),observed=obs[j],null_mean=float(null[:,j].mean()),
                excess=float(obs[j]-null[:,j].mean()),p=float((1+(null[:,j]>=obs[j]).sum())/1000)))
        print(f'spectral block {block} complete',flush=True)
    frame=pd.DataFrame(rows);frame['p_holm_9']=holm(frame.p);frame.to_csv(OUT/'spectral_block_tests.csv',index=False)
    np.savez_compressed(OUT/'spectral_null_replicates.npz',**allnull)
    save_manifest('spectral',dict(permutations=999,sample=len(x),block_days=[1,7,30],holm_tests=9,
        limitation='Block shuffles partially retain local ordering; no formal identification of periodic cycles'),
        [SIGNAL/'timing_sample_indices.npy',SIGNAL/'features_complete.json'])

def population(replicates=20):
    x=np.load(DATA/'wallet_count_activity_scaled.npy',mmap_mode='r')
    evaluation=np.load(OUT/'annual_samples.npz')['evaluation'];pool=np.setdiff1d(np.arange(len(x)),evaluation)
    rows=[];jac=[]
    for k in range(2,7):
        ref=np.load(DATA/f'annual_fits_reproduced/k{k}_seed492_labels.npy')[evaluation]
        for r in range(replicates):
            ix=np.random.default_rng(95492+r).choice(pool,int(.8*len(pool)),replace=False)
            m=MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=8192,max_iter=200,random_state=492).fit(x[ix])
            y=m.predict(x[evaluation]);j=matched_jaccard(ref,y,k)
            rows.append(dict(k=k,replicate=r,fit_size=len(ix),evaluation_size=len(evaluation),ari=adjusted_rand_score(ref,y),min_jaccard=min(j.values())))
            jac.extend(dict(k=k,replicate=r,reference_cluster=c,jaccard=v) for c,v in j.items())
        pd.DataFrame(rows).to_csv(OUT/'population_resampling.csv',index=False)
        pd.DataFrame(jac).to_csv(OUT/'population_jaccard.csv',index=False)
        print(f'population 80pct K{k}: {replicates} fits',flush=True)
    save_manifest('population',dict(replicates=replicates,training_fraction_of_nonevaluation=.8,
        optimizer_seed=492,scaling='retained full-cohort scaler',evaluation='fixed 50000 excluded from all refits; annual reference saw these features',
        limitation='descriptive partition robustness conditional on preprocessing, not prediction or independent validation'),
        [DATA/'wallet_count_activity_scaled.npy',OUT/'annual_samples.npz'])

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['annual','participation','spectral','population']);p.add_argument('--replicates',type=int,default=30)
    a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=3):
        if a.stage=='annual':annual(a.replicates)
        elif a.stage=='participation':participation()
        elif a.stage=='population':population(a.replicates)
        else:spectral()

if __name__=='__main__':main()
