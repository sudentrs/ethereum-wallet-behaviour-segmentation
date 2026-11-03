"""Synchronize manuscript claims with complete, verified compact validation tables."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results_v3/year_end_2022_count_cohort'


def section(text,start,end,replacement):
    a=text.index(start);b=text.index(end,a)
    return text[:a]+replacement+'\n\n'+text[b:]


def span(values,digits=3):
    lo,hi=values.min(),values.max()
    return f'{lo:.{digits}f}' if lo==hi else f'{lo:.{digits}f}--{hi:.{digits}f}'


def main():
    current=ROOT/'overleaf/main.tex'
    if (ROOT/'overleaf/manuscript_inputs.json').exists():
        from scripts.build_extended_manuscript import main as rebuild_extended
        rebuild_extended()
        return
    receipt=json.loads((BASE/'validation_completion.json').read_text())
    if not receipt['complete']:
        raise ValueError('Complete validation required before editing claims')
    network=pd.read_csv(BASE/'network_comparison/network_comparison.csv')
    summary=pd.read_csv(BASE/'network_comparison/comparison_summary.csv')
    pairs=pd.read_csv(BASE/'monthly_k3/heldout_persistence.csv')
    triples=pd.read_csv(BASE/'monthly_k3/heldout_two_step_returns.csv')
    monthly_summary=pd.read_csv(BASE/'monthly_k2_k6/comparison_summary.csv')
    ref=network[(network.k==3)&(network.label_seed==492)]
    positive=int((ref.p_holm_84<.05).sum())
    seed_text='; '.join(f"seed {int(r.label_seed)}: {int(r.significant_months)}/12 months" for r in summary[summary.k==3].itertuples())
    comparison='; '.join(f"K{int(r.k)}: {int(r.significant_months)}/12" for r in summary[summary.label_seed==492].itertuples())
    stability=pd.read_csv(BASE/'annual/annual_seed_stability.csv')
    rows=[]
    for r in summary[summary.label_seed==492].itertuples():
        values=stability.loc[stability.k==r.k,'ari']
        rows.append(f"{int(r.k)} & {span(values)} & {100*r.mean_excess:.2f} & {int(r.significant_months)}/12 "+r"\\")
    comparison_table=r'''\begin{table}[t]
\centering
\caption{Annual stability and network diagnostics. Excess is the mean sampled observed-minus-null difference in percentage points. Network columns use seed 492 and the full 84-test Holm correction.}
\label{tab:resolutioncomparison}
\begin{tabular}{rrrr}
\toprule
$k$ & Seed ARI range & Excess (pp) & Supported months \\
\midrule
'''+ '\n'.join(rows)+r'''
\bottomrule
\end{tabular}
\end{table}
'''
    tex=ROOT/'overleaf/main.tex'
    text=tex.read_text()
    methods=r'''\subsection{Transaction-Network Null Test}
We compare annual K2--K6 seed-492 labels and repeat K3 using seeds 493 and 494.
For each month, we retain transfer rows whose sender and recipient both belong to the year-end code-free cohort and draw one uniform 200,000-row priority sample shared by all seven solutions.
Repeated transfer rows and self-transfers are retained. The observed statistic is the same-label transfer fraction.
The null preserves the sampled graph and permutes labels among its unique endpoint wallets 9,999 times, using common wallet permutations across solutions.
We apply Holm correction across the full family of 84 solution-by-month tests. The larger permutation count is needed because 999 permutations cannot resolve a first Holm rejection at 0.05 for 84 tests.
This tests label--network alignment, not causality, community identity, or degree-controlled preference. We compare excess over each solution's null expectation rather than ranking raw same-label fractions.'''
    text=section(text,r'\subsection{Transaction-Network Null Test}',r'\section{Results}',methods)
    results=(r'\subsection{Transaction-Network Alignment}'+'\n'+
        f'The annual K3 seed-492 solution has above-null same-state transfer concentration in {positive}/12 months after the 84-test Holm correction.\n'+
        f'Its sampled observed fraction is {span(ref.observed)} (mean {ref.observed.mean():.3f}), compared with null means {span(ref.null_mean)} (mean {ref.null_mean.mean():.3f}).\n'+
        f'The mean observed-minus-null difference is {ref.excess.mean():.3f}, with monthly differences {span(ref.excess)}. Raw permutation p-values are {span(ref.p_raw,4)} and adjusted p-values are {span(ref.p_holm_84,4)}.\n'+
        f'For seed 492, corrected support is {comparison}. For K3 initialization sensitivity, corrected support is {seed_text}.\n'+
        r'''These comparisons are descriptive evidence under a common null, not a direct test that one partition is superior to another. Finer partitions do not automatically provide stronger network alignment, and alignment is not unique to K3. K3 remains a working resolution selected primarily for initialization stability and interpretable profiles. Table~\ref{tab:resolutioncomparison} makes the tradeoff explicit: K4 has larger mean network excess but much lower initialization stability.
'''+comparison_table+r'''

\begin{figure*}[t]
\centering
\includegraphics[width=0.95\textwidth]{figures/network_comparison_overview.pdf}
\caption{Observed-minus-null transfer concentration on shared monthly samples: annual resolutions at seed 492 (left), and K3 initialization sensitivity (right). Differences below zero are descriptive; the confirmatory tests use the upper tail.}
\label{fig:networkcomparison}
\end{figure*}

Coverage remains limited to 13.7\%--19.3\% of raw monthly ERC-20 transfers with two cohort endpoints.
The result concerns this retained subgraph, not the entire ERC-20 network. Shuffling breaks degree--label associations, so shared applications and degree effects remain possible explanations.''')
    text=section(text,r'\subsection{Transaction-Network Alignment}',r'\subsection{Held-Out Monthly States}',results)
    monthly=(r'\subsection{Held-Out Monthly States}'+'\n'+
        f'The independently trained monthly model uses validated wallet-day inputs and deterministic wallet ordering before seeded sampling. Across held-out adjacent pairs, {int(pairs.n.min()):,}--{int(pairs.n.max()):,} wallets are active in both months.\n'+
        f'Observed persistence is {span(pairs.observed)}, compared with chance agreement {span(pairs.chance)}; '+r'$\kappa$'+f' is {span(pairs.kappa)}.\n'+
        r'''\begin{figure}[t]
\centering
\includegraphics[width=0.92\columnwidth]{figures/k3_heldout_transition_matrix.pdf}
\caption{Held-out transition probabilities for the deterministic frozen monthly model. Monthly state IDs are not annual K3 role IDs.}
\label{fig:monthly}
\end{figure}
'''+
        f'Among first-step switchers active in all three required months, observed K3 two-step return is {span(triples.observed)}, versus null means {span(triples.null_mean)}. Raw p-values are {span(triples.p)} and 20-test Holm-adjusted p-values are {span(triples.p_holm_all_tests)}.\n'+
        'This evidence is conditional on active wallet-months and the retrospectively defined year-end cohort; it is not prospective forecasting or a causal explanation of state movement.')
    monthly+='\nMonthly K2--K6 were trained on the same deterministic sample and evaluated on the same held-out months. Corrected two-step-return support is '+ '; '.join(
        f"K{int(r.k)}: {int(r.significant_returns)}/4 triples" for r in monthly_summary.itertuples())+'. These monthly resolutions are compared separately from annual labels. For binary K2, first-step switchers have a starting state determined by the middle state; within-middle-state shuffling therefore leaves the return statistic unchanged. Its p=1 is structurally uninformative, not evidence against temporal structure.\n'+r'''
\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/monthly_resolution_comparison.pdf}
\caption{Held-out persistence above marginal chance for independently trained monthly K2--K6 models on shared count-only inputs.}
\label{fig:monthlycomparison}
\end{figure}
'''
    text=section(text,r'\subsection{Held-Out Monthly States}',r'\section{Discussion}',monthly)
    old='In all twelve monthly transaction snapshots, same-state transfer concentration exceeds a shuffled-label null; held-out July--December state persistence also exceeds chance agreement and two-step returns exceed a shuffled future-state null after Holm correction.'
    count_text='all twelve' if positive==12 else f'{positive} of twelve'
    new=f'In {count_text} monthly snapshots, annual K3 seed-492 transfer concentration exceeds a shuffled-label null after correction across 84 network tests; held-out monthly persistence and two-step return also exceed their respective baselines.'
    text=text.replace(old,new)
    text=text.replace('A corrected network null test finds above-null same-state transfer concentration in every monthly snapshot, and a separate frozen monthly model finds above-chance persistence and two-step return in held-out data.',
        f'A shared-sample network comparison finds corrected above-null concentration for annual K3 seed 492 in {positive}/12 monthly snapshots, and a separate deterministic frozen monthly model finds above-chance persistence and above-null two-step return.')
    text=text.replace('We sample active wallet-months from January--June to fit one RobustScaler and a three-state MiniBatchKMeans model.',
        'We sort normalized wallet identifiers within each month and sample 20,000 active wallet-months per January--June training month with fixed seeds. Transactions per calendar day, transactions per active day, and daily-count coefficient of variation receive log(1+x) transforms before fitting one RobustScaler and separate MiniBatchKMeans models for K2--K6. K3 remains the main descriptive monthly illustration; its labels are distinct from annual K3.')
    text=text.replace("We apply Holm correction across the four return tests", "We apply Holm correction across all twenty return tests (five monthly resolutions and four held-out triples each)")
    text=text.replace('test whether returning to the initial state exceeds a shuffled future-state null with 999 permutations.',
        'test whether returning to the initial state exceeds a future-state null with 999 permutations restricted within the middle-state groups. This retains the observed middle-to-future transition margins among switchers.')
    text=text.replace('especially temporal persistence and concentration features.','especially activity level and temporal persistence/concentration features.')
    text=text.replace('depends especially on persistence/concentration information.',
                      'depends especially on activity level and persistence/concentration information.')
    tex.write_text(text,encoding='utf-8')
    print('Manuscript synchronized to verified current tables.')


if __name__=='__main__':
    main()
