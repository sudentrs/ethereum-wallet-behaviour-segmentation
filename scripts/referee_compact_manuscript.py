"""Self-contained main-text methods and compact evidence tables.

Full extension settings and all extension tables are separately preserved by the
publisher in supplementary.tex. This module does not run a LaTeX engine.
"""
import re
import json
import pandas as pd
import numpy as np

METHODS=r'''\section{Methodology}
\subsection{Study Design and Historical Cohort}
The study uses the ERC-20 Trading 2022 release \cite{somin2025erc2022,somin2025dataset}. Its supplied annual feature universe contains 2,738,243 addresses. A complete historical scan queries code at block 16,308,189, the final Ethereum block of 2022: 2,508,997 addresses have exactly empty code and 229,246 have nonempty code, with no unresolved queries. Membership and row order are frozen with checksums. This defines a year-end code-free cohort, not continuous EOA status. The upstream selection that created the supplied feature universe is not independently reconstructed, so cluster shares do not estimate prevalence across all Ethereum users.

The same membership supports three descriptions: annual aggregate roles, separately learned monthly states and full-year daily signals (Fig.~\ref{fig:pipeline}). Raw network processing covers 245,911,059 transfer rows across twelve months. Wallet-day sources are checked for normalized valid addresses, dates within the expected month, unique wallet--day rows, and finite nonnegative integer counts. Counts denote wallet-record incidence, not distinct blockchain transactions: a transfer contributes sender and recipient records, including two incidences for a self-transfer. Daily signal totals reconcile exactly with the annual count source for every retained address.

\begin{figure*}[t]
\centering
\resizebox{\textwidth}{!}{\input{figures_current/framework_pipeline.tex}}
\caption{Layered behavioural evaluation on a fixed historical cohort. Annual K2--K6 comparisons yield the main K3 description; independent monthly state models and daily signal representations answer different questions. Sensitivity analyses and simple baselines qualify the joint interpretation.}
\label{fig:pipeline}
\end{figure*}

\subsection{Annual Features and Partition Robustness}
Sixteen features form three families. Activity level contains observed days, total count, and observed-day count mean, maximum and standard deviation. Persistence/concentration contains inclusive first-to-last span, observed days divided by span, count coefficient of variation, and maximum-day count divided by total count. Directionality contains incoming-, outgoing- and both-active days, their three observed-day ratios, and incoming-minus-outgoing day balance divided by observed days. Directional flags use positive pooled daily incoming/outgoing amounts; zero-value transfers can contribute counts without activating a flag. Amount magnitudes are excluded, but direction flags retain this preprocessing dependence.

Counts and durations receive $\log(1+x)$; ratios, balance, coefficient of variation and concentration remain untransformed. Each column is centred by its cohort median and divided by its interquartile range, using one for a zero range. The annual matrix contains no token-price, gas, identity or legacy-cluster input. Correlated features and seven direction coordinates can implicitly weight related measurements more than once.

MiniBatchKMeans fits K2--K6 using seeds 492--494, ten initializations, batch size 8,192 and 200 maximum iterations. Silhouette uses the same 5,000-address sample at seed 492; seed ARI/NMI and matched agreement use all addresses \cite{hubert1985partitions,vinh2010information,kuhn1955hungarian,rousseeuw1987silhouettes}. K3 feature-family removals retain estimator settings and the original scaling of surviving columns.

Additional retrospective controls fix 50,000 evaluation addresses and exclude them from every new fit. At each K2--K6, thirty fits use independent 100,000-address subsets and twenty use 80\% of the remaining cohort, keeping optimizer seed 492 and the original scaler fixed. Assignments are compared with the original full-cohort reference, which did see those features; this is partition robustness conditional on scaling, not predictive validation. Matched cluster Jaccard scores complement ARI. On one shared 100,000-address subset, K3--K5 also compare batch k-means, diagonal-covariance Gaussian mixtures and equal-family weighting at three seeds. Weighting divides coordinates by the square root of their family's column count. Full settings and all cluster-level results are in the supplementary material.

\subsection{Network Nulls, Baselines and Graph Sensitivity}
For eligible sampled transfer rows $E_m$, with both endpoints in the cohort, annual labels $g$ define
\begin{equation}
H_m=|E_m|^{-1}\sum_{(u,v)\in E_m}\mathbf{1}\{g(u)=g(v)\}.
\end{equation}
The original comparison uses 200,000 shared rows per month and common permutations across seven label solutions: K2--K6 seed 492 and two additional K3 seeds. Labels are shuffled among sampled endpoint wallets while edges remain fixed, including repeated rows and self-transfers. Upper-tail Monte Carlo p-values use $(1+\#\{H_m^{(b)}\ge H_m\})/(B+1)$ with $B=9,999$. Effect size is observed minus null-mean concentration. Holm correction initially covers 84 tests \cite{holm1979sequential}.

The extension compares annual K3--K5 and two simple three-group baselines on common uniform samples of up to 50,000 non-self rows per month. One baseline uses empirical transfer-count terciles, assigning ties together to the upper interval. The other assigns span at most thirty days to one group, and splits remaining addresses at twenty-four observed active days. These illustrative thresholds are fixed without optimizing a network outcome; group sizes are not matched to K3.

Both unrestricted and activity-stratified label permutations are used. Strata combine $\lfloor\log_2(1+d_{\rm in})\rfloor$ and $\lfloor\log_2(1+d_{\rm out})\rfloor$, where counts use all eligible non-self monthly events. Shuffling preserves label composition within sampled-endpoint strata. K3 additionally tests all events, unique directed non-self pairs, exclusion of the month's most frequent eligible token, and exclusion of the top 1\% endpoints ranked by eligible non-self event activity. Deduplication and exclusions precede sampling. The 216 extension tests use 9,999 permutations each; we also correct them jointly with the original 84 tests as a 300-test family. Approximate activity strata do not control exact degree or all token exposure; changed graph populations prevent causal interpretations of sensitivity differences.

\subsection{Monthly States, Inactivity and Participation}
Monthly models use transactions per calendar day, active-day fraction, transactions per active day, calendar-day count coefficient of variation, peak-count share and inclusive span fraction. The first, third and fourth features receive $\log(1+x)$ before robust scaling. Up to 20,000 lexicographically sorted and uniformly sampled active observations per January--June month fit a shared scaler and separate K2--K6 models; centroids are frozen for July--December. Models use seed 492, ten initializations, batch size 4,096 and 100 maximum iterations. Wallets can recur in training months.

For five held-out adjacent pairs, active-only persistence $A_o$ is compared with marginal chance $A_e=\sum_c p_t(c)p_{t+1}(c)$ and $\kappa=(A_o-A_e)/(1-A_e)$ \cite{cohen1960agreement}. For four triples, return conditions on activity in all three months and a first-step switch. Future labels are shuffled within middle-state groups, preserving middle-to-future margins among switchers. There are 999 permutations and twenty K2--K6 return tests in one Holm family. Binary K2 is structurally degenerate because switchers' starting states are determined by the middle state, leaving return counts unchanged under this null.

Inactivity is additionally encoded as an observation category after K3 assignment, allowing all-cohort transitions without fitting an inactive centroid. Previously observed inactive addresses are distinguished from those not yet observed active in 2022; this is not an address-creation classification.

A separate next-month participation task learns K2--K6 vocabularies on January--March only, fits prediction models on January--May pairs (up to 50,000 active observations per month), and evaluates July--November pairs. Constant prevalence and smoothed state rates are compared with two-feature activity logistic regression, six-feature logistic regression, its K3-indicator augmentation, and six-feature histogram gradient boosting. No evaluation features or outcomes fit these models. Brier/log loss are pooled by observations, while AUC is averaged over months. Two hundred paired wallet-level Poisson bootstraps preserve repeated-wallet contributions across months for descriptive loss-difference intervals conditional on fitted models. They do not account for network dependence. This remains temporal evaluation within a retrospectively selected cohort, not prospective population-wide prediction.

\subsection{Daily Signals and Reproduction Controls}
All 365 daily counts, including zeros on absent days, are reconstructed for every cohort address. Six time-domain features summarize active fraction, longest active/inactive runs, active/inactive switches, peak share and calendar-day coefficient of variation. Frequency features apply rFFT to within-wallet centred $\log(1+x_t)$, exclude DC and normalize non-DC power. Seven summaries capture power above sixty days, fourteen--sixty days and below fourteen days, weekly/monthly bands, peak-power share and spectral entropy. Weekly and monthly bands use $1/8\le f<1/6$ and $1/35\le f<1/25$ cycles per day. Discrete bins approximate calendar periods. Zero-power signals would be excluded from both partitions; none occur here.

Each representation is robust-scaled separately, logging only count coefficient of variation beforehand. K2--K6 fits at three seeds use a shared uniform 100,000-address training sample, ten initializations, batch size 8,192 and 200 maximum iterations; assignments cover the full eligible cohort and silhouette uses 3,000 fixed addresses. Seventy-five comparisons measure annual--signal and time--frequency overlap. These are full-year descriptive fits.

A uniform 2,000-address sample tests sample-mean low-frequency share, peak-power share and negative entropy against histogram-preserving nulls. Complete daily permutation uses 999 replicates and a three-test Holm family. Additional seven- and thirty-day block permutations retain within-block order after a random circular origin, preserving the shorter final block. The three null types form a nine-test extension family. They test temporal ordering, not recurring cycles or individual-wallet significance.

Feature and matrix hashes reproduce exactly. Thirteen of fifteen annual label arrays match archived hashes; K3 seed 494 and K6 seed 493 are identified as reproduced fits under the rerun runtime. Current tables use the complete rerun. Manifests record source identity, row order, settings, samples and result hashes. All analyses are retrospective; the complementary views share source data and are not independent replications.

'''

def compact_results(OUT,BASE,tabular,span):
    pop=pd.read_csv(OUT/'population_resampling.csv');alg=pd.read_csv(OUT/'annual_algorithms.csv')
    summary=pd.read_csv(OUT/'network_summary_global300.csv');pred=pd.read_csv(OUT/'participation_pooled_scores.csv').set_index('model')
    inactive=pd.read_csv(OUT/'participation_inactivity.csv');sig=pd.read_csv(OUT/'spectral_block_tests.csv')
    ci=pd.read_csv(OUT/'participation_prediction_intervals.csv');agreement=pd.read_csv(OUT/'network_baseline_agreement.csv').set_index('partition')
    primary=pd.read_csv(BASE/'annual/annual_fit_runs.csv');stability=pd.read_csv(BASE/'annual/annual_seed_stability.csv')
    def nr(part,null):return summary[(summary.partition==part)&summary.variant.eq('nonself_events')&summary['null'].eq(null)].iloc[0]
    s=r'''\section{Results}
\subsection{Annual Resolution and Behavioural Profiles}
K2 has the highest sampled silhouette (0.357), but its largest group contains 72.4--83.2\% of addresses across seeds. K3 silhouette is 0.298, with seed ARI 0.908--0.971, NMI 0.853--0.944 and matched agreement 0.973--0.992. K4--K6 seed agreement is weaker (Table~\ref{tab:annualrobustness}). Thus K3 is selected as a compact descriptive vocabulary rather than the maximizer of separation or balanced group sizes.

'''
    rows=[]
    for k in range(2,7):
        g=pop[pop.k.eq(k)];a=primary[(primary.k==k)&(primary.seed==492)].iloc[0]
        b=stability[stability.k.eq(k)]
        ari_col='ari' if 'ari' in b.columns else 'adjusted_rand_index'
        rows.append([k,f'{a.silhouette:.3f}',span(b[ari_col]),f'{g.ari.mean():.3f}',span(g.ari)])
    s+=tabular('Annual initialization and training-subset sensitivity. Resampling uses twenty 80\\% refits, fixed optimization seed and 50,000 evaluation addresses; the original full-cohort scaler is retained.',
        'tab:annualrobustness','rcccc',r'$k$ & Silhouette & Seed ARI & Refit mean ARI & Refit range',rows,True)
    rows=[['Sustained activity','572,750','22.8',29,73,268,'0.139','0.116'],
          ['Distributed lower activity','1,746,310','69.6',9,16,173,'0.060','0.211'],
          ['Short-span concentrated','189,937','7.6',4,16,7,'0.750','0.500']]
    s+=tabular('Annual K3 seed-492 raw-unit medians. Share is a percentage; density and concentration are ratios.',
        'tab:profiles','lrrrrrrr',r'Profile & Addresses & Share & Active days & Counts & Span (days) & Density & Concentration',rows,True)
    s+=r'''The two lower-count profiles share a median of sixteen incidences but differ sharply in span (173 versus seven days). Sustained activity extends across more of the year (Table~\ref{tab:profiles}). These names summarize overlapping distributions, not controllers or applications; interquartile ranges remain in the replication tables.

Matched K3 feature-family removals yield ARI 0.393 for activity level, 0.357 for persistence/concentration and 0.711 for directionality; matched agreement is 0.780, 0.595 and 0.909. Initialization stability therefore coexists with substantial representation dependence.

'''
    k3=pop[pop.k.eq(3)];ak3=alg[alg.k.eq(3)]
    s+=(f'The larger-subset K3 refits have mean ARI {k3.ari.mean():.3f} and range {span(k3.ari)}, exposing variation missed by the three-seed check. '
        'The thirty smaller 100,000-address refits and cluster-level Jaccard distributions are reported in the supplement. '
        f'On the shared algorithm-comparison sample, K3 ARI against the annual reference is {span(ak3[ak3.variant.eq("batch_kmeans")].ari_annual)} for batch k-means, '
        f'{span(ak3[ak3.variant.eq("diagonal_gmm")].ari_annual)} for the diagonal mixture and {span(ak3[ak3.variant.eq("equal_family_weight")].ari_annual)} under equal-family weighting. '
        'These outcomes qualify the interpretation as dependent on training addresses and estimator geometry.\n\n')
    s+=r'''\subsection{Network Alignment and Stronger Controls}
The complete eligible subgraph contains 38,733,517 rows, or 15.75\% of processed transfers (monthly coverage 13.7--19.3\%). In the original 200,000-event samples, K3 seed 492 has mean excess 9.09 percentage points and twelve supported months under the original 84-test family; the other K3 seeds have mean excess 8.40 and 9.54 points and twelve supported months each. K4 has greater mean excess (14.19 points), while K5 has 8.35; K2 and K6 have negative mean excess. This is not a universal resolution ranking.

'''
    rows=[]
    for part,name in [('annual_k3','Annual K3'),('annual_k4','Annual K4'),('annual_k5','Annual K5'),('transfer_terciles','Count terciles'),('span_activity_rule','Span/activity rule')]:
        a=nr(part,'unrestricted');b=nr(part,'activity_stratified')
        rows.append([name,f'{100*a.mean_excess:.2f}',f'{100*b.mean_excess:.2f}',f'{int(b.supported)}/12',f'{b.max_adjusted_p:.4f}'])
    s+=tabular('Common non-self event samples: mean excess in percentage points under unrestricted and activity-stratified nulls. Support and maximum p-value use the stratified null and combined 300-test Holm correction.',
        'tab:conditionednetwork','lrrrr',r'Partition & Unrestricted & Stratified & Supported & Max. adjusted $p$',rows,True)
    n3=nr('annual_k3','activity_stratified')
    s+=(f'After activity stratification, non-self K3 mean excess is {100*n3.mean_excess:.2f} points with {int(n3.supported)}/12 supported months (Table~\\ref{{tab:conditionednetwork}}). '
        f'The count-tercile and span/activity baselines have ARI {agreement.loc["transfer_terciles","ari_annual_k3"]:.3f} and {agreement.loc["span_activity_rule","ari_annual_k3"]:.3f} with K3. '
        'They test whether readily interpretable rules also capture graph alignment. Baseline group shares differ from K3, so the table cannot establish predictive or semantic superiority from excess alone.\n\n')
    rows=[]
    for variant,name in [('all_events','All events'),('nonself_events','Non-self events'),('unique_pairs','Unique directed pairs'),('without_top_token','Without top token'),('without_top_1pct_hubs','Without top 1\\% endpoints')]:
        a=summary[(summary.partition=='annual_k3')&summary.variant.eq(variant)&summary['null'].eq('activity_stratified')].iloc[0]
        rows.append([name,f'{100*a.mean_excess:.2f}',f'{int(a.supported)}/12'])
    s+=tabular('K3 graph sensitivity under activity-stratified randomization; excess is in percentage points and support uses the combined 300-test family.',
        'tab:graphsensitivity','lrr',r'Graph variant & Mean excess & Supported',rows)
    hub=summary[(summary.partition=='annual_k3')&summary.variant.eq('without_top_1pct_hubs')&summary['null'].eq('activity_stratified')].iloc[0]
    unique=summary[(summary.partition=='annual_k3')&summary.variant.eq('unique_pairs')&summary['null'].eq('activity_stratified')].iloc[0]
    s+=(f'Removing the most active 1\\% of endpoints yields mean activity-stratified excess {100*hub.mean_excess:.2f} points and {int(hub.supported)}/12 supported months, '
        f'whereas unique directed pairs have {int(unique.supported)}/12 supported months. '
        'This contrast shows that graph composition and transfer multiplicity materially change the association (Table~\\ref{tab:graphsensitivity}). '
        'It does not isolate a causal hub effect. Monthly coverage, exact excluded-token identifiers and both nulls are retained in the supplement and replication tables.\n\n')
    s+=r'''\subsection{Monthly Persistence, Return and Inactivity}
Held-out K3 adjacent pairs contain 676,741--786,661 addresses active in both months. Persistence is 0.639--0.702 against marginal chance 0.491--0.539, giving kappa 0.292--0.353. Monthly K2 has larger kappa, so the temporal branch does not select K3 as an optimal resolution. Monthly IDs have no shared semantics with annual cluster numbers.

'''
    comp=pd.read_csv(BASE/'monthly_k2_k6/comparison_summary.csv').set_index('k')
    ret=pd.read_csv(BASE/'monthly_k2_k6/heldout_two_step_returns.csv')
    pairs=pd.read_csv(BASE/'monthly_k2_k6/heldout_persistence.csv');rows=[]
    for k in range(2,7):
        p=pairs[pairs.k.eq(k)];r=ret[ret.k.eq(k)]
        excess=(r.observed-r.null_mean)*100
        rows.append([k,span(p.observed),span(p.kappa),'Degenerate' if k==2 else span(excess,2),'--' if k==2 else f'{int((r.p_holm_all_tests<.05).sum())}/4'])
    s+=tabular('Frozen monthly models: active-only persistence and kappa; conditional return excess in percentage points. Return support uses twenty-test Holm correction. K2 return p=1 is structurally uninformative.',
        'tab:monthlycomparison','rcccc',r'$k$ & Persistence & $\kappa$ & Return excess & Supported',rows,True)
    s+=r'''Among first-step switchers active across each triple, K3 observed return is 0.409--0.471 against null means 0.383--0.448. Excess is only 1.88--2.58 percentage points despite corrected p=0.020 for all four triples. K4--K6 also have four supported triples each (Table~\ref{tab:monthlycomparison}), but each resolution changes the switcher population and the meaning of return.

'''
    a=inactive[inactive.group.eq('currently_active')];b=inactive[inactive.group.eq('previously_seen_inactive')];c=inactive[inactive.group.eq('not_yet_seen_in_2022')]
    s+=(f'Including inactivity, next-month activity among currently active addresses ranges from {span(a.next_activity_rate)}. '
        f'It ranges from {span(b.next_activity_rate)} among previously observed but currently inactive addresses, and from {span(c.next_activity_rate)} among those not yet observed active in 2022. '
        'Active-only persistence omits these distinct participation paths; the complete inactive-inclusive transition matrix is supplied separately.\n\n')
    s+='\\subsection{Participation Baselines and Predictive Limits}\n'
    names=[('constant','Constant prevalence'),('activity','Two-feature logistic'),('all_count','Six-feature logistic'),('nonlinear_count','Six-feature boosting'),('k3_state_only','K3 state only'),('all_count_plus_k3','Six features + K3')]
    rows=[[name]+[f'{pred.loc[key,c]:.4f}' for c in ['brier','log_loss','auc']] for key,name in names]
    s+=tabular('Later-period next-month participation: pooled Brier/log loss (lower is better) and mean monthly AUC (higher is better). These are early-period monthly states, not annual roles.',
        'tab:participationprediction','lrrr',r'Model & Brier & Log loss & AUC',rows)
    s+=(f'K3 state-only predictions improve on constant prevalence in Brier score ({pred.loc["k3_state_only","brier"]:.4f} versus {pred.loc["constant","brier"]:.4f}), '
        f'but the two-feature activity baseline scores {pred.loc["activity","brier"]:.4f} and nonlinear count baseline {pred.loc["nonlinear_count","brier"]:.4f}. '
        'A compact state vocabulary therefore does not demonstrate predictive superiority over the underlying activity measurements (Table~\\ref{tab:participationprediction}).\n\n')
    b=ci[(ci.metric=='brier')&ci.contrast.eq('all_count_plus_k3 minus all_count')].iloc[0]
    l=ci[(ci.metric=='log_loss')&ci.contrast.eq('all_count_plus_k3 minus all_count')].iloc[0]
    s+=(f'Adding K3 indicators to six-feature logistic regression changes pooled Brier score by {b.difference:.6f} (paired wallet-bootstrap 95\\% interval {b.lower:.6f} to {b.upper:.6f}) '
        f'and log loss by {l.difference:.6f} ({l.lower:.6f} to {l.upper:.6f}). '
        'These small, metric-dependent changes concern a deterministic recoding of the same features. Full K2--K6 and supervised-training-excluded subgroup scores are in the supplement; the task remains conditional on present activity and retrospective cohort membership.\n\n')
    s+=r'''\subsection{Time/Frequency Agreement and Timing Controls}
The reconstruction includes all 2,508,997 cohort addresses, 41,552,909 wallet-day rows and 189,526,795 count incidences. Every annual total reconciles, and all addresses have positive non-DC power. Frequency K3 seed ARI is 0.882--0.934, while time-domain K3 is 0.197--0.639. Annual--time K3 agreement is ARI 0.353/NMI 0.263; annual--frequency agreement is ARI 0.250/NMI 0.116. Time--frequency ARI is 0.251. These overlaps support related but distinct descriptions rather than one common taxonomy.

\begin{figure*}[t]\centering
\includegraphics[width=0.82\textwidth]{figures_current/signal_cross_representation.pdf}
\caption{Annual K3 versus independently fitted time-domain and frequency-domain K3 on the same population. Rows sum to one; numerical labels are arbitrary.}
\label{fig:signaloverlap}\end{figure*}

'''
    s+='Original complete-day timing permutations support all three sample-mean statistics at Holm p=0.003. The extension tests local-order-preserving block nulls (Table~\\ref{tab:blocktimingcompact}); all nine individual tests and K2--K6 signal diagnostics are supplied in the supplement.\n\n'
    rows=[]
    for b in [1,7,30]:
        g=sig[sig.block_days.eq(b)].set_index('metric')
        rows.append([b]+[f'{g.loc[m,"p_holm_9"]:.3f}' for m in ['low_frequency_share','peak_power_share','negative_entropy']])
    s+=tabular('Timing sensitivity: Holm-adjusted p-values across nine tests, 999 permutations per null on the same 2,000-address sample.',
        'tab:blocktimingcompact','rrrr',r'Block days & Low frequency & Peak share & Neg. entropy',rows)
    low=sig[sig.metric.eq('low_frequency_share')].set_index('block_days')
    s+=(f'Observed mean low-frequency share is {low.loc[1,"observed"]:.4f}; null means rise from {low.loc[1,"null_mean"]:.4f} under daily permutation '
        f'to {low.loc[7,"null_mean"]:.4f} and {low.loc[30,"null_mean"]:.4f} under seven- and thirty-day blocks. '
        f'The corresponding excess falls from {low.loc[1,"excess"]:.4f} to {low.loc[30,"excess"]:.4f}, showing that preservation of local episodes explains part of the original effect. ')
    s+='The tests concern sample-mean temporal arrangement conditional on daily-count histograms. Single episodes and long bursts can generate concentrated spectra; neither cross-representation overlap nor timing significance establishes repeated cycles, individual periodicity or independently validated social roles.\n\n'
    return s

def compact(tex,OUT,BASE,tabular,span):
    a=tex.index(r'\section{Methodology}');b=tex.index(r'\section{Discussion}')
    tex=tex[:a]+METHODS+compact_results(OUT,BASE,tabular,span)+tex[b:]
    candidate=json.loads((OUT/'candidate_manifest.json').read_text())
    if candidate['exact_threshold_10_set_match']:
        old='The upstream selection that created the supplied feature universe is not independently reconstructed, so cluster shares do not estimate prevalence across all Ethereum users.'
        new=(f'An independent audit of all {candidate["daily_rows"]:,} merged wallet-day rows finds that the supplied candidate set exactly matches addresses with at least ten annual count incidences, '
             'with no omitted or additional addresses under this rule. This establishes empirical selection equivalence within the supplied daily source, not reconstruction of raw-transfer cleaning or historical producer intent. '
             'The analysis therefore describes an activity-selected population; cluster shares do not estimate prevalence across all Ethereum users.')
        assert old in tex;tex=tex.replace(old,new)
        tex=tex.replace('The cohort is conditional on a supplied feature universe and one year-end code observation, not every Ethereum user or continuous EOA identity.',
            'The cohort is conditional on the observed at-least-ten-count candidate rule and one year-end code observation, not every Ethereum user or continuous EOA identity.')
    # References in the retained discussion point to the compact main tables.
    return tex
