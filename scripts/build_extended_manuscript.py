"""Build the extended manuscript from completed controlled-pipeline results."""
import json
import re
import hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results_v3/year_end_2022_count_cohort'
OUT=ROOT/'overleaf'


def table(label,caption,columns,header,rows,wide=False):
    env='table*' if wide else 'table'
    return '\n'.join([r'\begin{'+env+'}[t]',r'\centering\footnotesize',
        r'\caption{'+caption+'}',r'\label{tab:'+label+'}',
        r'\begin{tabular}{'+columns+'}',r'\toprule',header+r' \\',r'\midrule',
        *[row+r' \\' for row in rows],r'\bottomrule',r'\end{tabular}',r'\end{'+env+'}'])


def span(v):return f'{v.min():.3f}--{v.max():.3f}'


def validate_inputs(root,expected):
    for name,wanted in expected.items():
        path=root/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=wanted:
            raise ValueError(f'Result input changed: {name}; revise the narrative before rebuilding')


def main():
    if (BASE/'signals/manifest.json').exists():
        raise RuntimeError('The signal-integrated manuscript is edited in overleaf/main.tex. '
                           'The legacy extended_body.tex must not overwrite it; '
                           'see scripts/publish_year_end_signal_manuscript.py and the frozen input manifest.')
    frozen=json.loads((OUT/'manuscript_inputs.json').read_text())
    validate_inputs(ROOT,frozen['input_sha256'])
    receipt=json.loads((BASE/'validation_completion.json').read_text())
    if not receipt['complete'] or receipt['network_tests']!=84 or receipt['monthly_return_holm_family']!=20:
        raise ValueError('Completed annual/network/monthly pipeline required')
    old=(OUT/'main.tex').read_text()
    prefix=old[:old.index(r'\begin{abstract}')]
    prefix=prefix.replace('\\usepackage{balance}\n','')
    prefix=re.sub(r'\\title\{[^\n]+\}',lambda _:r'\title{Ethereum Wallet Segmentation Through Cohort-Controlled Layered Validation}',prefix)
    bibliography=old[old.index(r'\begin{thebibliography}'):]
    body=(OUT/'extended_body.tex').read_text()
    fit=pd.read_csv(BASE/'annual/annual_fit_runs.csv')
    stable=pd.read_csv(BASE/'annual/annual_seed_stability.csv')
    hold=pd.read_csv(BASE/'annual/k3_feature_holdout_sensitivity.csv')
    network=pd.read_csv(BASE/'network_comparison/comparison_summary.csv')
    profiles=pd.read_csv(BASE/'annual/profiles_k3/annual_exact_raw_profiles_seed492_k3.csv')
    monthly=pd.read_csv(BASE/'monthly_k2_k6/comparison_summary.csv')
    returns=pd.read_csv(BASE/'monthly_k2_k6/heldout_two_step_returns.csv')
    parts={}
    parts['LAYER_TABLE']=table('layers','Validation layers and inferential boundaries.',
        r'@{}p{.18\columnwidth}p{.32\columnwidth}p{.38\columnwidth}@{}',
        'Layer & Question & Boundary',[
        'Cohort & Which historical addresses are retained? & One-block code status; not continuous EOA identity',
        'Annual fits & Does initialization recover similar groups? & Three seeds in one representation',
        'Holdouts & Does feature removal change K3? & Measurement sensitivity; not ground truth',
        'Network & Do labels align with transfer endpoints? & Fixed sampled graph; not degree-controlled causality',
        'Monthly states & Is held-out state movement structured? & Separate model; active observations only'])
    parts['COHORT_TABLE']=table('cohort','Historical cohort accounting within the supplied feature universe.',
        'lr','Quantity & Addresses',[
        'Starting annual feature universe & 2,738,243',
        'Previously retained by earlier filter & 2,443,868',
        'Retained at year-end 2022 & 2,508,997',
        'Nonempty code at year-end & 229,246',
        'Shared by earlier and year-end lists & 2,443,852',
        'Added relative to earlier list & 65,145',
        'Removed relative to earlier list & 16',
        'Unresolved historical outcomes & 0'])
    parts['FEATURE_TABLE']=table('features','Annual feature families. Amount magnitudes are excluded; directional flags use positive daily amounts.',
        r'@{}p{.27\columnwidth}p{.65\columnwidth}@{}','Family & Measurements',[
        'Activity level (5) & Active days; total transfer count; average, maximum and standard deviation of daily count',
        'Persistence/ concentration (4) & Activity span; activity density; count coefficient of variation; transaction concentration',
        'Directionality (7) & Incoming-, outgoing-, both-active days; their three active-day ratios; directional day balance'])
    rows=[]
    for k in range(2,7):
        f=fit[(fit.k==k)&(fit.seed==492)].iloc[0]; s=stable[stable.k==k]
        rows.append(f'{k} & {f.silhouette:.3f} & {span(s.ari)} & {span(s.hungarian_agreement)}')
    parts['ANNUAL_TABLE']=table('annual','Annual separation and full-population initialization agreement. Silhouette uses seed 492 and a fixed sample.',
        'rrrr','$k$ & Silhouette & ARI range & Matched range',rows)
    names=['Sustained activity','Distributed lower activity','Short-span concentrated']
    rows=[]
    for c in range(3):
        p=profiles[profiles.cluster==c].set_index('feature'); n=int(p.iloc[0]['n'])
        v=lambda name:p.loc[name,'median']
        rows.append(f'{names[c]} & {n:,} & {100*n/2508997:.1f} & {v("active_days_observed"):.0f} & {v("total_tx"):.0f} & {v("activity_span_days"):.0f} & {v("activity_density"):.3f} & {v("tx_concentration_ratio"):.3f}')
    parts['PROFILE_TABLE']=table('profiles','Annual K3 raw-unit medians for seed 492. Density and peak concentration are ratios; share is a percentage.',
        'lrrrrrrr','Profile & Addresses & Share & Active days & Transfers & Span (days) & Density & Concentration',rows,True)
    family_names={'activity_level':'Activity level','persistence_concentration':'Persistence/concentration','directionality':'Directionality'}
    parts['HOLDOUT_TABLE']=table('holdouts','Matched-MiniBatchKMeans feature-family removals relative to full-feature annual K3.',
        'lrrrr','Removed family & Columns & ARI & NMI & Matched',[
        f'{family_names[r.removed_family]} & {r.features_removed} & {r.ari_vs_full_k3:.3f} & {r.nmi_vs_full_k3:.3f} & {r.hungarian_agreement_vs_full_k3:.3f}' for r in hold.itertuples()])
    parts['NETWORK_TABLE']=table('network','Network support under the 84-test Holm family. Excess is averaged across months and expressed in percentage points.',
        'rrrrr','$k$ & Seed & Mean excess & Supported & Max. adjusted $p$ ',[
        f'{int(r.k)} & {int(r.label_seed)} & {100*r.mean_excess:.2f} & {int(r.significant_months)}/12 & {r.max_adjusted_p:.4f}' for r in network.itertuples()])
    parts['PERSISTENCE_TABLE']=table('persistence','Held-out monthly persistence, marginal chance and chance-adjusted agreement across five adjacent pairs.',
        'rccc',r'$k$ & Persistence & Chance & $\kappa$',[
        f'{int(r.k)} & {r.persistence_min:.3f}--{r.persistence_max:.3f} & {r.chance_min:.3f}--{r.chance_max:.3f} & {r.kappa_min:.3f}--{r.kappa_max:.3f}' for r in monthly.itertuples()])
    months={202207:'Jul--Sep',202208:'Aug--Oct',202209:'Sep--Nov',202210:'Oct--Dec'}
    parts['RETURN_TABLE']=table('returns','Monthly K3 conditional returns among first-step switchers. Adjusted p-values use the full twenty-test temporal family.',
        'lrrrrr','Triple & Switchers & Observed & Null & Excess (pp) & Adj. $p$',[
        f'{months[r.month_start]} & {r.n_switchers:,} & {r.observed:.3f} & {r.null_mean:.3f} & {100*(r.observed-r.null_mean):.2f} & {r.p_holm_all_tests:.3f}' for r in returns[returns.k==3].itertuples()])
    parts['RETURN_SUMMARY_TABLE']=table('returnsummary','Monthly return comparisons. The binary K2 null is structurally constant, so its p-value is uninformative.',
        'rcrr','$k$ & Return excess (pp) & Supported & Max. adj. $p$',[
        f'{int(r.k)} & '+('Degenerate' if r.k==2 else f'{100*r.return_excess_min:.2f}--{100*r.return_excess_max:.2f}')+f' & {int(r.significant_returns)}/4 & {r.max_adjusted_return_p:.3f}' for r in monthly.itertuples()])
    for name,value in parts.items():
        body=body.replace('@@'+name+'@@',value)
    if '@@' in body:raise ValueError('Unfilled table placeholder')
    # IEEE references are numbered in order of first citation.
    entries=dict(re.findall(r'\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\\end\{thebibliography\})',bibliography,re.S))
    ordered=list(dict.fromkeys(key for group in re.findall(r'\\cite\{([^}]+)\}',body) for key in group.split(',')))
    if set(ordered)!=set(entries):raise ValueError('Missing or uncited bibliography entry')
    bibliography='\\begin{thebibliography}{99}\n'+''.join('\\bibitem{'+key+'} '+entries[key].strip()+'\n' for key in ordered)+'\\end{thebibliography}\n\\end{document}\n'
    (OUT/'main.tex').write_text(prefix+body+'\n'+bibliography,encoding='utf-8')
    x=np.arange(len(hold));width=.25
    fig,ax=plt.subplots(figsize=(6.2,3.3))
    for j,(col,label) in enumerate([('ari_vs_full_k3','ARI'),('nmi_vs_full_k3','NMI'),('hungarian_agreement_vs_full_k3','Matched agreement')]):
        ax.bar(x+(j-1)*width,hold[col],width,label=label)
    ax.set(xticks=x,xticklabels=['Activity level','Persistence / concentration','Directionality'],ylim=(0,1),ylabel='Agreement with full K3')
    ax.tick_params(axis='x',labelsize=8);ax.legend(frameon=False,fontsize=8,ncol=3);ax.grid(axis='y',alpha=.2);fig.tight_layout()
    fig.savefig(OUT/'figures/matched_feature_holdouts.pdf',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.2,3.3))
    for k,g in returns[returns.k>2].groupby('k'):
        ax.plot(range(4),100*(g.observed-g.null_mean),marker='o',label=f'K{k}')
    ax.set(xticks=range(4),xticklabels=['Jul-Sep','Aug-Oct','Sep-Nov','Oct-Dec'],ylabel='Return excess (percentage points)')
    ax.legend(frameon=False,ncol=4);ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(OUT/'figures/conditional_return_comparison.pdf',bbox_inches='tight');plt.close(fig)
    print('Extended manuscript built; approximate body words:',len(re.findall(r'\b\w+\b',body)))


if __name__=='__main__':main()
