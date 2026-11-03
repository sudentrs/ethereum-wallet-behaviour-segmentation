"""Publish compact outputs only after both complete validation runs pass checks."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import platform
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib

from scripts.apply_network_holm_correction import holm

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results_v3/year_end_2022_count_cohort'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_network(table,manifest):
    expected={(202200+m,k,seed) for m in range(1,13)
              for k,seed in [(2,492),(3,492),(4,492),(5,492),(6,492),(3,493),(3,494)]}
    observed=set(table[['month','k','label_seed']].itertuples(index=False,name=None))
    if not manifest.get('complete') or len(table)!=84 or observed!=expected:
        raise ValueError('Network comparison is incomplete or duplicated')
    if not np.isfinite(table[['p_raw','p_holm_84']].to_numpy()).all():
        raise ValueError('Invalid p values')
    np.testing.assert_allclose(table.p_holm_84,holm(table.p_raw.to_numpy()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--monthly-dir',type=Path,required=True)
    args=p.parse_args()
    nm=json.loads((BASE/'network_comparison/manifest.json').read_text())
    mm=json.loads((args.monthly_dir/'manifest.json').read_text())
    network=BASE/'network_comparison/network_comparison.csv'
    table=pd.read_csv(network)
    validate_network(table,nm)
    if len(nm['raw_sources'])!=12:
        raise ValueError('Network comparison is incomplete')
    if digest(network)!=nm['summary_sha256']:
        raise ValueError('Network summary hash mismatch')
    np.testing.assert_allclose(table.p_holm_84,holm(table.p_raw.to_numpy()))
    annual=json.loads((BASE/'annual/annual_artifact_manifest.json').read_text())
    expected={(r['k'],r['seed']):r['labels_sha256'] for r in annual['runs']}
    if nm['wallet_source_sha256']!=annual['wallet_source_sha256']:
        raise ValueError('Network wallet order differs from the fitted model source')
    if any(r['sha256']!=expected[r['k'],r['seed']] for r in nm['labels']):
        raise ValueError('Network labels differ from audited annual labels')
    if len(mm['source'])!=12 or 'training_sampling_order' not in mm:
        raise ValueError('Monthly validation or deterministic sampling is incomplete')
    mm.update(producer_script_sha256=digest(ROOT/'scripts/run_monthly_count_validation.py'),
              frozen_model_sha256=digest(args.monthly_dir/'frozen_monthly_models.joblib'),
              monthly_states_sha256=digest(args.monthly_dir/'monthly_states.npz'))
    frozen=joblib.load(args.monthly_dir/'frozen_monthly_models.joblib')
    mm.update(model_settings={str(k):model.get_params() for k,model in frozen['models'].items()},
              scaler_settings=frozen['scaler'].get_params(),
              log1p_features=['tx_per_calendar_day','tx_per_active_day','daily_count_cv'])
    (args.monthly_dir/'manifest.json').write_text(json.dumps(mm,indent=2)+'\n')
    paired_all=pd.read_csv(args.monthly_dir/'heldout_persistence.csv')
    returned_all=pd.read_csv(args.monthly_dir/'heldout_two_step_returns.csv')
    if set(mm['k_values'])!=set(range(2,7)) or len(paired_all)!=25 or len(returned_all)!=20:
        raise ValueError('K2--K6 monthly analysis is incomplete')
    np.testing.assert_allclose(returned_all.p_holm_all_tests,holm(returned_all.p.to_numpy()))
    all_monthly=BASE/'monthly_k2_k6'
    all_monthly.mkdir(exist_ok=True)
    for name in ['heldout_persistence.csv','heldout_two_step_returns.csv','heldout_entropy.csv',
                 'monthly_coverage.csv','monthly_role_profiles.csv','manifest.json']:
        shutil.copyfile(args.monthly_dir/name,all_monthly/name)
    for k in range(2,7):
        for ext in ['csv','pdf']:
            name=f'k{k}_heldout_transition_matrix.{ext}'
            shutil.copyfile(args.monthly_dir/name,all_monthly/name)
    monthly=BASE/'monthly_k3'
    archive=monthly/'archived_pre_validation'
    archive.mkdir(parents=True,exist_ok=True)
    names=['heldout_persistence.csv','heldout_two_step_returns.csv','heldout_entropy.csv',
           'k3_heldout_transition_matrix.csv','k3_heldout_transition_matrix.pdf',
           'monthly_coverage.csv','monthly_role_profiles.csv','manifest.json']
    for name in names:
        if (monthly/name).exists() and not (archive/name).exists():
            shutil.copyfile(monthly/name,archive/name)
        if name.endswith('.csv'):
            data=pd.read_csv(args.monthly_dir/name)
            if 'k' in data:
                data=data[data.k==3]
            data.to_csv(monthly/name,index=False)
        else:
            shutil.copyfile(args.monthly_dir/name,monthly/name)
    paired=pd.read_csv(monthly/'heldout_persistence.csv')
    returned=pd.read_csv(monthly/'heldout_two_step_returns.csv')
    if len(paired)!=5 or len(returned)!=4:
        raise ValueError('Unexpected monthly test family')
    if not np.allclose(returned.p_holm_all_tests,returned_all.loc[returned_all.k==3,'p_holm_all_tests']):
        raise ValueError('K3 excerpt must retain the global 20-test temporal correction')
    sensitivity=[]
    variants=[('previous_tracked',archive),
              ('validated_unsorted',args.monthly_dir.parent/'year_end_2022_monthly_k3_validated'),
              ('validated_sorted',monthly)]
    for variant,path in variants:
        if not (path/'heldout_persistence.csv').exists():
            continue
        oldp=pd.read_csv(path/'heldout_persistence.csv')
        oldr=pd.read_csv(path/'heldout_two_step_returns.csv')
        corrected='p_holm_all_tests' if 'p_holm_all_tests' in oldr else 'p_holm_all_12_tests'
        sensitivity.append(dict(variant=variant,persistence_min=oldp.observed.min(),
            persistence_max=oldp.observed.max(),kappa_min=oldp.kappa.min(),kappa_max=oldp.kappa.max(),
            return_min=oldr.observed.min(),return_max=oldr.observed.max(),
            maximum_adjusted_return_p=oldr[corrected].max()))
    pd.DataFrame(sensitivity).to_csv(monthly/'training_order_sensitivity.csv',index=False)

    # One common transfer sample per month, with separate null expectations per model.
    fig,axes=plt.subplots(1,2,figsize=(10,3.5))
    for k,g in table[table.label_seed==492].groupby('k'):
        axes[0].plot(np.arange(1,13),100*g.sort_values('month').excess,marker='o',ms=3,label=f'K{k}')
    for seed,g in table[table.k==3].groupby('label_seed'):
        axes[1].plot(np.arange(1,13),100*g.sort_values('month').excess,marker='o',ms=3,label=f'Seed {seed}')
    for ax in axes:
        ax.axhline(0,color='black',lw=.8)
        ax.set(xlabel='2022 month',ylabel='Observed minus null (percentage points)',xticks=range(1,13))
        ax.legend(fontsize=7,frameon=False)
        ax.grid(alpha=.2)
    axes[0].set_title('Annual resolutions: seed 492')
    axes[1].set_title('Annual K3: initialization sensitivity')
    fig.tight_layout()
    for ext in ['pdf','png']:
        fig.savefig(BASE/f'network_comparison/network_comparison_overview.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)

    reference=table[(table.k==3)&(table.label_seed==492)]
    legacy=pd.read_csv(BASE/'network_k3/monthly_network_validation_summary.csv')
    aligned=reference.merge(legacy,on='month',validate='one_to_one')
    exact_counts_match=bool((aligned.raw_rows==aligned.raw_rows_read).all() and
        (aligned.eligible_rows==aligned.rows_with_both_cluster_labels).all() and
        np.allclose(aligned.exact_same_ratio,aligned.exact_same_cluster_ratio))
    if not exact_counts_match:
        raise ValueError('Full-edge K3 counts disagree with the archived reference; investigate before publishing')
    fig,ax=plt.subplots(figsize=(6.5,3.3))
    ax.plot(range(1,13),reference.observed,marker='o',label='Observed')
    ax.plot(range(1,13),reference.null_mean,marker='o',label='Shuffled-label mean')
    ax.set(xlabel='2022 month',ylabel='Same-cluster transfer ratio',xticks=range(1,13))
    ax.legend(frameon=False);fig.tight_layout()
    fig.savefig(ROOT/'overleaf/figures/k3_network_observed_vs_null.png',dpi=220)
    plt.close(fig)
    for name in ['annual_model_resolution.pdf','annual_seed_stability.pdf','k3_count_activity_profiles.pdf']:
        shutil.copyfile(BASE/'figures'/name,ROOT/'overleaf/figures'/name)
    shutil.copyfile(monthly/'k3_heldout_transition_matrix.pdf',ROOT/'overleaf/figures/k3_heldout_transition_matrix.pdf')
    shutil.copyfile(BASE/'network_comparison/network_comparison_overview.pdf',ROOT/'overleaf/figures/network_comparison_overview.pdf')

    summary=table.groupby(['k','label_seed']).agg(months=('month','size'),
        significant_months=('p_holm_84',lambda v:int((v<.05).sum())),
        mean_excess=('excess','mean'),min_excess=('excess','min'),max_excess=('excess','max'),
        min_adjusted_p=('p_holm_84','min'),max_adjusted_p=('p_holm_84','max')).reset_index()
    summary.to_csv(BASE/'network_comparison/comparison_summary.csv',index=False)
    monthly_rows=[]
    for k in range(2,7):
        pair=paired_all[paired_all.k==k]; ret=returned_all[returned_all.k==k]
        monthly_rows.append(dict(k=k,persistence_min=pair.observed.min(),persistence_max=pair.observed.max(),
            chance_min=pair.chance.min(),chance_max=pair.chance.max(),kappa_min=pair.kappa.min(),
            kappa_max=pair.kappa.max(),return_excess_min=(ret.observed-ret.null_mean).min(),
            return_excess_max=(ret.observed-ret.null_mean).max(),
            significant_returns=int((ret.p_holm_all_tests<.05).sum()),
            max_adjusted_return_p=ret.p_holm_all_tests.max()))
    monthly_summary=pd.DataFrame(monthly_rows)
    monthly_summary.to_csv(all_monthly/'comparison_summary.csv',index=False)
    fig,ax=plt.subplots(figsize=(6.5,3.5))
    for k,pair in paired_all.groupby('k'):
        ax.plot(range(1,6),pair.observed.to_numpy()-pair.chance.to_numpy(),marker='o',label=f'K{k}')
    ax.set(xlabel='Held-out adjacent pair (Jul-Aug through Nov-Dec)',ylabel='Persistence above marginal chance',xticks=range(1,6))
    ax.legend(frameon=False,ncol=5);ax.grid(alpha=.2);fig.tight_layout()
    for ext in ['pdf','png']:
        fig.savefig(all_monthly/f'monthly_resolution_comparison.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)
    shutil.copyfile(all_monthly/'monthly_resolution_comparison.pdf',ROOT/'overleaf/figures/monthly_resolution_comparison.pdf')
    replication=json.loads((BASE/'annual/annual_reproduction_audit.json').read_text())
    record=dict(complete=True,cohort_wallets=mm['cohort_size'],annual_exact_matches=replication['exact_label_hash_matches'],
        legacy_k3_exact_counts_match=exact_counts_match,
        annual_runs=15,network_tests=len(table),network_permutations=nm['permutations'],
        network_holm_family=84,monthly_return_holm_family=20,monthly_k_values=list(range(2,7)),
        monthly_sampling_order=mm['training_sampling_order'],
        network_summary_sha256=digest(network),monthly_manifest_sha256=digest(monthly/'manifest.json'),
        holdouts_sha256=digest(BASE/'annual/k3_feature_holdout_sensitivity.csv'))
    import sklearn, duckdb, numba
    record['runtime']=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,
                           scikit_learn=sklearn.__version__,duckdb=duckdb.__version__,numba=numba.__version__)
    record['network_producer_script_matches']=digest(ROOT/'scripts/run_year_end_network_comparison.py')==nm['script_sha256']
    if not record['network_producer_script_matches']:
        raise ValueError('Network producer source changed after run; audit required')
    (BASE/'validation_completion.json').write_text(json.dumps(record,indent=2)+'\n')
    lines=['# Completed year-end validation','',
        'All twelve supplied raw transfer months and all twelve daily CSVs were processed.',
        'Daily validation rejects invalid dates/addresses/counts and duplicate wallet-day records.',
        'Monthly training samples are selected after sorting normalized wallet IDs.',
        '', '## Network comparisons', '', summary.to_markdown(index=False), '',
        'Excesses are proportions; multiply by 100 for percentage points. Significance uses the',
        'single 84-test Holm family, with 9,999 permutations and shared monthly edge samples.',
        'A nonsignificant upper-tail test is not evidence of equivalence or a lower-tail test.',
        '', '## Matched-estimator holdouts', '',
        pd.read_csv(BASE/'annual/k3_feature_holdout_sensitivity.csv').to_markdown(index=False), '',
        '## All monthly resolutions', '',monthly_summary.to_markdown(index=False),'',
        'Twenty monthly return tests across K2--K6 form a separate Holm family.',
        'For K2, the starting state of a first-step switcher is fixed by the middle state.',
        'Shuffling future labels within middle-state groups leaves binary return counts unchanged;',
        'the resulting p=1 is structurally uninformative and must not be read as evidence against temporal structure.',
        '## Deterministic held-out K3 excerpt', '', paired.to_markdown(index=False),'',
        returned.to_markdown(index=False),'',
        '## Reproduction limits', '',
        'Features and scaled matrix match the archived hashes. Thirteen of fifteen annual label arrays',
        'match exactly; K3 seed494 and K6 seed493 are explicitly identified as reproduced fits.',
        'All five seed492 references and K3 seed493 match archived labels.',
        'The validated, deterministically sampled monthly model supersedes the old unsorted training run.',
        'Its numerical persistence rates differ because deterministic ordering changes the seeded training sample.',
        'training_order_sensitivity.csv retains the old and intermediate summaries for transparent comparison;',
        'this is a preprocessing diagnostic, not a prespecified random-seed robustness study.',
        'See annual_reproduction_audit.json, per-source hashes and REPRODUCE_CURRENT_VALIDATION.md.',
        'No new RPC scan, causal claim, token-value aggregation, or permanent EOA claim is made.']
    (ROOT/'docs/VALIDATION_COMPLETION.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(summary.to_string(index=False),flush=True)
    print('Published compact validated outputs and synchronized manuscript figures.',flush=True)


if __name__=='__main__':
    main()
