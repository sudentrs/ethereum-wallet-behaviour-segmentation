"""Publish completed referee controls into LaTeX; never invoke a TeX engine."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
from scripts.run_referee_robustness import ROOT,BASE,OUT,sha,holm

METHOD=r'''
\subsection{Resampling, Estimator and Weighting Controls}
The additional controls are retrospective robustness analyses, not a preregistered selection exercise. A fixed uniform evaluation set of 50,000 addresses is excluded from every new training subset. For each K2--K6 resolution, we refit on thirty independent 100,000-address subsets and twenty independent subsets containing 80\% of the remaining population. MiniBatchKMeans settings and optimizer seed 492 remain fixed to isolate training-subset perturbation. ARI compares assignments on the fixed evaluation set with the original full-cohort seed-492 partition; Hungarian-matched cluster Jaccard scores expose instability hidden by aggregate agreement. The original reference saw the evaluation features, and the full-cohort scaler is retained. These are conditional robustness diagnostics, not held-out predictive validation or confidence intervals for a true taxonomy.

On one shared 100,000-address training subset, MiniBatchKMeans, batch k-means and a diagonal-covariance Gaussian mixture are compared for K3--K5 at seeds 492--494, using the same 50,000 evaluation addresses. Batch k-means uses ten initializations and 300 maximum iterations; the mixture uses three initializations and 300 maximum iterations. An equal-family-weight variant divides each robust-scaled coordinate by the square root of its family's column count, giving each of the three families equal total weight under equal per-coordinate variation. Agreement with the annual reference measures dependence on estimator and weighting; it does not rank estimator quality against ground truth.

\subsection{Simple Segmentation and Controlled Network Sensitivities}
Two transparent three-group baselines use the same annual cohort. Transfer-count terciles use empirical one-third and two-thirds cutpoints, assigning tied counts together to the upper interval. A span/activity rule assigns span at most thirty days to one group; among remaining addresses, at least twenty-four observed active days defines another group. These illustrative thresholds are fixed in the extension script without optimizing a network outcome. Group shares are reported because they are not matched to annual K3.

For each month, full eligible transfer records supply non-self incoming and outgoing event counts for every participating address. The main extension compares annual K3, K4 and K5 and both baselines on one common uniform sample of up to 50,000 non-self transfer rows. Labels are randomized among sampled endpoint wallets either unrestrictedly or within joint $\lfloor\log_2(1+d_{\rm in})\rfloor$, $\lfloor\log_2(1+d_{\rm out})\rfloor$ strata. Counts defining strata use the complete eligible non-self monthly graph, not only the sample. Within-stratum label composition is preserved among sampled endpoint wallets. These strata control transfer activity approximately; they do not fix exact degree, unique-neighbour degree or token exposure.

Annual K3 additionally uses four graph variants: all eligible events including self-transfers; unique directed non-self pairs; non-self events after removing the month's most frequent token; and non-self events after removing the top 1\% of participating endpoints ranked by total incoming plus outgoing eligible non-self event count. Token and hub ranks use the full eligible graph. Each variant is uniformly sampled from its own full eligible set; repeated-pair deduplication precedes sampling. Both nulls use 9,999 permutations. The five main partitions and four additional K3 variants give 216 tests across twelve months and two nulls. We retain their 216-test correction and additionally apply Holm jointly to these tests and the original 84 network tests, giving a conservative 300-test family for the extension results. Changed graph populations and baseline group sizes prevent a universal quality ranking from excess alone.

\subsection{Inactivity and Later-Period Participation Baselines}
An explicit inactive observation category is added after assignment to the original frozen monthly K3 model; it is not fitted as a centroid. July--December transitions then include every cohort address. Currently inactive addresses are divided into those observed active earlier in 2022 and those not yet observed active in the supplied year. The latter category does not establish address creation or first-ever Ethereum use.

A separate participation task relearns monthly K2--K6 vocabularies using up to 20,000 active observations per month from January--March only. The scaler and centroids are frozen. Supervised training uses up to 50,000 active addresses per current month in January--May pairs, with next-month activity as the target. Evaluation uses all currently active addresses in July--November and their August--December outcomes. Thus neither test-period features nor outcomes fit the state vocabulary or prediction models.

We compare a constant training prevalence, Laplace-smoothed state-specific activity rates, logistic regression on two activity features, logistic regression on all six monthly features, the latter plus K3 one-hot indicators, and histogram gradient boosting on the six features. Logistic inputs are standardized on supervised training data. Boosting uses 150 maximum iterations, fifteen maximum leaves and L2 regularization of one. State indicators are deterministic functions of count features; any gain would reflect a different functional approximation, not newly measured information.

Brier score and log loss are pooled by evaluation observations; AUC is averaged over evaluation months. Scores are also reported for addresses absent from the supervised training sample, which need not be absent from state-model training. Two hundred paired wallet-level Poisson bootstrap replicates provide descriptive 95\% intervals for loss differences, using the same wallet weight across evaluation months and conditioning on fitted models. This preserves repeated-wallet contributions but does not model network dependence or between-year uncertainty. The task remains conditional on current activity and retrospective year-end membership.

\subsection{Timing Controls Preserving Local Ordering}
The original uniform 2,000-address timing sample is reused for additional 999-replicate nulls. Alongside complete daily permutation, seven-day and thirty-day block permutations preserve ordering within each block. Each wallet receives a random circular origin before blocks are formed; the shorter final block is retained. All variants preserve the complete daily-count histogram, including zeros. The same three sample-mean statistics are tested under each variant, giving one nine-test Holm family. Block shuffles partially preserve local episodes; they are sensitivity controls rather than proofs that a significant residual identifies recurring cycles.
'''

def tabular(caption,label,columns,header,rows,wide=False):
    env='table*' if wide else 'table'
    return ('\\begin{'+env+'}[t]\n\\centering\\footnotesize\n\\caption{'+caption+'}\n\\label{'+label+'}\n'
        '\\begin{tabular}{'+columns+'}\n\\toprule\n'+header+r' \\'+'\n\\midrule\n'+
        '\n'.join(' & '.join(map(str,row))+r' \\' for row in rows)+'\n\\bottomrule\n\\end{tabular}\n\\end{'+env+'}\n')

def span(values,digits=3):return f'{min(values):.{digits}f}--{max(values):.{digits}f}'

def main():
    for stage in ['annual','population','participation','spectral','network','candidate']:
        m=json.loads((OUT/f'{stage}_manifest.json').read_text())
        assert m['complete'],stage
        for name,h in m['outputs'].items():assert sha(OUT/name)==h,(stage,name)
    net=pd.read_csv(OUT/'network_all_tests.csv');old=pd.read_csv(BASE/'network_comparison/network_comparison.csv')
    assert len(net)==216 and len(old)==84
    combined=np.r_[old.p_raw.to_numpy(),net.p.to_numpy()];q=holm(combined)
    net['p_holm_300']=q[84:];net.to_csv(OUT/'network_extension_with_global_correction.csv',index=False)
    old=old.copy();old['p_holm_300']=q[:84];old.to_csv(OUT/'network_original_with_global_correction.csv',index=False)
    summary=net.groupby(['partition','variant','null']).agg(mean_excess=('excess','mean'),min_excess=('excess','min'),max_excess=('excess','max'),
        supported=('p_holm_300',lambda x:int((x<.05).sum())),max_adjusted_p=('p_holm_300','max')).reset_index()
    summary.to_csv(OUT/'network_summary_global300.csv',index=False)
    def network_row(partition,variant,null):return summary[(summary.partition==partition)&(summary.variant==variant)&(summary['null']==null)].iloc[0]
    small=pd.read_csv(OUT/'annual_resampling.csv');pop=pd.read_csv(OUT/'population_resampling.csv');alg=pd.read_csv(OUT/'annual_algorithms.csv')
    pred=pd.read_csv(OUT/'participation_prediction_scores.csv');ci=pd.read_csv(OUT/'participation_prediction_intervals.csv')
    signal=pd.read_csv(OUT/'spectral_block_tests.csv');inactive=pd.read_csv(OUT/'participation_inactivity.csv')
    jac=pd.read_csv(OUT/'population_jaccard.csv');sizes=pd.read_csv(OUT/'network_partition_sizes.csv')
    k3=pop[pop.k.eq(3)];ak3=alg[alg.k.eq(3)];n3=network_row('annual_k3','nonself_events','activity_stratified')
    hub3=network_row('annual_k3','without_top_1pct_hubs','activity_stratified')
    ranges={name:span(ak3[ak3.variant.eq(name)].ari_annual) for name in ['batch_kmeans','diagonal_gmm','equal_family_weight']}
    result='\\subsection{Training-Subset and Estimator Robustness}\n'
    result+=(f'The twenty 80\\% refits give annual K3 mean ARI {k3.ari.mean():.3f}, with a {span(k3.ari)} range against the original reference. '
        'The range is substantially wider than the original three-seed comparison. Strong initialization agreement therefore does not establish invariance to training-address selection. '
        'The smaller 100,000-address refits provide a second, explicitly sample-size-dependent diagnostic (Table~\\ref{tab:resampling}). '
        'All comparisons retain the annual scaling; they do not measure uncertainty from rebuilding the source representation.\n\n')
    rows=[]
    for k in range(2,7):
        a=pop[pop.k.eq(k)];b=small[small.k.eq(k)]
        rows.append([k,f'{a.ari.mean():.3f}',span(a.ari),f'{b.ari_annual.mean():.3f}',span(b.ari_annual)])
    result+=tabular('ARI against annual seed 492 on 50,000 fixed evaluation addresses. Twenty 80\\% refits and thirty 100,000-address refits use a fixed optimizer seed.',
        'tab:resampling','rcccc',r'$k$ & 80\% mean & Range & 100k mean & Range',rows)
    result+='For K3, matched Jaccard ranges across the twenty larger refits are '+', '.join(f'{span(g.jaccard)} for reference cluster {int(c)}' for c,g in jac[jac.k.eq(3)].groupby('reference_cluster'))+'. '
    result+='These cluster-level results make membership changes visible even when a population-level ARI remains relatively high.\n\n'
    result+=(f'On the common sample, batch k-means has K3 agreement {ranges["batch_kmeans"]}, compared with {ranges["diagonal_gmm"]} for the diagonal mixture and '
        f'{ranges["equal_family_weight"]} after equal-family weighting. Table~\\ref{{tab:algorithms}} includes K4 and K5. '
        'The result supports a k-means-based descriptive choice while showing that an alternative probabilistic geometry can produce a substantially different partition.\n\n')
    rows=[]
    for k in [3,4,5]:rows.append([k]+[span(alg[(alg.k==k)&(alg.variant==name)].ari_annual) for name in ['batch_kmeans','diagonal_gmm','equal_family_weight']])
    result+=tabular('Sample-trained estimator and weighting sensitivity: ARI ranges against the annual reference across three seeds.','tab:algorithms','rccc',
        r'$k$ & Batch k-means & Diagonal GMM & Equal families',rows)
    result+='\\subsection{Network Evidence After Activity Controls}\n'
    result+=(f'For K3 on non-self events, activity-stratified mean excess is {100*n3.mean_excess:.2f} percentage points, with '
        f'{int(n3.supported)}/12 supported months under the combined 300-test Holm correction. '
        'Table~\\ref{tab:conditionednetwork} compares all five descriptions on common monthly non-self event samples. '
        'The unrestricted and conditioned effects answer different questions; any attenuation identifies the part of the original alignment accounted for by the declared activity strata. '
        'Remaining effects can still reflect variation within bins and shared token exposure.\n\n')
    rows=[]
    for part,name in [('annual_k3','Annual K3'),('annual_k4','Annual K4'),('annual_k5','Annual K5'),('transfer_terciles','Count terciles'),('span_activity_rule','Span/activity rule')]:
        a=network_row(part,'nonself_events','unrestricted');b=network_row(part,'nonself_events','activity_stratified')
        rows.append([name,f'{100*a.mean_excess:.2f}',f'{100*b.mean_excess:.2f}',f'{int(b.supported)}/12',f'{b.max_adjusted_p:.4f}'])
    result+=tabular('Common non-self event samples: mean excess in percentage points. Support and maximum adjusted p-value refer to the activity-stratified null and combined 300-test family.',
        'tab:conditionednetwork','lrrrr',r'Partition & Unrestr. & Stratified & Support & Max. $p$',rows,True)
    shares=[]
    for part,name in [('transfer_terciles','transfer-count terciles'),('span_activity_rule','span/activity rule')]:
        g=sizes[sizes.partition.eq(part)]
        shares.append(name+' ('+', '.join(f'{v*100:.1f}\\%' for v in g.share)+')')
    result+='The baseline group shares are '+ '; '.join(shares)+'. '
    agreement=pd.read_csv(OUT/'network_baseline_agreement.csv').set_index('partition')
    result+=f'Their full-cohort ARIs with annual K3 are {agreement.loc["transfer_terciles","ari_annual_k3"]:.3f} and {agreement.loc["span_activity_rule","ari_annual_k3"]:.3f}, respectively. '
    result+='These comparisons test whether simple descriptions also align with the graph; neither excess nor statistical support alone establishes that clustering is superior.\n\n'
    rows=[]
    for variant,name in [('all_events','All transfer events'),('nonself_events','Non-self events'),('unique_pairs','Unique directed pairs'),('without_top_token','Without top token'),('without_top_1pct_hubs','Without top 1\\% endpoints')]:
        a=network_row('annual_k3',variant,'activity_stratified')
        rows.append([name,f'{100*a.mean_excess:.2f}',f'{100*a.min_excess:.2f}--{100*a.max_excess:.2f}',f'{int(a.supported)}/12'])
    result+=tabular('Annual K3 network sensitivity under activity-stratified label randomization. Excess is in percentage points; support uses the combined 300-test correction.',
        'tab:graphsensitivity','lrrr',r'Graph variant & Mean & Monthly range & Support',rows,True)
    result+='Each filtered variant has its own eligible edge population and endpoint composition. These results measure robustness to graph construction and exposure concentration, rather than isolating a causal token or hub effect. Exact monthly retained counts and excluded token identifiers accompany the replication tables.\n\n'
    result+='\\subsection{Inactivity and Participation Prediction}\n'
    act=inactive[inactive.group.eq('currently_active')];prior=inactive[inactive.group.eq('previously_seen_inactive')]
    unseen=inactive[inactive.group.eq('not_yet_seen_in_2022')]
    result+=(f'Across the five evaluation pairs, next-month activity among currently active addresses is {span(act.next_activity_rate)}. '
        f'Among currently inactive but previously observed addresses it is {span(prior.next_activity_rate)}, compared with '
        f'{span(unseen.next_activity_rate)} for addresses not yet observed active in 2022. '
        'These are cohort-conditional observed-activity rates, not estimates of Ethereum-wide entry or permanent departure. '
        'The complete four-category transition matrix is retained separately from the active-only state matrix.\n\n')
    pooled=[]
    for model,g in pred[pred.group.eq('all')].groupby('model'):
        pooled.append(dict(model=model,brier=np.average(g.brier,weights=g.n),log_loss=np.average(g.log_loss,weights=g.n),auc=g.auc.mean(),n=g.n.sum()))
    ps=pd.DataFrame(pooled).set_index('model');ps.to_csv(OUT/'participation_pooled_scores.csv')
    names=[('constant','Constant prevalence'),('activity','Two-feature logistic'),('all_count','Six-feature logistic'),('nonlinear_count','Six-feature boosting'),
           ('k3_state_only','K3 state only'),('all_count_plus_k3','Six features + K3')]
    rows=[[name]+[f'{ps.loc[key,c]:.4f}' for c in ['brier','log_loss','auc']] for key,name in names]
    result+=tabular('Later-period next-month participation: pooled Brier/log loss (lower is better), and mean monthly AUC (higher is better). All models use identical evaluation observations.',
        'tab:participationprediction','lrrr',r'Model & Brier & Log loss & AUC',rows)
    result+=(f'K3 state-only predictions have Brier score {ps.loc["k3_state_only","brier"]:.4f}, compared with {ps.loc["constant","brier"]:.4f} for constant prevalence, '
        f'{ps.loc["activity","brier"]:.4f} for two-feature logistic regression and {ps.loc["nonlinear_count","brier"]:.4f} for six-feature boosting. '
        'This task assesses a separately fitted early-period monthly vocabulary, not the predictive validity of full-year annual roles. '
        'A state-only gain over constant prevalence is insufficient evidence of added value over activity baselines.\n\n')
    result+='For adding K3 indicators to six-feature logistic regression, paired wallet-bootstrap loss differences (augmented minus unaugmented) are '
    for j,metric in enumerate(['brier','log_loss']):
        r=ci[(ci.metric==metric)&ci.contrast.eq('all_count_plus_k3 minus all_count')].iloc[0]
        result+=(' and ' if j else '')+f'{r.difference:.6f} for '+('Brier score' if j==0 else 'log loss')+f' (95\\% interval {r.lower:.6f} to {r.upper:.6f})'
    result+='. Their magnitude and direction must be interpreted alongside Table~\\ref{tab:participationprediction}; narrow intervals do not establish a practically important gain. Full K2--K6 scores and the subgroup absent from supervised training are supplied in the replication tables.\n\n'
    result+='\\subsection{Timing Evidence Under Block Nulls}\n'
    rows=[]
    for _,r in signal.iterrows():rows.append([int(r.block_days),{'low_frequency_share':'Low-frequency share','peak_power_share':'Peak-power share','negative_entropy':'Negative entropy'}[r.metric],
        f'{r.observed:.4f}',f'{r.null_mean:.4f}',f'{r.excess:.4f}',f'{r.p_holm_9:.3f}'])
    result+=tabular('Timing sensitivity on the same 2,000-address sample, 999 permutations per null and a nine-test Holm family. Block length one denotes complete daily permutation.',
        'tab:blocktiming','rlrrrr',r'Block days & Statistic & Observed & Null & Excess & Adj. $p$',rows,True)
    supported=signal.groupby('block_days').p_holm_9.apply(lambda a:int((a<.05).sum()))
    result+='The number of supported sample-mean timing statistics is '+', '.join(f'{supported.loc[b]}/3 for the {b}-day null' for b in [1,7,30])+'. '
    result+='The stronger nulls retain within-block ordering, so their effects distinguish some long-range arrangement from short local episodes. They do not establish a common period, wallet-specific significance or a recurring behavioural cycle.\n'

    tex=(ROOT/'overleaf/main.tex').read_text(encoding='utf-8')
    # Idempotent generated insertions make later data updates reviewable.
    for tag in ['REFEREE_METHODS','REFEREE_RESULTS']:
        tex=re.sub('% BEGIN '+tag+r'.*?% END '+tag+'\n?', '',tex,flags=re.S)
    tex=tex.replace(r'\usepackage{booktabs}',r'\usepackage{booktabs}'+'\n'+r'\usepackage{tikz}'+'\n'+r'\usetikzlibrary{arrows.meta}') if r'\usepackage{tikz}' not in tex else tex
    tex=tex.replace(r'\section{Results}','% BEGIN REFEREE_METHODS\n'+METHOD+'\n% END REFEREE_METHODS\n'+r'\section{Results}',1)
    tex=tex.replace(r'\section{Discussion}','% BEGIN REFEREE_RESULTS\n'+result+'\n% END REFEREE_RESULTS\n'+r'\section{Discussion}',1)
    tex=tex.replace("The diagram's K5 label is inherited from the original design; K2--K6 are compared here, with K3 retained as the annual working resolution.",
        'The updated diagram separates annual K2--K6 comparisons and the annual K3 description from monthly state models and full-year signals.')
    tex=tex.replace(r'\includegraphics[width=\textwidth]{figures_current/ethereum_methodology.png}',r'\resizebox{\textwidth}{!}{\input{figures_current/framework_pipeline.tex}}')
    tex=tex.replace('The displayed K5 taxonomy belongs to the original design; the present study compares K2--K6 and uses annual K3 as a descriptive working resolution.',
        'The study compares K2--K6 and uses annual K3 as the main descriptive segmentation, with explicit estimator and training-subset sensitivity controls.')
    tex=tex.replace('Three seeds in one representation','Seeds and training subsets; fixed scaling')
    tex=tex.replace('Separate model; active observations only','Separate model; active-only and inactivity views')
    tex=tex.replace('K3 combines strong annual seed agreement, interpretable duration/concentration profiles and above-null network alignment across three seeds. These properties support a practical vocabulary within the chosen representation. K4 has greater network excess but lower seed stability, and feature removal substantially changes K3. Thus K3 is a working summary, not an estimate of three intrinsic wallet types.',
        'K3 combines strong agreement across the original annual seeds with interpretable duration/concentration profiles. The new resampling results show that this is narrower than training-population invariance, while alternative estimators and weighting expose representation dependence. The activity-controlled graph and simple baselines in Tables~\\ref{tab:conditionednetwork}--\\ref{tab:graphsensitivity} determine how much network alignment survives stronger checks. These findings support a transparent working vocabulary within the chosen representation; they do not identify three intrinsic wallet types.')
    tex=tex.replace('Degree-stratified nulls and token-specific analyses remain complementary checks.',
        'The additional activity-stratified nulls and token/hub exclusions directly examine these sensitivities. Logarithmic event-count bins still permit residual activity differences and do not control all aspects of token exposure or unique-neighbour degree.')
    tex=tex.replace('Seed perturbations still cover only a narrow form of uncertainty; additional years, resampling, competing algorithms and externally labelled outcomes remain necessary for broader validation.',
        'Resampling, competing estimators, simple baselines and later-period participation now extend the original seed checks. Additional years, externally labelled outcomes, alternative cohort definitions and exact-degree or token-stratified controls remain necessary for broader validation. The upstream selection that created the supplied candidate feature universe has not been independently reconstructed.')
    abstract=fr'''Public blockchains expose detailed histories, but a partition of addresses does not by itself explain population behaviour. We evaluate Ethereum wallet segmentation through historical cohort controls, simple baselines and complementary network and temporal views. A complete year-end code scan retains 2,508,997 addresses from a supplied 2,738,243-address universe. Sixteen count/activity/direction features exclude pooled token amount magnitudes. Annual K2--K6 comparisons identify K3 as an interpretable working description, with three-seed ARI 0.908--0.971. However, twenty training-subset refits yield K3 ARI {span(k3.ari)}, while feature and estimator changes reveal substantial sensitivity. Non-self K3 network alignment survives monthly activity stratification in {int(n3.supported)} of twelve months, but in {int(hub3.supported)} months after excluding the most active 1\% of endpoints, under a combined 300-test Holm correction. Graph composition therefore materially affects the interpretation. Frozen monthly models reveal active-only persistence and conditional return, while inactivity-aware transitions expose omitted participation paths. Separately fitted early-period K3 states improve later-month participation prediction over constant prevalence but underperform activity-feature baselines. Daily representations show partial cross-representation agreement, while histogram-preserving daily and block nulls detect sample-mean temporal ordering without establishing repeated cycles. The contribution is an auditable account of the evidence and counterevidence for a bounded behavioural summary, rather than permanent identities or a uniquely validated taxonomy.'''
    assert 100<=len(abstract.split())<=250,len(abstract.split())
    tex=re.sub(r'(\\begin\{abstract\}).*?(\\end\{abstract\})',lambda m:m[1]+'\n'+abstract+'\n'+m[2],tex,count=1,flags=re.S)
    conclusion=r'''\section{Conclusion}
This study treats Ethereum wallet segmentation as a behavioural description requiring explicit validation. A complete historical scan defines 2,508,997 year-end code-free addresses, and a sixteen-feature count/activity/direction representation yields an interpretable annual K3 working summary. Its strong original seed agreement is qualified by training-subset variability, feature dependence and disagreement with alternative estimator geometry. Unrestricted network alignment does not by itself establish structure beyond activity; the stratified null and simple baselines materially narrow that interpretation.

Monthly persistence, inactivity, conditional return and later-period participation describe different aspects of changing activity. Prediction baselines prevent an interpretable state vocabulary from being mistaken for demonstrated predictive superiority. Rebuilt daily signals add cross-representation and block-null timing comparisons without identifying permanent rhythms. The resulting framework makes both support and limitations reproducible. Its empirical contribution concerns observable participation within one defined ERC-20 population and year; broader social, economic and cross-year interpretations require additional evidence.

'''
    tex=re.sub(r'\\section\{Conclusion\}.*?(?=\\section\*\{Code and Data Availability\})',lambda m:conclusion,tex,flags=re.S)
    discussion=r'''\section{Discussion}
\subsection{What the Annual Segmentation Can Summarize}
The K3 profiles distinguish sustained activity, distributed lower activity and short-span concentration within this representation. Those contrasts are useful descriptions, but strong agreement across three optimizer seeds is narrower than stability to training-address selection and induced input order. Resampling, feature removal and estimator comparisons show that the partition is not invariant. Simple rules also capture part of its structure. Accordingly, K3 is retained as an interpretable reference vocabulary rather than a uniquely validated behavioural taxonomy.

\subsection{Why Network Controls Change the Interpretation}
Activity-derived labels can correlate with endpoint activity. Unrestricted permutations break that association, whereas the stratified null retains part of it. The controlled comparison in Table~\ref{tab:conditionednetwork} therefore tests a stronger question than the original positive network result. Loss of support in most months narrows the unrestricted interpretation, while support after hub exclusion shows that the relation depends on the retained interaction population (Table~\ref{tab:graphsensitivity}). Neither result implies that all label--network relationships are absent or isolates a causal hub effect. Negative excess is descriptive under the upper-tail test, not a confirmed lower-tail result. Logarithmic bins, shared token exposure and within-bin heterogeneity still limit adjustment.

\subsection{Temporal Structure and Practical Usefulness}
Annual roles, signal partitions and monthly states have different meanings. Active-only persistence omits inactivity and reactivation, while conditional return further selects first-step switchers. K3 return excess is approximately two percentage points despite corrected significance. In the separate prediction task, state-only rates improve on constant prevalence but do not outperform activity-feature baselines; K3 indicators add only small, metric-dependent changes. The study therefore demonstrates temporal organization without establishing predictive superiority of the segmentation. Block-null timing effects concern arrangement beyond partially preserved local episodes, not recurring cycles or human behavioural mechanisms.

\subsection{Population Scope and Reproducibility}
The cohort is conditional on a supplied feature universe and one year-end code observation, not every Ethereum user or continuous EOA identity. Counts are record incidences, and amount-derived directional flags retain preprocessing limitations. Data shared across validation views prevent interpreting them as independent replications. Address-level resampling and bootstrap intervals do not capture all network dependence, cohort-selection uncertainty or between-year variation. The documented controls improve auditability, but additional years, independent raw-transfer reconstruction and independently labelled outcomes remain necessary for broader social-system interpretation. Reproduction checks establish traceability of measurements and summaries, not semantic ground truth.

'''
    tex=re.sub(r'\\section\{Discussion\}.*?(?=\\section\{Conclusion\})',lambda m:discussion,tex,flags=re.S)
    tex=tex.replace('The accompanying replication record contains cohort membership, compact annual and monthly tables, network summaries, figures, source validation records and provenance manifests.',
        'The local replication package contains cohort membership, compact annual and monthly tables, network summaries, robustness and participation controls, figures, source validation records and provenance manifests. The current manuscript and completion receipt identify the exact local revision; the repository URL alone does not certify that every local result is already present in a public versioned release.')
    availability=r'''\section*{Code and Data Availability}
Project code is maintained at \url{https://github.com/sudentrs/ethereum-wallet-behaviour-segmentation}. This revision is accompanied by a replication package containing analysis scripts, compact comparison tables, source-validation records and provenance manifests; the manuscript completion receipt identifies the exact revision. Cohort membership, raw transfer files and large derived matrices are external artifacts documented by the reproduction instructions and checksums. The underlying ERC-20 Trading 2022 data are available from Harvard Dataverse \cite{somin2025erc2022,somin2025dataset}. Older experiments are retained as historical provenance and are not substituted for corrected-cohort results.

'''
    tex=re.sub(r'\\section\*\{Code and Data Availability\}.*?(?=\\begin\{thebibliography\})',lambda m:availability,tex,flags=re.S)
    # Keep the main narrative compact without losing detailed experimental evidence.
    extra='\\section{Additional Diagnostics}\n'
    candidate=json.loads((OUT/'candidate_manifest.json').read_text())
    extra+='\\subsection{Candidate-Universe Selection Audit}\n'
    extra+=(f'The supplied merged daily source contains {candidate["daily_rows"]:,} rows and {candidate["daily_unique_addresses"]:,} distinct normalized addresses. '
        f'The candidate table contains {candidate["candidate_addresses"]:,} distinct addresses. '
        'Threshold comparisons use annual wallet-record count sums over the complete merged source, not only retained cohort addresses. '
        'Exact set equivalence establishes an empirical operational rule within that source, not the provenance of raw-transfer cleaning or proof of the upstream producer\'s intent.\n\n')
    extra+=tabular('Candidate-universe audit against annual count thresholds in the full supplied merged daily source. Candidate-only and threshold-only columns identify set differences.',
        'tab:suppcandidate','rrrrr',r'Threshold & Threshold addresses & Candidate only & Threshold only & Overlap',
        [[r['threshold'],f'{r["threshold_addresses"]:,}',f'{r["candidate_only"]:,}',f'{r["threshold_only"]:,}',f'{r["overlap"]:,}'] for r in candidate['comparisons']],True)
    extra+='\\subsection{Signal Definitions and Monthly Graph Coverage}\n'
    extra+=r'''Time features divide active days and longest active/inactive runs by 365, and active/inactive switches by 364. Peak share is maximum daily count divided by annual count; coefficient of variation uses population standard deviation across all 365 days divided by the calendar-day mean. Frequency bands use cycles/day: $0<f<1/60$, $1/60\le f<1/14$, $1/14\le f\le 1/2$, $1/8\le f<1/6$, and $1/35\le f<1/25$. Peak power is the largest normalized non-DC bin; entropy is $-\sum_j q_j\log_2 q_j$, with zero terms omitted. These definitions do not equate a broad spectral band with a verified calendar cycle.

'''
    coverage=json.loads((OUT/'network_manifest.json').read_text())['coverage']
    rows=[]
    for c in coverage:
        v=c['variants'];rows.append([c['month']]+[f'{v[name]:,}' for name in ['all_events','nonself_events','unique_pairs','without_top_token','without_top_1pct_hubs']])
    extra+=tabular('Complete eligible monthly graph sizes before sampling. Each null uses up to 50,000 rows from its declared variant. Exact excluded token identifiers and endpoint counts are recorded in the companion manifest.',
        'tab:suppgraphcoverage','rrrrrr',r'Month & All events & Non-self & Unique pairs & Token excluded & Hubs excluded',rows,True)
    sf=pd.read_csv(BASE/'signals/signal_model_resolution.csv');ss=pd.read_csv(BASE/'signals/signal_seed_stability.csv')
    rows=[]
    for rep in ['time','frequency']:
        for k in range(2,7):
            a=sf[(sf.representation==rep)&(sf.k==k)&(sf.seed==492)].iloc[0]
            b=ss[(ss.representation==rep)&(ss.k==k)]
            rows.append([rep.capitalize(),k,f'{a.silhouette:.3f}',span(b.ari)])
    extra+=tabular('Full-cohort signal resolution comparison. Silhouette uses seed 492; ARI ranges use all three seed pairs.',
        'tab:suppsignalresolution','lrrc',r'Representation & $k$ & Silhouette & Seed ARI',rows,True)
    rows=[]
    for (group,model),g in pred.groupby(['group','model']):
        rows.append([group.replace('_',r'\_'),model.replace('_',r'\_'),f'{np.average(g.brier,weights=g.n):.4f}',
            f'{np.average(g.log_loss,weights=g.n):.4f}',f'{g.auc.mean():.4f}',f'{g.n.sum():,}'])
    extra+=tabular('All participation models and the subgroup absent from supervised training. Losses are observation-weighted; AUC is the monthly mean. The subgroup can overlap state-vocabulary training.',
        'tab:suppallprediction','llrrrr',r'Group & Model & Brier & Log loss & AUC & Observations',rows,True)
    matrix=pd.read_csv(OUT/'participation_transition_probabilities.csv',index_col=0)
    rows=[[name]+[f'{v:.4f}' for v in row] for name,row in matrix.iterrows()]
    extra+=tabular('Pooled July--December K3 transitions including inactive observations. Row probabilities sum to one. Inactivity is not a fitted centroid.',
        'tab:suppinactivematrix','lrrrr',r'From / To & State 0 & State 1 & State 2 & Inactive',rows)
    ret=pd.read_csv(BASE/'monthly_k2_k6/heldout_two_step_returns.csv');rows=[]
    for _,r in ret.iterrows():
        rows.append([int(r.k),str(int(r.month_start)),f'{int(r.n_switchers):,}',f'{r.observed:.4f}',f'{r.null_mean:.4f}',f'{r.p_holm_all_tests:.3f}'])
    extra+=tabular('All conditional-return tests. Month is the triple start, denominators include only active first-step switchers, and p-values use the original twenty-test family. Binary K2 is structurally degenerate.',
        'tab:suppreturntests','rrrrrr',r'$k$ & Start month & Switchers & Observed & Null & Adj. $p$',rows,True)
    supplement=(r'\documentclass[journal,letterpaper]{IEEEtran}'+'\n'+r'\usepackage{amsmath,amssymb,booktabs}'+'\n'+
        r'\usepackage[hidelinks]{hyperref}'+'\n'+r'\title{Supplementary Material: Ethereum Wallet Segmentation Through Layered Behavioural Validation}'+'\n'+
        r'\author{Selim Balcisoy, Sena Kahya, and Sude Tiras}'+'\n'+r'\begin{document}\maketitle'+'\n'+
        'This supplement records the detailed retrospective controls and full comparison tables accompanying the main manuscript. '
        'The main text defines the data source, original validation branches and inferential scope. No additional raw population or year is introduced here.\n'+
        r'\section{Extended Methods}'+METHOD+'\n'+r'\section{Full Extension Results}'+result+'\n'+extra+'\n'+r'\end{document}'+'\n')
    (ROOT/'overleaf/supplementary.tex').write_text(supplement,encoding='utf-8')
    from scripts.referee_compact_manuscript import compact
    tex=compact(tex,OUT,BASE,tabular,span)
    # Preserve every bibliography record and order by actual first citation.
    start=tex.index(r'\begin{thebibliography}');end=tex.index(r'\end{thebibliography}')
    bib=tex[start:end];items=dict(re.findall(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|\Z)',bib,flags=re.S))
    cites=list(dict.fromkeys(k for group in re.findall(r'\\cite\{([^}]+)\}',tex[:start]) for k in group.split(',')))
    assert set(cites)==set(items),(set(cites)-set(items),set(items)-set(cites))
    tex=tex[:start]+r'\begin{thebibliography}{99}'+'\n'+''.join(r'\bibitem{'+key+'}'+items[key] for key in cites)+tex[end:]
    (ROOT/'overleaf/main.tex').write_text(tex,encoding='utf-8')
    source_inputs=list((ROOT/'data/interim/year_end_2022_monthly_k3_validated_ordered').glob('monthly_features_*.csv.gz'))
    source_inputs+=[ROOT/'data/interim/year_end_2022_signals/daily_counts.npy',ROOT/'data/processed/wallet_daily_2022.csv',ROOT/'data/processed/wallet_kmeans_clusters.csv']
    source_inputs+=list((ROOT/'data/interim/year_end_2022_count_cohort/annual_fits_reproduced').glob('k*_seed492_labels.npy'))
    receipt=dict(complete=True,manuscript='overleaf/main.tex',manuscript_sha256=sha(ROOT/'overleaf/main.tex'),
        supplementary_sha256=sha(ROOT/'overleaf/supplementary.tex'),pipeline_sha256=sha(ROOT/'overleaf/figures_current/framework_pipeline.tex'),
        latex_compiled=False,page_count_verified=False,network_original_tests=84,network_extension_tests=216,network_combined_family=300,
        annual_subsample_fits=len(small),annual_population_fits=len(pop),algorithm_comparisons=len(alg),
        timing_block_tests=len(signal),participation_months=5,
        inputs={p.name:sha(p) for p in OUT.glob('*_manifest.json')},
        validated_cache_inputs={p.relative_to(ROOT).as_posix():sha(p) for p in source_inputs},
        source_code_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/run_referee_robustness.py',ROOT/'scripts/run_referee_network.py',ROOT/'scripts/referee_compact_manuscript.py',ROOT/'scripts/audit_candidate_universe.py']},
        note='Current receipt supersedes manuscript hash in prior framework completion; original result receipts remain historical provenance. No acceptance or layout certification.')
    (OUT/'revision_completion.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
