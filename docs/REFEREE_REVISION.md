# Current delivery — 5 November 2026

The current paper is `overleaf/main.tex`, identical to the open editor source in
`output/guncel_makale_2026-11-05/main.tex`. It uses the supplied methodology PNG,
includes the completed additional analyses, and was compiled successfully at
10 pages. `referee_extension/current_manuscript_delivery.json` records its hashes.
The earlier revision receipt remains historical analytical provenance; its old
manuscript hash and uncompiled status do not describe this delivery. Old paper
exports and K5 draft sources were removed; analytical evidence is preserved.

---

# Referee revision — 4 November 2026

The current editable manuscript is `overleaf/main.tex`. The earlier supplied
paper provides the narrative structure: population-level motivation, concrete
behavioural contrasts, the validation problem, and then the framework. Its old
EOA population and K4/K5/K6 conclusions are not reused. The supplied latest PDF
and second text identify the corrected-cohort analysis as the empirical base.

The main paper remains in IEEEtran journal/Letter format. Detailed experimental
settings and extended tables are in `overleaf/supplementary.tex`. The diagram is
now code-native TikZ in `overleaf/figures_current/framework_pipeline.tex` and
contains the current K2–K6 comparison and main annual K3 segmentation.

**No LaTeX compilation, new manuscript PDF, visual layout certification, or
page-count certification is performed, as requested.** TCSS author instructions
describe regular papers as normally about ten Transactions pages, with at most
two overlength pages. Static source checks cannot certify that requirement.

## Completed analysis branches

All new empirical results use the corrected year-end code-free cohort, not the
older 2,443,868-address EOA cohort.

The candidate audit resolves the operational selection rule exactly within the
merged daily source: 83,519,492 rows, 25,417,590 distinct addresses, and precisely
2,738,243 addresses with annual count >=10. The supplied candidate set has no
additional or omitted addresses under that rule. It is an activity-selected
population, not a census; raw-transfer cleaning remains outside that equivalence.

- **Training subset robustness:** 30 independent 100,000-address fits at each
  K2–K6, plus 20 fits using 80% of the non-evaluation population at each K.
  A fixed 50,000-address evaluation set is excluded from every new fit. The
  original scaler is retained; this is conditional robustness, not prospective
  validation. Subset selection also induces input-order variation. Cluster-level
  matched Jaccard and population-level ARI are retained.
- **Estimator/weighting sensitivity:** MiniBatchKMeans, batch k-means,
  diagonal-covariance Gaussian mixtures and equal-family distance weighting at
  K3–K5, three seeds, common training and evaluation samples: 36 comparisons.
- **Transparent baselines:** tied-count terciles and a fixed span/activity rule;
  group shares, agreement with annual K3 and matched network comparisons.
- **Activity-controlled network:** unrestricted and joint log-binned full-month
  in/out event-count label permutations. The strata are approximate activity
  controls, not exact-degree or unique-neighbour-degree controls.
- **Graph sensitivity:** all events, non-self events, unique directed non-self
  pairs, dominant-token exclusion, and top-1%-activity endpoint exclusion.
  Exclusions and deduplication precede uniform edge sampling.
- **Multiplicity accounting:** 216 new tests, each using 9,999 permutations.
  Their own Holm correction is retained, together with a stronger 300-test
  correction combining the original 84 network tests and the extension.
- **Inactivity:** all-cohort transitions including an inactive observation
  category, distinguishing previously observed inactivity from addresses not yet
  observed active during 2022.
- **Participation task:** monthly state vocabulary fitted on Jan–Mar only;
  supervised Jan–May pairs; evaluation Jul–Nov pairs. Constant, K2–K6 state-only,
  two-feature logistic, six-feature logistic, state-augmented logistic and
  six-feature histogram boosting comparisons share evaluation observations.
  Paired wallet-level Poisson bootstrap intervals preserve repeated-wallet
  contributions across months. A subgroup excludes supervised-training wallets.
- **Stronger timing nulls:** complete daily and 7/30-day block permutations on
  the original uniform 2,000-address sample; 999 replicates, three statistics per
  null, one nine-test Holm family. All daily histograms remain fixed.
- **Candidate-universe audit:** full merged-source annual-count threshold
  comparisons quantify empirical selection equivalence and its limits. The
  machine-readable result, rather than an inferred upstream intention, determines
  the final manuscript wording.

## Findings that change the interpretation

K3's original three-seed agreement is much stronger than its worst training-subset
agreement. The 20 larger refits have mean ARI approximately 0.861 and range
0.257–0.986. The conclusion is therefore explicitly conditional on perturbation.

On common non-self event samples, K3's mean unrestricted excess is approximately
8.90 percentage points, but its activity-stratified mean is approximately
−0.88 points, with one supported month. Removing top-1%-activity endpoints
produces approximately +3.04 points and twelve supported months; unique directed
pairs have no supported months. The graph association depends materially on
activity control, repeated transfers and retained endpoint composition. Negative
excess is not interpreted as a significant lower-tail result.

State-only participation improves on constant prevalence but is worse than
activity-feature prediction baselines. Adding K3 indicators to the six-feature
logistic model produces very small, metric-dependent loss changes, not a broad
predictive superiority claim. These are separate early-period monthly states,
not annual full-year labels.

All nine daily/block timing tests remain supported at adjusted p=0.009. Effects
decrease under stronger block nulls. They establish sample-mean ordering beyond
the specified surrogates, not repeated cycles or individual significance.

## Reproduction without PDF compilation

On this checkout DuckDB is installed in `.runtime-packages`; set that directory
on `PYTHONPATH` when needed. Standard requirements include NumPy, pandas,
scikit-learn, SciPy, numba, joblib and threadpoolctl.
`requirements-referee.txt` records the tested dependency versions for Python
3.12.3; install it into an isolated environment when reproducing on a new machine.

```powershell
$env:PYTHONPATH = (Resolve-Path .runtime-packages).Path
$env:LOKY_MAX_CPU_COUNT = '3'
python -m scripts.run_referee_robustness annual
python -m scripts.run_referee_robustness population --replicates 20
python -m scripts.run_referee_robustness participation
python -m scripts.run_referee_robustness spectral
python -m scripts.run_referee_network
python -m scripts.audit_candidate_universe
python -m scripts.publish_referee_revision
python -m scripts.audit_tcss_manuscript
python -m scripts.audit_referee_revision
python -m unittest discover -s tests -v
```

The network script supports disjoint `--months` workers. Completed per-month
checkpoints must all match the same protocol before a completion manifest and
global correction are issued. Raw caches and exact sampled edge arrays are
local, recomputable artifacts. Compact CSV/JSON results are under
`results_v3/year_end_2022_count_cohort/referee_extension/`.

`revision_completion.json` binds the current source, supplementary source,
diagram, stage manifests, source code and additional input-cache hashes.
`revision_audit.json` records arithmetic, family identity and static LaTeX
checks. Prior completion receipts remain historical provenance and do not
certify the revised manuscript hash.

## Remaining scientific boundaries

This does not create independent actor labels, another year of observations,
continuous historical EOA certification, token-price-aware economic features,
or exact-degree/token-stratified graph adjustment. One sample per monthly graph
variant and dependence between addresses remain limitations. Neither software
tests nor these analyses guarantee IEEE acceptance. A public versioned release
must match the final local package before making a versioned public availability
claim.

Official guidance checked: https://www.ieeesmc.org/publications/transactions-on-computational-social-systems/information-for-authors/
