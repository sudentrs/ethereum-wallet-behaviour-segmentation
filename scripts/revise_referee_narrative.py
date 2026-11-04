"""Restore the supplied earlier narrative flow without restoring superseded claims."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

INTRO=r'''\section{Introduction}
Public blockchains such as Ethereum expose transaction histories at a scale that makes detailed behavioural analysis possible. However, transparency does not automatically make an ecosystem understandable. A block explorer can reveal the activity of an individual address, while millions of transfer records still leave a population-level question unanswered: what patterns of participation recur, and how do those patterns change over time? Addresses with similar transfer totals can differ substantially in the duration, concentration, direction and timing of their activity. Summarizing these differences requires more than counting transactions or inspecting individual histories.

Wallet segmentation offers a compact vocabulary for describing a large address population. Prior studies demonstrate the informational value of Ethereum transaction histories for ownership linkage, profiling and behavioural classification \cite{victor2020address,beres2021blockchain,bonifazi2022userspectra}. Our target is observable address-level participation. We ask whether groups discovered without semantic labels provide a defensible description of behaviour, rather than attempting to infer who controls an address. Throughout this paper, ``wallet'' denotes an address-level analytical unit; an address is not assumed to represent one person or one organization.

The difficulty is that a clustering algorithm returns a partition even when its groups are unstable, depend heavily on the representation, or add little beyond simple activity thresholds. An interpretable name and a favourable internal score therefore do not establish a useful taxonomy. General clustering-validation research distinguishes internal separation, stability and substantive interpretation \cite{halkidi2001validation,liu2022stability}. For Ethereum segmentation, these distinctions lead to a concrete research problem: what evidence is needed before a set of unsupervised groups can be used to describe participation in the system?

Behaviour also depends on the observation window. A year-long history can summarize sustained participation or short-span concentration, while monthly observations reveal persistence, inactivity and movement between states. Temporal blockchain analysis motivates examining this evolution explicitly \cite{agarwal2021temporal}. We distinguish annual behavioural roles, independently learned monthly states, and daily time/frequency representations. Their numerical labels need not correspond, and agreement between representations must be measured rather than assumed.

We investigate this problem using the ERC-20 Trading 2022 release and its dataset description \cite{somin2025erc2022,somin2025dataset}. A complete historical code scan retains 2,508,997 addresses from a supplied 2,738,243-address feature universe. Membership requires empty code at the final Ethereum block of 2022. On this fixed year-end code-free cohort, we construct a sixteen-feature count/activity/direction representation and compare annual K2--K6 models. Pooled token amount magnitudes are excluded because they do not share a common economic unit. Annual K3 serves as the main descriptive segmentation, while competing resolutions remain part of the evidence.

The central research question is:
\begin{quote}
To what extent can unsupervised Ethereum address segments provide an interpretable and reproducible account of participation across aggregate features, transaction-network structure and temporal activity?
\end{quote}

The contribution is an auditable validation design that keeps these questions distinct. First, historical membership and feature controls establish what population and measurements the segmentation describes. Second, initialization, resampling, feature-family and algorithm comparisons identify which aspects of the annual partition are reproducible and which depend on modelling choices. Third, network randomization, inactivity-aware monthly evaluation and rebuilt daily signals examine how the descriptions relate to interaction and temporal structure. Simple segmentation and participation baselines assess whether clustering adds information beyond readily available activity measurements.

This design is useful because the evidence can disagree. Greater network alignment need not accompany stronger initialization stability; stable optimization need not imply stability to training subsets; and a significant timing statistic need not establish repeated cycles. The contribution is therefore a measured account of which behavioural descriptions survive which checks, rather than a claim that Ethereum contains a unique number of permanent wallet types.

\section{Motivation}
The practical motivation is to make large-scale participation understandable without requiring verified labels for every address. Individual histories answer questions about a particular wallet, but they do not summarize how a population is composed or how its activity changes. A compact behavioural description could support ecosystem monitoring and the formulation of more specific hypotheses about participation. Applications such as anomaly detection or agent-based simulation are potential downstream uses; they require their own validation.

Consider two addresses with the same annual number of transfers. One may spread its activity over several months, while the other concentrates almost all activity into a short episode. A third may transact more often but only on a few isolated days. Transfer totals alone combine these patterns. Duration, density, concentration and daily ordering can separate them, but adding features also changes the geometry used to form clusters. The resulting segments must therefore be evaluated as measurement-dependent summaries.

A second motivation is the dynamic nature of participation. A low-activity address can become active, stop transacting, or return after an inactive interval. Annual roles describe the accumulated history; monthly states describe behaviour within shorter windows. Restricting evaluation to addresses active in consecutive months answers a persistence question, but omits disengagement and reactivation. Both views are needed to explain what a temporal result represents.

These needs create a validation problem in the absence of ground-truth behavioural classes. Internal metrics describe separation in the chosen feature space, while seed comparisons assess optimization sensitivity. Neither determines whether the same groups appear under different training samples, whether simple rules capture comparable structure, or whether the labels align with interactions after accounting for activity. A useful evaluation must expose these alternatives rather than selecting whichever metric favours one cluster count.

The layered framework assigns a specific question to each analysis. Annual profiles describe the groups; feature holdouts and equal-family weighting examine representation dependence; resampling and alternative estimators examine fitting sensitivity. Network nulls assess label--endpoint alignment, including the extent to which monthly transfer activity accounts for that alignment. Frozen monthly models examine persistence and conditional return, while inactivity-aware transitions and later-period participation baselines make the conditioning and practical limits visible. Daily time/frequency representations ask which aspects of temporal organization overlap with the aggregate roles.

These layers share addresses and source records, so they are complementary views rather than independent replications. Their purpose is to make the segmentation assessable: which findings survive stronger controls, which are captured by simpler descriptions, and which remain specific to a representation or observation window? This turns the study from a catalogue of clusters into a reproducible examination of the evidence needed to interpret them.

\section{Related Work}
\subsection{Address Linkage and Behavioural Classification}
Ethereum address analysis includes ownership-linkage heuristics and profiling from transaction histories. Victor investigates address-clustering heuristics \cite{victor2020address}, while B\'{e}res et al. study profiling and deanonymization using graph and behavioural information \cite{beres2021blockchain}. These studies establish that observable histories carry information about addresses and their relationships. Our objective concerns behavioural similarity within a specified population. Similar feature profiles do not establish common ownership, and the resulting segments are not entity-resolution outputs.

Bonifazi et al. represent Ethereum users through multivariate behavioural time series and define user spectra relative to predefined categories \cite{bonifazi2022userspectra}. This perspective motivates treating temporal activity as part of the representation rather than reducing every history to a single total. Our study learns partitions without semantic labels and then compares annual, monthly and signal representations. Consequently, raw-unit profiles, cross-representation agreement and sensitivity analyses must carry the interpretation that externally supplied categories would otherwise provide.

\subsection{Temporal and Network Perspectives}
Temporal graph properties have been used for malicious-account detection \cite{agarwal2021temporal}. T-EDGE represents Ethereum interactions through temporal weighted multidigraph embeddings \cite{tedge2020}, while Liang et al. examine the evolution of cryptocurrency transaction networks \cite{liang2018evolutionary}. These approaches motivate preserving interaction and temporal information when studying blockchain behaviour. Here the network is primarily an evaluation view of activity-derived segments, rather than the input to a graph representation-learning objective.

This distinction creates an important control requirement. Count-based features can correlate with transfer-network activity, so unrestricted label randomization alone does not establish structure beyond activity differences. We therefore compare unrestricted and activity-stratified network nulls and examine sensitivity to repeated pairs, self-transfers, dominant tokens and highly active endpoints. Likewise, temporal organization is evaluated with independently trained monthly models and full-year signal descriptions, whose inferential roles remain separate.

\subsection{Validation of Unsupervised Partitions}
Clustering validation distinguishes geometric compactness, agreement under perturbation and substantive usefulness \cite{halkidi2001validation}. Liu et al. review stability estimation and emphasize the significance of the perturbation being studied \cite{liu2022stability}. We distinguish changes in initialization, training addresses, feature families and estimator geometry. These checks answer different questions and need not support the same resolution.

ARI and NMI compare partitions without relying on arbitrary label numbers \cite{hubert1985partitions,vinh2010information}; Hungarian matching supports address-level agreement and matched cluster comparisons \cite{kuhn1955hungarian}. Silhouette describes internal separation \cite{rousseeuw1987silhouettes}. None supplies ground truth. Our evaluation combines these diagnostics with simple segmentation baselines, declared network randomization families and temporally separated participation comparisons. The intended advance is the controlled assessment of a behavioural segmentation across these views, including explicit reporting when a stronger control weakens its interpretation.

'''

def main():
    p=ROOT/'overleaf/main.tex';s=p.read_text(encoding='utf-8')
    backup=ROOT/'tmp/main_before_referee_revision.tex';backup.parent.mkdir(exist_ok=True)
    if not backup.exists():backup.write_text(s,encoding='utf-8')
    a=s.index(r'\section{Introduction}');b=s.index(r'\section{Methodology}')
    s=s[:a]+INTRO+s[b:]
    s=s.replace('Ethereum Wallet Segmentation Through Cohort-Controlled Layered Validation','Ethereum Wallet Segmentation Through Layered Behavioural Validation')
    p.write_text(s,encoding='utf-8')

if __name__=='__main__':main()
