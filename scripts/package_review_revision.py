"""Generate manuscript tables directly from completed review experiments."""
from pathlib import Path
import shutil
import hashlib
import importlib.metadata
import json
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
ROW_END = chr(92) * 2


def main():
    out=ROOT/"overleaf"
    source=ROOT/"results_v3"
    environment=dict(python=sys.version,packages={name:importlib.metadata.version(name)
        for name in ["numpy","pandas","scipy","scikit-learn","matplotlib","joblib","threadpoolctl"]})
    (source/"environment.json").write_text(json.dumps(environment,indent=2))
    scripts=[p for p in (ROOT/"scripts").glob("*.py") if p.name in {
        "run_resolution_review.py","run_monthly_count_validation.py","run_spectral_timing_surrogates.py",
        "run_conditioned_network_review.py","audit_token_value_provenance.py","evaluate_monthly_participation.py",
        "package_review_revision.py"}]
    (source/"script_checksums.json").write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in scripts},indent=2))
    sweep=pd.read_csv(source/"resolution_review/sweep_summary.csv")
    overlap=pd.read_csv(source/"resolution_review/cross_resolution_summary.csv")
    pairs=pd.read_csv(source/"monthly_count_validation/heldout_persistence.csv")
    triples=pd.read_csv(source/"monthly_count_validation/heldout_two_step_returns.csv")
    ent=pd.read_csv(source/"monthly_count_validation/heldout_entropy.csv").set_index("k")
    holdouts=pd.read_csv(ROOT/"results_v2/feature_role_checks/feature_holdout_summary_k4_k5_k6.csv")
    rows=[]
    for k,g in pairs.groupby("k"):
        obs=np.average(g.observed,weights=g.n);chance=np.average(g.chance,weights=g.n)
        t=triples[triples.k==k]
        rows.append(dict(k=k,pair_observations=int(g.n.sum()),persistence=obs,chance=chance,kappa=(obs-chance)/(1-chance),
            entropy_reduction=ent.loc[k,"entropy_reduction"],return_observed=np.average(t.observed,weights=t.n_switchers),
            return_null=np.average(t.null_mean,weights=t.n_switchers),significant=int((t.p_holm_all_12_tests<.05).sum())))
    summary=pd.DataFrame(rows)
    summary.to_csv(source/"monthly_count_validation/heldout_summary.csv",index=False)
    text=[r"\subsection{Resolution and Representation Sensitivity}",
        "A uniform 20,000-wallet sample from the complete annual feature file was used for a common exploratory sweep over $k=2$--10. Each candidate was fitted using mini-batch k-means with ten initializations and seeds 492--496. Silhouette used the same 2,000-row evaluation subset for each fit. Reported standard deviations describe variation across fits on this diagnostic sample, not population confidence intervals. The original annual scaler was retained for this sensitivity experiment.",
        r"\begin{table}[t]\centering\caption{Common exploratory sample sweep.}\label{tab:review_sweep}\small",
        r"\begin{tabular}{crr}\toprule $k$ & Silhouette (mean $\pm$ SD) & Mean DB \\\midrule"]
    for r in sweep.itertuples():text.append(f"{r.k} & ${r.silhouette_mean:.3f} \\pm {r.silhouette_sd:.3f}$ & {r.db_mean:.3f} " + ROW_END)
    text.extend([r"\bottomrule\end{tabular}\end{table}",
        "The largest mean silhouette occurs at $k=2$, whereas the smallest mean Davies--Bouldin index occurs at $k=5$. The sweep therefore does not establish $k=4$--6 as the only admissible range. We retain it as an exploratory neighbouring-resolution comparison.",
        "Seed-pair agreement, repeated 80\\% subsampling, a disjoint activity/value/other feature-group weighting check, full k-means, and a diagonal-covariance Gaussian mixture were evaluated on the same diagnostic sample. These comparisons test sensitivity rather than establish that one algorithm is correct.",
        r"\begin{table}[t]\centering\caption{Sample representation sensitivity: ARI against the reference sample fit.}\small",
        r"\begin{tabular}{crrr}\toprule $k$ & Count only & Equal group weight & Full k-means \\\midrule"])
    sensitivities=pd.read_csv(source/"resolution_review/representation_algorithm_sensitivity.csv")
    for k in [4,5,6]:
        s=sensitivities[sensitivities.k==k].set_index("representation")
        text.append(f"{k} & {s.loc['count_only','ari']:.3f} & {s.loc['equal_group_distance_weight','ari']:.3f} & {s.loc['full_kmeans','ari']:.3f} " + ROW_END)
    text.extend([r"\bottomrule\end{tabular}\end{table}",
        "Full-cohort overlap compares all 2,443,868 annual EOAs. The ARIs for K4/K5, K4/K6, and K5/K6 are respectively "+", ".join(f"{r.ari:.3f}" for r in overlap.itertuples())+". For example, K4 role 0 distributes 37.7\\% and 62.2\\% of its wallets into K5 roles 3 and 4; K5 role 1 distributes 53.8\\% and 43.5\\% into K6 roles 0 and 5. Cluster numbers are local identifiers and the partitions are not assumed to form a hierarchy.",
        r"\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{figures/review_k4_k5_overlap.pdf}\caption{Full-cohort K4/K5 overlap. Each row sums to one; identifiers are local to each partition.}\label{fig:review_overlap}\end{figure}",
        r"\begin{table}[t]\centering\caption{Comparable full-cohort feature holdouts: ARI.}\small",
        r"\begin{tabular}{lrrr}\toprule Removed family & K4 & K5 & K6 \\\midrule"])
    for scenario,name in [("activity_holdout","Activity"),("value_flow_holdout","Value flow"),("directionality_holdout","Directionality"),("volatility_concentration_holdout","Volatility"),("temporal_persistence_holdout","Persistence")]:
        h=holdouts[holdouts.scenario==scenario].set_index("k")
        text.append(name+" & "+" & ".join(f"{h.loc[k,'ari_vs_reference']:.3f}" for k in [4,5,6])+r" \\")
    text.extend([r"\bottomrule\end{tabular}\end{table}",
        r"\subsection{Corrected Monthly Count-State Evaluation}",
        "To avoid annual/monthly window mismatch and pooled token denominations, this separate analysis uses six monthly count features: transactions per calendar day, active-day fraction, transactions per active day, calendar-day count coefficient of variation, peak-day transaction share, and active-span fraction. The intensity and coefficient-of-variation features receive log1p transforms. A common RobustScaler and K4/K5/K6 prototypes are fitted on up to 20,000 active wallet-months from each of January--June (seed 492; ten initializations), then frozen. Missing wallet-months remain missing, and monthly state numbers are separate from annual role identifiers.",
        "Evaluation uses July--December only. Persistence is conditional on activity in adjacent months. Return tests use first-step switchers active in each of three consecutive months and shuffle final states within middle-state strata, with 999 permutations. Holm correction covers all twelve held-out return tests across the three resolutions. The annual EOA cohort is retrospectively defined; this is a later-period within-cohort test, not prospective validation on unseen users.",
        r"\begin{table}[t]\centering\caption{Frozen count-state evaluation, July--December.}\label{tab:corrected_temporal}\small",
        r"\begin{tabular}{crrrr}\toprule $k$ & Persistence & Chance & $\kappa$ & Return (null) \\\midrule"])
    for r in summary.itertuples():text.append(f"{r.k} & {100*r.persistence:.1f}\\% & {100*r.chance:.1f}\\% & {r.kappa:.3f} & {100*r.return_observed:.1f}\\% ({100*r.return_null:.1f}\\%) " + ROW_END)
    text.extend([r"\bottomrule\end{tabular}\end{table}",
        "All twelve held-out return tests have raw $p=0.001$ and joint Holm-adjusted $p=0.012$, the resolution supported by 999 null draws with no exceedances. Conditional next-state entropy reductions are 12.1\\%, 10.2\\%, and 9.4\\% for K4, K5, and K6. These results support temporal organization across the three count-state resolutions. They do not establish the correctness of the original value-based annual labels or eliminate stable wallet heterogeneity.",
        r"\subsection{Count-Preserving Timing Surrogates}",
        "A uniform sample of 500 annual EOAs was represented by all 365 daily transaction counts. Each surrogate permutes the daily counts within each wallet, preserving its count distribution, total activity, and active-day count. All 500 observed signals had positive non-DC power. Across 999 surrogate replicates, three upper-tail tests compare sample-mean low-frequency share, peak-power share, and negative spectral entropy. Holm correction covers these three summaries.",
        "Observed low-frequency share was 0.1055 versus a null mean of 0.0330; peak-power share was 0.0449 versus 0.0264; spectral entropy was 6.815 versus 6.969 bits. All three adjusted $p$-values were 0.003. This supports timing organization beyond the preserved daily-count distribution in this wallet sample; it does not establish recurring annual cycles or validate a specific annual partition."])
    prediction_path=source/"participation_task/monthly_prediction_scores.csv"
    if prediction_path.exists():
        scores=pd.read_csv(prediction_path)
        text.extend([r"\subsection{Held-Out Participation Prediction}",
            "We test whether the corrected monthly states summarize subsequent participation. Among wallets active in the current month, the target is activity in the following month. Predictions are trained on January--May pairs (up to 50,000 active wallets per month) and evaluated on all active wallets in July--November pairs. State-only predictors use smoothed training-state participation rates. Baselines are the training prevalence and logistic regression on log-transformed transaction intensity and active-day fraction. Wallets can recur between periods; this tests later time periods within the retrospective cohort, not unseen people.",
            r"\begin{table}[t]\centering\caption{Later-period prediction. Losses are weighted by evaluation pair size; lower is better.}\small",
            r"\begin{tabular}{lrr}\toprule Predictor & Brier loss & Log loss \\\midrule"])
        names={"constant_training_prevalence":"Constant","activity_logistic":"Activity logistic","k4_state_only":"K4 states","k5_state_only":"K5 states","k6_state_only":"K6 states"}
        for name,g in scores.groupby("model"):
            text.append(f"{names[name]} & {np.average(g.brier,weights=g.n):.4f} & {np.average(g.log_loss,weights=g.n):.4f} " + ROW_END)
        text.extend([r"\bottomrule\end{tabular}\end{table}",
            "State-only predictors improve on constant prevalence, but the simple activity logistic baseline has lower Brier and log loss in every evaluation month than any state-only predictor. The task therefore does not demonstrate incremental predictive value of the monthly segmentation over direct activity features. Interpretability and compression require their own evaluation; they cannot be inferred from statistically significant temporal persistence."])
    network_path=source/"conditioned_network/monthly_tests.csv"
    if network_path.exists():
        tests=pd.read_csv(network_path)
        coverage=pd.read_csv(source/"conditioned_network/monthly_coverage.csv")
        retained=coverage.two_labelled_eoa_nonself.sum()/coverage.raw_transfers.sum()
        text.extend([r"\subsection{Activity-Conditioned Network Evaluation}",
            "A separate network analysis streams all twelve monthly raw files for coverage and in/out transfer-event counts. Each month retains a uniform priority sample of 50,000 non-self transfer events with two labelled EOA endpoints. Wallet labels are shuffled either unrestricted among participating EOAs or within joint logarithmic in/out event-count bins fitted using the complete retained monthly graph. The bins condition on activity approximately; they are not exact unique-neighbour degree matching. The full-mixing statistic is mutual information between sender and recipient role, which can detect complementary cross-role organization even when same-role concentration is weak.",
            "For each resolution, null, and metric, 999 Monte Carlo draws produce upper-tail tests with Holm correction over twelve months. This defines separate testing families, not a single joint rejection across every analysis. Marginal draws on sampled endpoints use a multivariate hypergeometric distribution equivalent to restricting full within-stratum label permutations to those endpoints. No independence-calibrated combination across months is used.",
            f"The retained two-labelled-EOA non-self transfers constitute {100*retained:.1f}\\% of all raw transfers (monthly range {100*coverage.coverage_of_raw.min():.1f}--{100*coverage.coverage_of_raw.max():.1f}\\%). Exclusions include contracts and addresses outside the labelled cohort; these causes are not separated by this coverage statistic. The tests describe this retained subgraph and its event sample.",
            r"\begin{table}[t]\centering\caption{Monthly rejections after Holm correction within each candidate/null/metric family. Full mixing uses role mutual information.}\small",
            r"\begin{tabular}{llrrr}\toprule Null & Metric & K4 & K5 & K6 \\\midrule"])
        for null_name,label in [("unrestricted","Unrestricted"),("in_out_activity_bins","Activity bins")]:
            for metric,mlabel in [("same_role_ratio","Same role"),("role_mixing_mutual_information_bits","Full mixing")]:
                g=tests[(tests["null"]==null_name)&(tests.metric==metric)]
                ns=[int((g[g.k==k].p_holm_within_k_null_metric<.05).sum()) for k in [4,5,6]]
                text.append(label+" & "+mlabel+" & "+" & ".join(f"{n}/12" for n in ns)+" "+ROW_END)
        text.extend([r"\bottomrule\end{tabular}\end{table}",
            "Conditioned effects and full-mixing tests address different questions from unrestricted homophily. Significant full mixing is an association between endpoint labels under this null, not evidence of identity, causality, or uniformly positive same-role preference."])
    (out/"review_results.tex").write_text("\n".join(text)+"\n",encoding="utf-8")
    for name in ["k2_k10_diagnostics","k4_k5_overlap","k4_k6_overlap","k5_k6_overlap"]:
        shutil.copyfile(source/f"resolution_review/{name}.pdf",out/f"figures/review_{name}.pdf")
    profiles=pd.read_csv(ROOT/"results_v2/feature_role_checks/raw_role_medians_k4_k5_k6.csv")
    columns=["active_days_observed","activity_span_days","activity_density","total_tx","tx_per_active_day"]
    ranks=profiles[columns].rank(pct=True).to_numpy()
    fig,ax=plt.subplots(figsize=(8,7))
    im=ax.imshow(ranks,cmap="YlGnBu",vmin=0,vmax=1,aspect="auto")
    ax.set_xticks(range(len(columns)),["Active days","Active span\n(days)","Activity\ndensity","Transfers","Transfers per\nactive day"])
    ax.set_yticks(range(len(profiles)),[f"K{r.k}: C{r.cluster}" for r in profiles.itertuples()])
    for i in range(len(profiles)):
        for j,c in enumerate(columns):
            v=profiles.iloc[i][c]
            ax.text(j,i,f"{v:.2f}" if c in ["activity_density","tx_per_active_day"] else f"{v:.0f}",
                    ha="center",va="center",color="white" if ranks[i,j]>.65 else "black",fontsize=9)
    for boundary in [3.5,8.5]:ax.axhline(boundary,color="black",linewidth=1)
    fig.colorbar(im,ax=ax,label="Within-feature percentile among 15 role medians")
    fig.tight_layout();fig.savefig(out/"figures/review_count_profiles.pdf");plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,4.5));ax.axis("off")
    lines=[("Source and scope","2022 ERC-20 transfers; retrospectively classified EOA cohort"),
           ("Annual candidate partitions","K4 / K5 / K6; K2-K10 diagnostic sweep; count-only sensitivity"),
           ("Corrected temporal branch","Monthly count features; train Jan-Jun; freeze; evaluate Jul-Dec"),
           ("Evaluation","Role overlap; holdouts; conditioned network nulls; timing surrogates; prediction baselines")]
    for i,(name,detail) in enumerate(lines):
        y=.91-i*.24
        ax.text(.01,y,name,fontsize=12,fontweight="bold",va="top",transform=ax.transAxes)
        ax.text(.01,y-.085,detail,fontsize=10,va="top",transform=ax.transAxes)
    fig.tight_layout();fig.savefig(out/"figures/ethereum_methodology.png",dpi=180);plt.close(fig)
    print(summary.to_string(index=False))


if __name__=="__main__":main()
