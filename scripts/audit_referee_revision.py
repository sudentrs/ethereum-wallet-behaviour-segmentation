"""Independent receipt, arithmetic and source audit; never compile LaTeX."""
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from scripts.run_referee_robustness import ROOT,BASE,OUT,DATA,sha,holm

def check_tex(path):
    tex=path.read_text(encoding='utf-8')
    refs=set(re.findall(r'\\ref\{([^}]+)\}',tex));labels=re.findall(r'\\label\{([^}]+)\}',tex)
    assert refs<=set(labels),(path.name,refs-set(labels))
    assert len(labels)==len(set(labels)),path.name
    for asset in re.findall(r'\\(?:input|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}',tex):assert (path.parent/asset).exists(),asset
    assert '@@' not in tex and '??' not in tex
    # Check delimiters without relying on a TeX engine; escaped braces are literals.
    clean=re.sub(r'(?m)(?<!\\)%.*$','',tex)
    clean=re.sub(r'\\[{}]','',clean);depth=0
    for char in clean:
        if char=='{':depth+=1
        elif char=='}':depth-=1
        assert depth>=0,(path.name,'unbalanced closing brace')
    assert depth==0,(path.name,depth)
    starts=re.findall(r'\\begin\{([^}]+)\}',clean);ends=re.findall(r'\\end\{([^}]+)\}',clean)
    assert sorted(starts)==sorted(ends),(path.name,'environments')
    return dict(words=len(re.sub(r'\\[a-zA-Z]+',' ',tex).split()),tables=starts.count('table')+starts.count('table*'),
                figures=starts.count('figure')+starts.count('figure*'),labels=len(labels),sha256=sha(path))

def main():
    receipt=json.loads((OUT/'revision_completion.json').read_text());assert receipt['complete']
    delivery=json.loads((OUT/'current_manuscript_delivery.json').read_text()) if (OUT/'current_manuscript_delivery.json').exists() else receipt
    assert sha(ROOT/'overleaf/main.tex')==delivery['manuscript_sha256']
    if 'methodology_figure' in delivery:
        assert sha(ROOT/delivery['methodology_figure'])==delivery['methodology_sha256']
    assert sha(ROOT/'overleaf/supplementary.tex')==receipt['supplementary_sha256']
    assert not receipt['latex_compiled'] and not receipt['page_count_verified']
    for name,h in receipt['inputs'].items():assert sha(OUT/name)==h,name
    for name,h in receipt['validated_cache_inputs'].items():assert sha(ROOT/name)==h,name
    for name,h in receipt['source_code_sha256'].items():assert sha(ROOT/name)==h,name
    for stage in ['annual','population','participation','spectral','network','candidate']:
        m=json.loads((OUT/f'{stage}_manifest.json').read_text());assert m['complete']
        for name,h in m['outputs'].items():assert sha(OUT/name)==h,(stage,name)
        for name,h in m.get('inputs',{}).items():assert sha(ROOT/name)==h,(stage,name)
    a=pd.read_csv(OUT/'annual_resampling.csv');b=pd.read_csv(OUT/'population_resampling.csv');alg=pd.read_csv(OUT/'annual_algorithms.csv')
    candidate=json.loads((OUT/'candidate_manifest.json').read_text())
    threshold=pd.read_csv(OUT/'candidate_threshold_comparison.csv').set_index('threshold')
    build=pd.read_csv(ROOT/'data/processed/wallet_kmeans6_expanded_daily_features_build_summary.csv').iloc[0]
    assert candidate['daily_rows']==build.daily_rows_read==83519492
    assert candidate['candidate_addresses']==build.cluster_wallets==2738243
    assert candidate['candidate_daily_rows']==build.daily_rows_matching_cluster_wallets
    assert candidate['invalid_count_rows']==0 and candidate['exact_threshold_10_set_match']
    assert threshold.loc[10,'candidate_only']==threshold.loc[10,'threshold_only']==0
    assert threshold.loc[10,'threshold_addresses']==2738243
    assert len(a)==150 and len(b)==100 and len(alg)==36
    assert set(a.k)==set(b.k)==set(range(2,7))
    assert not a.duplicated(['k','replicate']).any() and not b.duplicated(['k','replicate']).any()
    assert a.groupby('k').size().eq(30).all() and b.groupby('k').size().eq(20).all()
    assert alg.converged.all() and not alg.duplicated(['k','seed','variant']).any()
    samples=np.load(OUT/'annual_samples.npz');assert len(np.intersect1d(samples['evaluation'],samples['reference_fit']))==0
    net=pd.read_csv(OUT/'network_all_tests.csv');n=pd.read_csv(OUT/'network_extension_with_global_correction.csv')
    old=pd.read_csv(BASE/'network_comparison/network_comparison.csv')
    assert len(net)==len(n)==216 and not net.duplicated(['month','partition','variant','null']).any()
    assert set(net.month)==set(range(202201,202213));assert net.groupby('month').size().eq(18).all()
    np.testing.assert_allclose(net.excess,net.observed-net.null_mean)
    np.testing.assert_allclose(net.p_holm_216,holm(net.p))
    np.testing.assert_allclose(n.p_holm_300,holm(np.r_[old.p_raw,net.p])[84:])
    assert net.p.between(1/10000,1).all() and net.sampled_edges.between(1,50000).all()
    for _,g in net[net.variant.eq('nonself_events')].groupby('month'):
        assert g.sampled_edges.nunique()==g.eligible_edges.nunique()==1
    manifest=json.loads((OUT/'network_manifest.json').read_text())
    original=old[(old.k==3)&(old.label_seed==492)].set_index('month')
    for c in manifest['coverage']:
        assert c['eligible_events']==original.loc[int(c['month']),'eligible_rows']
        assert c['nonself_events']+c['self_events']==c['eligible_events']
        assert c['variants']['unique_pairs']<=c['nonself_events']
    spectral=pd.read_csv(OUT/'spectral_block_tests.csv');assert len(spectral)==9
    assert not spectral.duplicated(['block_days','metric']).any() and spectral.n.eq(2000).all()
    np.testing.assert_allclose(spectral.p_holm_9,holm(spectral.p))
    np.testing.assert_allclose(spectral.excess,spectral.observed-spectral.null_mean)
    scores=pd.read_csv(OUT/'participation_prediction_scores.csv');assert set(scores.month)=={7,8,9,10,11}
    assert not scores.duplicated(['month','group','model']).any()
    for _,g in scores.groupby(['month','group']):assert g.n.nunique()==g.prevalence.nunique()==1
    probs=pd.read_csv(OUT/'participation_transition_probabilities.csv',index_col=0)
    counts=pd.read_csv(OUT/'participation_transition_counts.csv',index_col=0)
    np.testing.assert_allclose(probs.sum(1),1)
    np.testing.assert_allclose(probs,counts.to_numpy()/counts.sum(1).to_numpy()[:,None])
    assert counts.to_numpy().sum()==5*2508997
    ci=pd.read_csv(OUT/'participation_prediction_intervals.csv');assert len(ci)==6
    assert ci.lower.le(ci.upper).all() and ci.wallet_bootstraps.eq(200).all()
    pred=scores[scores.group.eq('all')]
    for _,r in ci.iterrows():
        left,right=r.contrast.split(' minus ')
        one=pred[pred.model.eq(left)].set_index('month');two=pred[pred.model.eq(right)].set_index('month')
        expected=np.average(one[r.metric]-two[r.metric],weights=one.n)
        np.testing.assert_allclose(r.difference,expected,atol=1e-12)
    tex={name:check_tex(ROOT/'overleaf'/name) for name in ['main.tex','supplementary.tex']}
    check_tex(ROOT/'overleaf/figures_current/framework_pipeline.tex')
    main=(ROOT/'overleaf/main.tex').read_text();assert 'K=5' not in main and "diagram's K5" not in main
    result=dict(checks_passed=True,source_checks=tex,annual_subsample_fits=150,annual_population_refits=100,
        algorithm_comparisons=36,new_network_tests=216,combined_network_family=300,timing_null_tests=9,
        predictive_models=int(scores.model.nunique()),latex_compiled=False,page_count_verified=False,
        limitation='Arithmetic, provenance and static LaTeX checks only; no external peer review, raw-population reconstruction or visual page-layout certification.')
    (OUT/'revision_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
