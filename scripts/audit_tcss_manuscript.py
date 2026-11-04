"""Independently reconcile manuscript inputs, test families and LaTeX assets."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.apply_network_holm_correction import holm
from scripts.build_extended_manuscript import validate_inputs
from scripts.finalize_year_end_validation import validate_network

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results_v3/year_end_2022_count_cohort'


def main():
    tex = (ROOT/'overleaf/main.tex').read_text(encoding='utf-8')
    frozen = json.loads((ROOT/'overleaf/manuscript_inputs.json').read_text())
    validate_inputs(ROOT, frozen['input_sha256'])
    status = json.loads((ROOT/'results_v3/year_end_2022_full_cohort/status.json').read_text())
    assert status['complete'] and status['remaining'] == 0
    assert status['included'] + status['excluded'] == status['population'] == 2738243
    assert status['included'] == 2508997
    net = pd.read_csv(BASE/'network_comparison/network_comparison.csv')
    nm = json.loads((BASE/'network_comparison/manifest.json').read_text())
    validate_network(net, nm)
    assert nm['permutations'] == 9999 and net.sample_edges.eq(200000).all()
    np.testing.assert_allclose(net.excess, net.observed-net.null_mean)
    np.testing.assert_allclose(net.standardized_effect, net.excess/net.null_std)
    ns = pd.read_csv(BASE/'network_comparison/comparison_summary.csv').set_index(['k','label_seed'])
    for identity, g in net.groupby(['k','label_seed']):
        r = ns.loc[identity]
        assert len(g) == r.months == 12
        assert (g.p_holm_84 < .05).sum() == r.significant_months
        np.testing.assert_allclose([r.mean_excess,r.min_excess,r.max_excess],
                                   [g.excess.mean(),g.excess.min(),g.excess.max()])
    counts = net[net.k.eq(3)&net.label_seed.eq(492)]
    assert counts.raw_rows.sum() == 245911059 and counts.eligible_rows.sum() == 38733517
    ret = pd.read_csv(BASE/'monthly_k2_k6/heldout_two_step_returns.csv')
    pair = pd.read_csv(BASE/'monthly_k2_k6/heldout_persistence.csv')
    assert len(ret) == 20 and len(pair) == 25
    assert not ret.duplicated(['k','month_start']).any()
    np.testing.assert_allclose(ret.p_holm_all_tests, holm(ret.p.to_numpy()))
    np.testing.assert_allclose(pair.kappa, (pair.observed-pair.chance)/(1-pair.chance))
    assert ret[ret.k.eq(2)].p.eq(1).all()
    ms = pd.read_csv(BASE/'monthly_k2_k6/comparison_summary.csv').set_index('k')
    for k,g in pair.groupby('k'):
        r=ms.loc[k]
        for source,column in [('observed','persistence'),('chance','chance'),('kappa','kappa')]:
            np.testing.assert_allclose([r[column+'_min'],r[column+'_max']], [g[source].min(),g[source].max()])
    fit = pd.read_csv(BASE/'annual/annual_fit_runs.csv')
    stable = pd.read_csv(BASE/'annual/annual_seed_stability.csv')
    assert len(fit)==15 and not fit.duplicated(['k','seed']).any() and len(stable)==15
    profiles = pd.read_csv(BASE/'annual/profiles_k3/annual_exact_raw_profiles_seed492_k3.csv')
    assert profiles.groupby('cluster').n.first().sum()==2508997
    assets = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',tex)
    assert len(assets)==len(set(assets))
    assert 'figures_current/ethereum_wallet_behaviour_methodology.png' in assets
    assert all((ROOT/'overleaf'/asset).is_file() for asset in assets)
    signal_manifest = json.loads((BASE/'signals/manifest.json').read_text())
    assert signal_manifest['complete'] and signal_manifest['cohort_size'] == 2508997
    assert signal_manifest['positive_power_wallets'] + signal_manifest['zero_power_excluded'] == 2508997
    assert signal_manifest['annual_total_reconciliation'] == 'exact for every cohort address'
    for name, expected_hash in signal_manifest['outputs'].items():
        assert hashlib.sha256((BASE/'signals'/name).read_bytes()).hexdigest() == expected_hash
    current_source = ROOT/'data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv'
    assert hashlib.sha256(current_source.read_bytes()).hexdigest() == signal_manifest['sources']['wallet_source_sha256']
    mm = json.loads((BASE/'monthly_k2_k6/manifest.json').read_text())
    assert mm['cohort_sha256'] == signal_manifest['sources']['cohort_sha256']
    for source in mm['source']:
        assert source['sha256'] == signal_manifest['sources']['daily'][str(int(source['month'][-2:]))]
    sf = pd.read_csv(BASE/'signals/signal_model_resolution.csv')
    ss = pd.read_csv(BASE/'signals/signal_seed_stability.csv')
    sc = pd.read_csv(BASE/'signals/cross_representation_agreement.csv')
    st = pd.read_csv(BASE/'signals/timing_surrogate_tests.csv')
    assert len(sf) == len(ss) == 30 and len(sc) == 75 and len(st) == 3
    assert not sf.duplicated(['representation','k','seed']).any()
    assert sf.assigned.eq(signal_manifest['positive_power_wallets']).all()
    np.testing.assert_allclose(st.p_holm_3, holm(st.p.to_numpy()))
    np.testing.assert_allclose(st.excess, st.observed-st.null_mean)
    for key, g in sf.groupby(['representation','k']):
        assert set(g.seed) == {492,493,494}
    assert set(sc.n) == {signal_manifest['positive_power_wallets']}
    assert not sc.duplicated(['left','right']).any()
    hashes={a:hashlib.sha256((ROOT/'overleaf'/a).read_bytes()).hexdigest() for a in assets}
    cites=list(dict.fromkeys(k for group in re.findall(r'\\cite\{([^}]+)\}',tex) for k in group.split(',')))
    assert cites==re.findall(r'\\bibitem\{([^}]+)\}',tex)
    assert set(re.findall(r'\\ref\{([^}]+)\}',tex)) <= set(re.findall(r'\\label\{([^}]+)\}',tex))
    abstract=tex.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
    assert 100<=len(abstract.split())<=250 and r'\documentclass[journal,letterpaper]' in tex
    assert '@@' not in tex
    result={'checks_passed':True,'abstract_words':len(abstract.split()),'network_tests':len(net),
            'monthly_return_tests':len(ret),'monthly_persistence_pairs':len(pair),
            'annual_fits':len(fit),'signal_fits':len(sf),'cross_representation_comparisons':len(sc),
            'signal_timing_tests':len(st),'cohort':status['included'],'figure_sha256':hashes,
            'manuscript_sha256':hashlib.sha256((ROOT/'overleaf/main.tex').read_bytes()).hexdigest(),
            'limitations':'Summary and provenance reconciliation; not independent re-extraction of all raw measurements or external semantic validation.'}
    (BASE/'tcss_manuscript_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='figure_sha256'},indent=2))


if __name__=='__main__':main()
