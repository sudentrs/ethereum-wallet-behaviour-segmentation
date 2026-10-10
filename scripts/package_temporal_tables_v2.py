"""Verify triple counts and package Table III/VII/VIII temporal inputs.

Run after run_temporal_validation_v2.py. Does not finalise Person 2's metrics
or edit a manuscript: no LaTeX source is present in this checkout.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def entropy(counts):
    total = np.sum(counts)
    if not total:
        return np.nan
    p = np.asarray(counts, dtype=float) / total
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out-dir', type=Path, default=ROOT / 'results_v2/temporal_k4_k5_k6')
    args = p.parse_args()
    out = args.out_dir
    summary = pd.read_csv(out / 'temporal_summary.csv')
    triples = pd.read_csv(out / 'two_step_stratified.csv')
    matrix = pd.read_csv(out / 'transition_matrix.csv')
    checks, metrics, profiles = [], [], []
    for k in [4,5,6]:
        old = pd.read_csv(ROOT / f'results/eoa_only_kmeans{k}/temporal_validation/two_step_return_analysis.csv')
        new = triples[triples.k == k].merge(old, left_on=['month_start','month_middle','month_end'],
            right_on=['month_t','month_t1','month_t2'], validate='one_to_one')
        if len(new) != 10:
            raise ValueError('Expected ten consecutive calendar triples')
        for r in new.itertuples():
            match = (r.n_wallets == r.wallets_present_all_three and
                r.n_initial_switchers == r.left_original_state_count and
                r.n_returned == r.returned_to_original_state_count)
            checks.append(dict(k=k,month_start=r.month_start,legacy_triple_counts_match=match))
            if not match:
                raise ValueError(f'Legacy triple counts differ: K{k}, {r.month_start}')
            if r.null_std > 0:
                error = abs(r.null_mean - r.exact_null_expectation)
                if error > 6*r.null_std/np.sqrt(r.permutations):
                    raise ValueError('Monte Carlo null mean inconsistent with analytical expectation')
        counts = matrix[matrix.k==k].pivot(index='from_state',columns='to_state',values='count').to_numpy()
        n = counts.sum()
        hn = entropy(counts.sum(0))
        hc = sum(row.sum()/n*entropy(row) for row in counts)
        s = summary.set_index('k').loc[k]
        for name,value in [('observed_self_transition',s.observed_self_transition),
                           ('chance_self_transition',s.expected_self_transition),
                           ('cohen_kappa',s.cohen_kappa),('next_state_entropy_bits',hn),
                           ('conditional_entropy_bits',hc),('mutual_information_bits',hn-hc),
                           ('normalized_entropy_reduction',(hn-hc)/hn),
                           ('transition_observations',n)]:
            metrics.append(dict(k=k,metric=name,value=value,
                method='pair-size-weighted' if name in ['observed_self_transition','chance_self_transition','cohen_kappa'] else 'pooled transition matrix'))
        for c,row in enumerate(counts):
            profiles.append(dict(k=k,state=c,transition_observations=int(row.sum()),
                self_transition_probability=row[c]/row.sum(),transition_entropy_bits=entropy(row)))
    pd.DataFrame(checks).to_csv(out/'triple_reconstruction_checks.csv',index=False)
    pd.DataFrame(metrics).to_csv(out/'table_vii_metrics.csv',index=False)
    pd.DataFrame(profiles).to_csv(out/'table_vii_state_profiles.csv',index=False)
    legacy=pd.read_csv(ROOT/'results_v2/temporal_k4_k5_k6/legacy_mixed_annual_scaling_stats.csv')
    eoa=pd.read_csv(ROOT/'data/processed/wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled_scaling_stats.csv')
    comparison=legacy.merge(eoa,on='feature',suffixes=('_legacy_mixed','_eoa'),validate='one_to_one')
    comparison['median_difference']=comparison.median_legacy_mixed-comparison.median_eoa
    comparison['iqr_difference']=comparison.iqr_legacy_mixed-comparison.iqr_eoa
    comparison.to_csv(out/'scaler_population_comparison.csv',index=False)
    cols=legacy.feature.tolist()
    annual_raw=pd.read_csv(ROOT/'data/processed/wallet_kmeans6_expanded_daily_features.csv',
        nrows=500,usecols=['wallet']+cols,dtype={'wallet':str}).set_index('wallet')
    annual_scaled=pd.read_csv(ROOT/'data/processed/wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled.csv',
        nrows=500,usecols=['wallet']+cols,dtype={'wallet':str}).set_index('wallet')
    common=annual_raw.index.intersection(annual_scaled.index)
    if not len(common):
        raise ValueError('No common wallets in annual scaler provenance sample')
    sample_checks=[]
    for r in comparison.itertuples():
        values=annual_raw.loc[common,r.feature].replace([np.inf,-np.inf],np.nan).fillna(0.)
        observed=annual_scaled.loc[common,r.feature].to_numpy()
        errors={}
        for name in ['legacy_mixed','eoa']:
            kind=getattr(r,'transform_type_'+name)
            transformed=values if kind=='raw' else np.log1p(values) if kind=='log1p' else np.sign(values)*np.log1p(np.abs(values))
            iqr=getattr(r,'iqr_'+name)
            predicted=(transformed-getattr(r,'median_'+name))/(iqr if iqr else 1.)
            errors[name]=float(np.max(np.abs(predicted-observed)))
            if name=='eoa' and not np.allclose(predicted,observed,rtol=1e-5,atol=1e-5):
                raise ValueError(f'EOA annual scaler provenance check failed: {r.feature}')
        sample_checks.append(dict(feature=r.feature,n_wallets=len(common),
            max_abs_error_eoa_scaler=errors['eoa'],max_abs_error_legacy_mixed_scaler=errors['legacy_mixed']))
    pd.DataFrame(sample_checks).to_csv(out/'annual_scaler_sample_check.csv',index=False)
    audit='''

## Additional scaler provenance finding

The local EOA-only annual scaler does not reproduce legacy monthly state compositions
(K4 January maximum share difference 0.0464, with the same active-wallet count).
The legacy temporal / strengthening code references a mixed-population annual scaler.
That missing scaler was recovered from data/processed/wallet_kmeans6_expanded_daily_features.csv
using the original robust_scale_expanded_features.transform_series function and exact
full-population quartiles. This is not a refit on monthly data.
Only the recovered legacy scaler is accepted for these outputs after reconstruction checks.
The EOA-only feature-space scaler remains untouched. Both scaler populations are compared
in scaler_population_comparison.csv; replacing one silently would change the experiment.

This adds a population-scaling concern to the observation-window concern: the reproduced
monthly assignments use mixed-population scaling with EOA-only median prototypes.
Annual raw/scaled sample values identify the separate EOA scaler: annual_scaler_sample_check.csv
verifies all 33 features on the shared wallets in the first 500 annual raw/scaled rows.
The results are a transparent revalidation of the legacy assignment, not a correction of
these assignment biases. Professor review should consider consistent EOA scaling and
annualisation together before finalising temporal claims. If either changes, rerun all
transition, entropy, and return outputs and revise every affected paper number.

Additional Section IV-F wording: The legacy monthly assignment also uses scaling statistics
estimated on the mixed annual address population with EOA-only prototypes. This population
mismatch may further affect monthly assignments; temporal conclusions remain conditional
on this assignment procedure.
'''
    summary_path=out/'temporal_validation_v2_summary.md'
    summary_path.write_text(summary_path.read_text(encoding='utf-8').split('\n\n## Additional scaler provenance finding')[0]+audit,encoding='utf-8')
    replacements_path=out/'paper_replacement_paragraphs.md'
    replacements_path.write_text(replacements_path.read_text(encoding='utf-8').split('Additional Section IV-F wording:')[0]+audit[audit.index('Additional Section IV-F wording:'):],encoding='utf-8')
    table3 = pd.read_csv(out/'table_iii_temporal_inputs.csv')
    table3['interpretation'] = table3.k.map({
        4:'Conservative taxonomy with strongest monthly network evidence; compare chance-corrected persistence rather than raw agreement; monthly scaling caveats apply.',
        5:'Highest seed stability; richer descriptive taxonomy; weaker network evidence; monthly assignment scaling caveat applies.',
        6:'Fine-grained taxonomy with strong network evidence and lower seed stability; monthly assignment scaling caveat applies.'})
    table3.to_csv(out/'table_iii_temporal_inputs.csv',index=False)
    (out/'README.md').write_text('''# Temporal V2 handoff

Guide Items 8, 10 and 9 are implemented using the limitation path for monthly scaling.
The existing monthly assignment method is retained; final claims require professor review.
Read temporal_validation_v2_summary.md and paper_replacement_paragraphs.md before copying numbers.

Reproduce from the repository root:

```powershell
python scripts/test_temporal_validation_v2.py
python scripts/recover_legacy_temporal_scaler.py
python scripts/run_temporal_validation_v2.py --permutations 99 --out-dir results_v2/temporal_k4_k5_k6_smoke
python scripts/package_temporal_tables_v2.py --out-dir results_v2/temporal_k4_k5_k6_smoke
python scripts/run_temporal_validation_v2.py --permutations 999
python scripts/package_temporal_tables_v2.py
```

Required local inputs: complete 512 daily_wallet_partitions, recovered legacy annual scaling statistics,
K4/K5/K6 median prototypes, annual cluster sizes and legacy compact temporal outputs.
Large state CSVs and K4/K6 wallet-label CSVs are not required: states are reconstructed,
then verified against monthly compositions and every pair and triple count.
The ignored NPZ cache stores aligned wallet rows with -1 for absence, across twelve months
and three resolutions. It never treats inactivity as a behavioural state.

Table III temporal inputs are partial: Person 2 must supply the final internal metrics,
including sampled silhouette mean plus standard deviation, before joint integration.
Table VII uses table_vii_metrics.csv and table_vii_state_profiles.csv.
Table VIII uses table_viii_k5_inputs.csv (all K comparisons are in two_step_stratified.csv).
No manuscript was edited, and no results were sent or pushed automatically.
The legacy mixed-population scaler differs from the EOA-only feature-space scaler.
See scaler_population_comparison.csv and the additional provenance finding in the summary.
Old results remain unchanged. Percentages in CSVs are fractions; multiply by 100 for display.
Pooled counts are wallet-window observations, not unique-wallet counts.
''',encoding='utf-8')
    print('All 30 legacy triple count checks passed; Table III/VII/VIII handoff packaged.')


if __name__ == '__main__':
    main()
