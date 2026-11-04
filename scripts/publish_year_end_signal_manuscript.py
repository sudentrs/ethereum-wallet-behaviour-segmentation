"""Integrate completed corrected-cohort signal evidence into the existing TeX.

Does not compile, open another document, or rerun legacy analyses. Numerical
claims are built from the completed results and frozen in manuscript_inputs.
"""
import hashlib
import json
import re
import shutil
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results_v3/year_end_2022_count_cohort'
SIGNALS=BASE/'signals'


def subsection(s, title, content):
    pattern=r'\\subsection\{'+re.escape(title)+r'\}\n.*?(?=\\subsection\{|\\section\{|\\section\*\{)'
    replacement='\\subsection{'+title+'}\n'+content.strip()+'\n\n'
    result,n=re.subn(pattern,lambda _:replacement,s,flags=re.S)
    assert n==1,(title,n)
    return result


def main():
    if (BASE/'referee_extension/revision_completion.json').exists():
        raise RuntimeError('The referee revision supersedes this publisher. Use scripts.publish_referee_revision; do not overwrite main.tex with the earlier signal-only narrative.')
    manifest=json.loads((SIGNALS/'manifest.json').read_text())
    assert manifest['complete'] and manifest['cohort_size']==2508997
    for name,digest in manifest['outputs'].items():
        assert hashlib.sha256((SIGNALS/name).read_bytes()).hexdigest()==digest
    p=ROOT/'overleaf/main.tex'
    s=p.read_text(encoding='utf-8')
    assert 'Full-Cohort Count Signals and Cross-Representation Checks' not in s,'Already integrated; review the saved source before repeating'
    backup=ROOT/'tmp/pre_signal_integration_main.tex'
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists(): backup.write_text(s,encoding='utf-8')
    dest=ROOT/'overleaf/figures_current'
    dest.mkdir(exist_ok=True)
    for name in ['signal_resolution_validation.pdf','signal_cross_representation.pdf']:
        shutil.copy2(SIGNALS/name,dest/name)
    # Keep the chosen schematic but explicitly distinguish its old numerical label.
    start=s.index('Figure~\\ref{fig:pipeline} places the study')
    end=s.index('\\begin{table}[t]',start)
    s=s[:start]+r'''The schematic in Fig.~\ref{fig:pipeline} organizes data preparation, annual representations, signal analysis and validation. All reported branches now use the same year-end cohort. The diagram's K5 label is inherited from the original design; K2--K6 are compared here, with K3 retained as the annual working resolution.

\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{figures_current/ethereum_methodology.png}
\caption{Overview of the layered Ethereum wallet behaviour framework. (A) ERC-20 transfer records are cleaned and standardized. Historical code at block 16,308,189, the final Ethereum block of 2022, retains 2,508,997 code-free addresses from 2,738,243 candidates; a one-block observation does not establish continuous EOA status. (B) Aggregate wallet features are transformed and robust-scaled before candidate k-means resolutions are compared. The displayed K5 taxonomy belongs to the original design; the present study compares K2--K6 and uses annual K3 as a descriptive working resolution. (C) Daily count signals yield time-domain and frequency-domain features, which are clustered separately on the corrected cohort. (D) Feature-space, transaction-network, held-out monthly-state and cross-representation checks support a bounded joint interpretation of annual roles and temporal activity.}
\label{fig:pipeline}
\end{figure*}

'''+s[end:]
    # Remove repeated motivation while preserving its substance and section structure.
    a=s.index('\\section{Motivation}')
    b=s.index('\\section{Related Work}',a)
    s=s[:a]+r'''\section{Motivation}
Transaction counts alone do not distinguish persistent participation from brief bursts. Duration, concentration, direction and the ordering of daily activity provide complementary descriptions. A useful population summary should expose these differences without equating addresses with people, ownership or intent.

Validation layers address different failure modes. Seed agreement tests optimization sensitivity; feature removal tests representation dependence; network permutations test label--endpoint alignment; frozen monthly models test held-out state structure. Signal comparisons ask whether a separate full-year representation recovers the same groups. These checks share data and are not independent confirmations. In particular, stronger network excess need not accompany greater initialization stability, and spectral concentration need not imply recurring cycles. We report these tensions rather than collapsing them into a universal ranking.

'''+s[b:]
    s=subsection(s,'What Makes the Annual K3 Interpretation Defensible',r'''K3 combines strong annual seed agreement, interpretable duration/concentration profiles and above-null network alignment across three seeds. These properties support a practical vocabulary within the chosen representation. K4 has greater network excess but lower seed stability, and feature removal substantially changes K3. Thus K3 is a working summary, not an estimate of three intrinsic wallet types.''')
    s=subsection(s,'Annual Roles and Monthly States Answer Different Questions',r'''Annual roles, full-year signal clusters and frozen monthly states answer different questions. Cross-representation agreement measures overlap after fitting on the same year; it is descriptive and does not establish external validity. Monthly evaluation separates January--June fitting from July--December assignment, but the population remains retrospectively selected at year-end. Numerical cluster IDs have no common meaning across these models.''')
    s=subsection(s,'Representation and Population Boundaries',r'''Counts represent wallet-record incidence, not comparable economic value or distinct Ethereum transactions. Pooled token amounts are excluded, including from the rebuilt signal branch. Directional day flags retain the preprocessing limitations described in Methodology. The year-end code-free cohort is a subset of a supplied feature universe, not all Ethereum users, and does not establish continuous EOA identity.''')
    s=subsection(s,'Network Dependence and the Meaning of External Evidence',r'''Activity-derived labels can correlate with endpoint degree and application exposure. The fixed-graph wallet-label null breaks those associations, so positive excess establishes alignment under that randomization rather than a causal interaction mechanism. Degree-stratified nulls and token-specific analyses remain complementary checks.''')
    s=subsection(s,'Temporal Conditioning and Statistical Significance',r'''Monthly persistence conditions on activity in both months; returns additionally condition on a first-step switch and activity in all three months. K3 return excess is approximately two percentage points despite corrected significance. The signal null conditions on each sampled wallet's daily-count histogram and tests the ordering of activity. Long bursts and single episodes can generate low-frequency power without repeated cycles. Neither test estimates unconditional future behaviour or permanent roles.''')
    s=subsection(s,'Reproducibility and Remaining Research Directions',r'''Source hashes, membership, row order, preprocessing, models and output hashes are recorded. Daily signal totals are checked against the annual count source for every cohort address. Seed perturbations still cover only a narrow form of uncertainty; additional years, resampling, competing algorithms and externally labelled outcomes remain necessary for broader validation. The computational-social-systems contribution is an auditable measurement framework for address-level participation, not identification of people or social mechanisms.''')
    s=subsection(s,'Reproduction Controls and Scope of Signal Evidence',r'''The rebuilt annual features and scaled matrix reproduce their archived hashes. Thirteen of fifteen annual label arrays also match; K3 seed 494 and K6 seed 493 differ under the rerun runtime. All seed-492 references and K3 seed 493 match. Current tables use the complete rerun. Daily signals are reconstructed anew from all twelve validated sources using the exact same cohort; older-cohort Fourier or flow-magnitude results are not reused.''')
    # The holdout table already gives all values; avoid an identical extra plot.
    s=re.sub(r'\\begin\{figure\}\[t\]\\centering\n\\includegraphics\[width=\\columnwidth\]\{figures_current/matched_feature_holdouts.pdf\}.*?\\end\{figure\}\n','',s,flags=re.S)
    method=r'''\subsection{Full-Cohort Count Signals and Cross-Representation Checks}
For every retained address, the twelve daily files are revalidated for address format, month, unique wallet--day rows and finite nonnegative integer counts. Cohort joins reconstruct 365 calendar-day counts with absent days set to zero. The annual sum must match the supplied count source exactly for each address. No pooled token amount enters this branch.

Six time-domain features describe active-day fraction, longest active/inactive runs divided by 365, active/inactive switches divided by 364, peak-day count share and calendar-day count coefficient of variation. For frequency features, $\log(1+x_t)$ is centred within wallet, transformed by the real discrete Fourier transform, and normalized by total non-DC power. Seven summaries describe power at periods above 60 days, 14--60 days and below 14 days, weekly and monthly bands, peak-power share and spectral entropy. At 365 days, bands use discrete Fourier bins rather than exact calendar cycles. Zero-power signals remain in population accounting but are excluded from both signal partitions to keep comparison populations identical.

Time and frequency representations are robust-scaled separately on the eligible population; only the unbounded count coefficient of variation is log-transformed beforehand. Each uses MiniBatchKMeans K2--K6, seeds 492--494, ten initializations, batch size 8,192 and 200 maximum iterations. Centroids are fitted on the same uniform 100,000-address sample and assign all eligible addresses; silhouette uses a separate fixed 3,000-address sample. Full-population ARI, NMI and matched agreement assess seed sensitivity and comparison with annual K2--K6 labels. These full-year comparisons are descriptive, not held-out prediction or independent ground truth.

A separate uniform sample of 2,000 cohort addresses tests temporal ordering. Zero-power exclusions are counted. For each of 999 replicates, all 365 daily counts, including zeros, are permuted within each wallet, preserving its full count histogram. Three upper-tail tests concern sample-mean low-frequency share, peak-power share and negative entropy, with one three-test Holm correction. This null tests ordering beyond count magnitudes; it does not establish recurring cycles or wallet-specific periodicity.

'''
    s=s.replace('\\section{Results}',method+'\\section{Results}',1)
    s=s.replace('Monthly states & Is held-out state movement structured?',
                'Signals & Does daily ordering add structure? & Full-year descriptive fits; no proven cycles '+r'\\'+'\nMonthly states & Is held-out state movement structured?')
    s=s.replace('These findings are interpreted jointly without treating agreement between layers as proof of identity or causality.',
                'Rebuilt full-year count signals add time/frequency partitions, same-cohort overlap and histogram-preserving timing tests. Findings are interpreted jointly without treating agreement between layers as proof of identity or causality.')
    fit=pd.read_csv(SIGNALS/'signal_model_resolution.csv')
    stable=pd.read_csv(SIGNALS/'signal_seed_stability.csv')
    cross=pd.read_csv(SIGNALS/'cross_representation_agreement.csv').set_index(['left','right'])
    timing=pd.read_csv(SIGNALS/'timing_surrogate_tests.csv')
    n=manifest['positive_power_wallets']; excluded=manifest['zero_power_excluded']
    body='\\subsection{Rebuilt Signal and Cross-Representation Evidence}\n'
    body+=f'The daily reconstruction covers all 2,508,997 cohort addresses and reconciles every annual count total exactly. Of these, {n:,} have positive non-DC power; {excluded:,} constant signals are excluded from the signal partitions. Table~\\ref{{tab:signalresolution}} reports all candidate resolutions rather than selecting a signal taxonomy from one score.\n\n'
    body+=r'''\begin{table}[t]
\centering\footnotesize
\caption{Corrected-cohort signal partitions. Silhouette uses seed 492; ARI ranges cover three full-population seed pairs. Centroids use 100,000 sampled addresses.}
\label{tab:signalresolution}
\begin{tabular}{llrr}
\toprule
Representation & $k$ & Silhouette & Seed ARI range \\
\midrule
'''
    for name in ['time','frequency']:
        for k in range(2,7):
            score=fit[(fit.representation==name)&(fit.k==k)&(fit.seed==492)].iloc[0].silhouette
            st=stable[(stable.representation==name)&(stable.k==k)].ari
            body+=f'{name.capitalize()} & {k} & {score:.3f} & {st.min():.3f}--{st.max():.3f} '+r'\\'+'\n'
    body+=r'\bottomrule\end{tabular}\end{table}'+'\n\n'
    ts=stable[(stable.representation=='time')&(stable.k==3)].ari
    fs=stable[(stable.representation=='frequency')&(stable.k==3)].ari
    body+=f'Frequency K3 has seed ARI {fs.min():.3f}--{fs.max():.3f}, whereas time-domain K3 has {ts.min():.3f}--{ts.max():.3f}. This disagreement limits a common-taxonomy interpretation; the K3 comparisons below illustrate overlap rather than selecting a shared optimum.\n\n'
    t=cross.loc['annual_k3','time_k3']; f=cross.loc['annual_k3','frequency_k3']; tf=cross.loc['time_k3','frequency_k3']
    body+=f'For the K3 illustration, annual--time agreement is ARI {t.ari:.3f} and NMI {t.nmi:.3f}; annual--frequency agreement is ARI {f.ari:.3f} and NMI {f.nmi:.3f}. Time--frequency ARI is {tf.ari:.3f}. Figure~\\ref{{fig:signaloverlap}} shows row-normalized overlap. The 75 comparison records cover every annual--signal K2--K6 combination and every time--frequency combination. Equal cluster counts do not imply equal semantics or independent validation.\n\n'
    body+=r'''\begin{figure*}[t]\centering
\includegraphics[width=0.9\textwidth]{figures_current/signal_cross_representation.pdf}
\caption{Annual K3 versus independently fitted time-domain and frequency-domain K3 clusters on the same positive-power population. Each row sums to one; cluster numbers are arbitrary.}
\label{fig:signaloverlap}\end{figure*}

\begin{table}[t]\centering\footnotesize
\caption{Within-wallet timing surrogates on the corrected-cohort sample; 999 permutations and one three-test Holm family.}
\label{tab:signaltiming}
\begin{tabular}{lrrr}\toprule
Statistic & Observed & Null mean & Adj. $p$ \\
\midrule
'''
    titles={'low_frequency_share':'Low-frequency share','peak_power_share':'Peak-power share','negative_entropy':'Negative entropy'}
    for row in timing.itertuples():
        body+=f'{titles[row.metric]} & {row.observed:.4f} & {row.null_mean:.4f} & {row.p_holm_3:.3f} '+r'\\'+'\n'
    body+=r'\bottomrule\end{tabular}\end{table}'+'\n\n'
    supported=int((timing.p_holm_3<.05).sum())
    body+=f'The timing sample retains {manifest["null_positive_power"]:,} positive-power addresses after {manifest["null_zero_power_excluded"]:,} exclusions. {supported} of the three summaries exceed their respective histogram-preserving nulls after Holm correction (Table~\\ref{{tab:signaltiming}}). Effects concern sample-mean organization of daily activity; they do not establish repeated cycles, individual significance, or a common periodic wallet type.\n\n'
    s=s.replace('\\section{Discussion}',body+'\\section{Discussion}',1)
    s=s.replace('Separate frozen monthly K2--K6 models, trained on January--June and evaluated on July--December, show above-chance persistence.',
                'Rebuilt daily-count spectra and time-domain partitions provide same-cohort cross-representation checks and histogram-preserving timing tests. Frozen monthly K2--K6 models show above-chance held-out persistence.')
    s=s.replace('The study contributes five linked components:','The study contributes six linked components:')
    s=s.replace('and frozen, held-out monthly state models. K3','frozen, held-out monthly state models; and rebuilt time/frequency representations with conditional timing tests. K3')
    s=s.replace('An absent wallet-month is encoded as missing','An absent wallet-month is encoded as missing')
    s=s.replace('The contribution is a transparent description of a bounded population, not an identity-recovery method or universal taxonomy.',
                'The rebuilt time/frequency branch reconciles daily counts across the full cohort and measures cross-representation overlap and timing-null effects. The contribution is a transparent description of a bounded population, not an identity-recovery method or universal taxonomy.')
    s=s.replace('Annual roles, monthly states and network alignment provide distinct evidence.','Annual roles, signal partitions, monthly states and network alignment provide distinct evidence.')
    # Fail rather than silently introduce missing references or assets.
    assert set(re.findall(r'\\ref\{([^}]+)\}',s)) <= set(re.findall(r'\\label\{([^}]+)\}',s))
    for asset in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',s): assert (ROOT/'overleaf'/asset).is_file()
    abstract=s.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
    assert 100<=len(abstract.split())<=250
    p.write_text(s,encoding='utf-8')
    frozen_path=ROOT/'overleaf/manuscript_inputs.json'
    frozen=json.loads(frozen_path.read_text())
    frozen['pipeline']='controlled year-end cohort, annual/monthly/network and rebuilt count-signal branches'
    for path in SIGNALS.iterdir():
        if path.is_file(): frozen['input_sha256'][path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    frozen['signal_branch']=dict(cohort=n+excluded,positive_power=n,zero_power_excluded=excluded,model_fits=30,cross_representation_comparisons=75,timing_holm_family=3)
    frozen['source_of_truth']='overleaf/main.tex; legacy extended_body.tex is historical and must not overwrite this source'
    frozen_path.write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
    print('Updated existing main.tex; no compilation performed.')
    print('Abstract words:',len(abstract.split()),'Source words:',len(s.split()))


if __name__=='__main__': main()
