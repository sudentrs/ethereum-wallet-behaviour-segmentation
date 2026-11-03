> Version note: The compiled ten-page checks below describe the earlier pre-signal revision. The current signal-integrated main.tex has not been compiled or page-count verified. See YEAR_END_SIGNAL_VALIDATION.md and framework_validation_completion.json for the latest analysis and audit.

# TCSS manuscript audit — 2026-11-03

The manuscript was reviewed against the completed corrected-cohort results and
the official TCSS author instructions. This is an internal scientific and
presentation audit, not peer-review acceptance or a guarantee of error-free research.

## Corrections made

- Replaced the conference class and conference author blocks with IEEEtran journal
  format on US Letter. Kept the original section structure and ten-page target.
- Reconciled cohort accounting: 2,738,243 candidates, 2,508,997 retained,
  229,246 excluded, no unresolved historical queries. The criterion is empty code
  at block 16,308,189, not continuous EOA status.
- Corrected a measurement overstatement: annual direction flags are derived from
  positive pooled daily incoming/outgoing amounts. Amount magnitudes are omitted,
  but the seven direction features are not independent of amount preprocessing.
  Zero-value events can affect counts without activating those flags.
- Clarified observed-day annual denominators versus calendar-day monthly
  denominators, inclusive span, concentration, and wallet-record incidence rather
  than unique blockchain transactions. Self-transfers create two wallet incidences
  in the source conversion.
- Removed unsupported preregistration implications. These are declared analysis
  families in a retrospective study, not a preregistered experiment.
- Retained competing evidence: K2 has the largest silhouette and monthly kappa;
  K4 has greater mean network excess; K3 has the strongest tested annual seed
  stability. No universal optimum is claimed.
- Kept annual labels distinct from frozen monthly states and stated the
  retrospective cohort selection and activity-conditioned evaluation.
- Rechecked global Holm families: 84 network tests with 9,999 permutations and
  20 monthly return tests with 999 permutations. Binary K2 return degeneracy is
  explained, not interpreted as absent temporal structure.
- Stated that fixed-graph label permutations do not control degree–label
  association, and that network evidence is not independent of count features.
- Limited the social-systems interpretation to observable address participation
  patterns. No human identity, social influence, economic value, causal mechanism,
  ground-truth taxonomy or downstream utility is asserted.
- Reordered the embedded bibliography by first citation, completed the Vinh et al.
  article title, and checked key dataset and related-work records against primary
  publisher sources. No older-cohort Fourier results enter the current claims.
- Marked `docs/PIPELINE.md` as historical and linked the current reproduction guide.

## Validation performed

`python -m scripts.audit_tcss_manuscript` checks the frozen result hashes, cohort
accounting, complete test identifiers, both Holm corrections, network effect and
standardization arithmetic, result summaries, temporal kappa, annual run counts,
K3 profile totals, asset existence, citation ordering and LaTeX cross-references.
Its machine-readable output is
`results_v3/year_end_2022_count_cohort/tcss_manuscript_audit.json`.

The 34 repository tests passed. The final PDF is compiled and all ten rendered
pages are visually checked. References and figures resolve; no overfull boxes
or missing-glyph warnings remain. Underfull line warnings remain in narrow
columns/tables; they do not indicate content overflow.

This audit reuses the completed raw-file validation and provenance manifests.
It does not repeat the RPC scan, re-read every raw TSV byte, or independently
reconstruct the annual source features from raw transfers. A matching feature
hash is not evidence of that stronger reconstruction.

## Remaining issues a TCSS referee can reasonably raise

1. **Population provenance:** the candidate feature universe is supplied. Its
   original upstream selection rule is not independently reconstructed. The paper
   states this boundary. Before submission, document that selection rule if it can
   be recovered; cluster shares cannot estimate prevalence among all Ethereum users.
2. **Semantic and social validation:** no independently labelled actor categories,
   social outcomes or downstream task are available. The paper is a descriptive
   measurement/validation case study, not a validated social-mechanism model.
3. **Alternative baselines:** only MiniBatchKMeans and three annual seeds are
   evaluated. No bootstrap stability, alternative estimator comparison or
   degree-stratified network null has been completed. These would strengthen the
   scientific contribution; they cannot be manufactured through wording.
4. **Dependence and generalization:** correlated annual features, the same source
   interaction system, one year, one graph sample per month and active-only monthly
   evaluation limit independence and generalizability.
5. **Release state:** the corrected manuscript and some replication files remain
   local and unpushed. A supplementary replication archive is supplied separately.
   The public GitHub URL alone must not be presented as a versioned release of all
   the new results until those files are actually published.

These are disclosed research limits, not resolved claims. TCSS novelty and scope
acceptance remain editorial judgments.

## Primary sources used for this audit

- [TCSS author instructions](https://www.ieeesmc.org/publications/transactions-on-computational-social-systems/information-for-authors/)
- [Dataset descriptor](https://www.nature.com/articles/s41597-025-05662-w)
- [2022 source dataset](https://doi.org/10.7910/DVN/5P82QC)
- [Bonifazi et al.](https://doi.org/10.1186/s40537-022-00586-3)
- [Agarwal et al.](https://doi.org/10.1007/s41109-020-00338-3)
- [T-EDGE](https://doi.org/10.3389/fphy.2020.00204)
- [Liang et al.](https://doi.org/10.1371/journal.pone.0202202)
- [Vinh et al.](https://jmlr.org/papers/v11/vinh10a.html)
