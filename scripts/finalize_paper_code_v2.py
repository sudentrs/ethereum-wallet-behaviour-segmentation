"""Reference-label metrics and paper integration inputs; no reclustering substitutes."""
import argparse
from pathlib import Path
import shutil
import hashlib
import numpy as np
import pandas as pd
from sklearn import config_context
from sklearn.metrics import silhouette_score, davies_bouldin_score
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results_v2/final_table_inputs'

def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): digest.update(block)
    return digest.hexdigest()

def metrics(features, k4_labels=None, k6_labels=None):
    df = pd.read_csv(features, dtype={'wallet': str})
    cols = [c for c in df if c not in {'wallet', 'cluster', 'old_cluster'}]
    x = df[cols].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy(np.float32)
    wallets = pd.Index(df.wallet)
    if not wallets.is_unique: raise ValueError('Duplicate feature wallets')
    feature_hash = fingerprint(features)
    checkpoint = OUT / 'internal_metrics.csv'
    old = pd.read_csv(checkpoint).set_index('k') if checkpoint.exists() else pd.DataFrame()
    samples_path = OUT / 'internal_metrics_samples.csv'
    rows, runs = [], pd.read_csv(samples_path).to_dict('records') if samples_path.exists() else []
    with threadpool_limits(limits=4), config_context(working_memory=128):
        for k in (4, 5, 6):
            path = Path(k4_labels) if k == 4 and k4_labels else ROOT / f'results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv'
            if k == 6 and k6_labels: path = Path(k6_labels)
            if len(old) and k in old.index and old.loc[k, 'status'] == 'complete' and path.exists():
                if old.loc[k].get('features_sha256') == feature_hash and old.loc[k].get('labels_sha256') == fingerprint(path):
                    rows.append(dict(k=k, **old.loc[k].to_dict()))
                    continue
            if not path.exists():
                rows.append(dict(k=k, silhouette_mean=np.nan, silhouette_std=np.nan, davies_bouldin_full=np.nan,
                                 status='missing_original_labels', wallets=len(x), sample_size=0, repeats=0))
                print(f'K{k}: original labels missing; no substitute used', flush=True)
                continue
            ref = pd.read_csv(path, dtype={'wallet': str}).set_index('wallet')
            if not ref.index.is_unique or len(ref) != len(wallets) or not wallets.isin(ref.index).all():
                raise ValueError(f'K{k}: reference population mismatch')
            y = ref.reindex(wallets).cluster.to_numpy(int)
            sizes = pd.read_csv(ROOT / f'results/eoa_only_kmeans{k}/cluster_sizes.csv').set_index('cluster')
            if not np.array_equal(np.bincount(y, minlength=k), sizes.wallet_count.to_numpy()):
                rows.append(dict(k=k, silhouette_mean=np.nan, silhouette_std=np.nan, davies_bouldin_full=np.nan,
                                 status='reference_label_size_mismatch', wallets=len(x), sample_size=0, repeats=0))
                print(f'K{k}: reference labels mismatch; refusing substitute', flush=True)
                continue
            expected = pd.read_csv(ROOT / f'results/eoa_only_kmeans{k}/cluster_feature_medians_robust_scaled.csv').set_index('cluster')
            actual = df[cols].assign(cluster=y).groupby('cluster').median()
            if not np.allclose(actual[cols], expected[cols], rtol=1e-5, atol=1e-6):
                raise ValueError(f'K{k}: scaled feature profiles mismatch')
            db = float(davies_bouldin_score(x, y))
            scores = []
            for repeat in range(5):
                seed = 42 + repeat
                idx = np.random.default_rng(seed).choice(len(x), 20000, replace=False)
                score = float(silhouette_score(x[idx], y[idx]))
                scores.append(score)
                runs.append(dict(k=k, repeat=repeat+1, seed=seed, sample_size=len(idx), silhouette=score))
                pd.DataFrame(runs).to_csv(OUT / 'internal_metrics_samples.csv', index=False)
                print(f'K{k}: sample {repeat+1}/5 silhouette={score:.6f}', flush=True)
            rows.append(dict(k=k, silhouette_mean=np.mean(scores), silhouette_std=np.std(scores),
                             davies_bouldin_full=db, status='complete', wallets=len(x), sample_size=20000, repeats=5,
                             features_sha256=feature_hash, labels_sha256=fingerprint(path)))
            pd.DataFrame(rows).to_csv(OUT / 'internal_metrics.csv', index=False)
    pd.DataFrame(rows).to_csv(OUT / 'internal_metrics.csv', index=False)

def package():
    from build_k_evidence_matrix import make_matrix
    table = make_matrix().drop(columns=['silhouette_mean'])
    fixed = pd.read_csv(OUT / 'internal_metrics.csv')
    table = table.merge(fixed, on='k', validate='one_to_one')
    sizes = pd.read_csv(ROOT / 'results_v2/feature_role_checks/internal_metrics_k4_k5_k6.csv')
    table = table.merge(sizes[['k','min_cluster_share','max_cluster_share']], on='k', validate='one_to_one')
    table['profile_heatmap'] = table.k.map(lambda k: f'results_v2/feature_role_checks/k{k}_profile_heatmap.pdf')
    table.to_csv(OUT / 'table_iii.csv', index=False)
    shown = table[['k','min_cluster_share','max_cluster_share','seed_stability_ari','silhouette_mean','silhouette_std',
                   'davies_bouldin_full','network_holm_sig_months','network_mean_observed_minus_null',
                   'self_transition_observed_vs_expected','temporal_kappa','two_step_holm_sig_triples','paper_interpretation','status']]
    shown = shown.fillna('Pending original labels')
    (OUT / 'table_iii.tex').write_text(shown.to_latex(index=False, escape=True), encoding='utf-8')
    manifest = []
    for name, source in {
        'table_vii_metrics.csv':'temporal_k4_k5_k6/table_vii_metrics.csv',
        'table_vii_state_profiles.csv':'temporal_k4_k5_k6/table_vii_state_profiles.csv',
        'table_viii_k5.csv':'temporal_k4_k5_k6/table_viii_k5_inputs.csv',
        'table_iv_raw_medians.csv':'feature_role_checks/k5_raw_role_medians.csv',
        'table_vi_network.csv':'network_k4_k5_k6_B999/network_summary.csv',
    }.items():
        shutil.copyfile(ROOT / 'results_v2' / source, OUT / name)
        manifest.append(dict(output=name, source='results_v2/'+source))
    holdout = pd.read_csv(ROOT / 'results_v2/feature_role_checks/feature_holdout_summary_with_persistence.csv')
    holdout[holdout.scenario != 'all_features_resample_baseline'].to_csv(OUT / 'table_v_k5.csv', index=False)
    manifest.extend([
        dict(output='table_iii.csv',source='results_v2/model_evidence_matrix/k4_k5_k6_evidence_matrix.csv + final_table_inputs/internal_metrics.csv + feature_role_checks/internal_metrics_k4_k5_k6.csv'),
        dict(output='table_v_k5.csv',source='results_v2/feature_role_checks/feature_holdout_summary_with_persistence.csv'),
    ])
    base = ROOT / 'results/full_eoa_temporal_signal_streaming_k5/model_selection'
    scores = pd.read_csv(base / 'temporal_signal_model_selection_summary.csv')
    scores['recomputed_score'] = scores.silhouette_sample.fillna(-1)+.25*scores.seed_stability_mean_ari.fillna(0)-np.maximum(0,scores.cluster_share_max-.75)-np.maximum(0,.01-scores.cluster_share_min)
    if not np.allclose(scores.selection_score, scores.recomputed_score, atol=1e-12): raise ValueError('Score audit failed')
    scores.signal_type = scores.signal_type.replace({'wavelength':'spectral'})
    scores.to_csv(OUT / 'selection_score_audit.csv', index=False)
    td = pd.read_csv(base / 'followup_analyses/behavior_k5_time_domain_outcome_profile.csv')
    td = td.sort_values(['k_cluster','within_behavior_share'], ascending=[True,False]).groupby('k_cluster').head(1)
    td = td.drop(columns=['total_tx_median'])
    td['scope'] = 'mean_among_dominant_TD_subgroup_wallets'
    td.to_csv(OUT / 'table_xi_dominant_td.csv', index=False)
    manifest.extend([
        dict(output='table_xi_dominant_td.csv',source=str((base/'followup_analyses/behavior_k5_time_domain_outcome_profile.csv').relative_to(ROOT))),
        dict(output='selection_score_audit.csv',source=str((base/'temporal_signal_model_selection_summary.csv').relative_to(ROOT))),
        dict(output='signal_state_profiles.csv',source=str(base.relative_to(ROOT))+'/time_domain_k5_cluster_profiles.csv + wavelength_k3_cluster_profiles.csv'),
    ])
    state_rows = []
    descriptions = ['intermediate activity with variable daily counts', 'sparse activity with long inactive gaps',
                    'sparse activity with relatively uniform active-day counts', 'intermediate recurrent activity',
                    'frequent activity with intermittent switching']
    for family, filename in [('TD','time_domain_k5_cluster_profiles.csv'), ('F','wavelength_k3_cluster_profiles.csv')]:
        profiles = pd.read_csv(base / filename)
        for row in profiles.to_dict('records'):
            c = int(row.pop('cluster'))
            row.update(state=f'{family}{c}', summary_statistic='mean',
                       description=descriptions[c] if family=='TD' else ['distributed high-frequency activity','mixed-frequency activity','concentrated activity'][c])
            state_rows.append(row)
    pd.DataFrame(state_rows).to_csv(OUT/'signal_state_profiles.csv', index=False)
    pd.DataFrame(manifest).to_csv(OUT / 'source_manifest.csv', index=False)
    pd.DataFrame({'path':[str(p.relative_to(ROOT)) for p in (ROOT/'results_v2').rglob('*.pdf')]}).to_csv(OUT/'figure_list.csv', index=False)
    print(table[['k','status','silhouette_mean','davies_bouldin_full']].to_string(index=False), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--features', type=Path, default=ROOT/'results/eoa_only_kmeans6/wallet_eoa_only_kmeans6_features_robust_scaled.csv')
    parser.add_argument('--k4-labels', type=Path)
    parser.add_argument('--k6-labels', type=Path)
    parser.add_argument('--package-only', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.package_only: metrics(args.features, args.k4_labels, args.k6_labels)
    package()
