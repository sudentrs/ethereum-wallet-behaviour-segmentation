# Review revision status

This is a working revision, not a submission-ready certification. Existing
results_v2 outputs are preserved. New experiments write to results_v3.

| Review concern | Implemented change | Remaining acceptance criterion |
|---|---|---|
| Preferred K5 claim | Main manuscript compares K4/K5/K6 without a winner | Integrate all new diagnostics and check every abstract/table/figure |
| Why K4-K6 | Completed common K2-K10 sample sweep with five prespecified seeds | Range retained as exploratory; no optimum inferred |
| Unequal candidate coverage | Full-cohort overlap counts/figures, comparable fifteen-role count-profile figure, K4/K5/K6 holdout table | Full-population signal associations across all three remain incomplete |
| Monthly/annual mismatch | Completed count-only monthly model, common RobustScaler and monthly prototypes trained Jan-Jun, frozen for Jul-Dec | Corrected tables integrated; these state IDs differ from annual IDs |
| Token units | January sample provenance audit and annual count-only sensitivity completed | Fixed-10^18 scaling identified; rebuild token-aware representation and rerun before trusting amount-based roles |
| Independent evaluation | Later-period participation task completed with constant and activity-logistic baselines | States lose to activity logistic in all months; no incremental predictive-utility claim supported |
| Stability | Completed sample seed-pair, 80% subsample, group-distance weighting, full k-means and diagonal GMM comparisons | These are sample sensitivity results, not full-population algorithm reruns |
| Network question | Completed twelve-month activity-conditioned label null, full-mixing tests and endpoint coverage; removed Fisher inference | Conditioning uses binned event counts, not exact unique-neighbour degree; sample scope and testing families documented |
| Historical EOA bias | Block-scoped cache fix; remote audit scripts and transaction evidence for 33 excluded addresses are available | Run the annual restoration pilot and assess population-wide exclusion; sampled evidence is not a full-cohort audit |
| Active-cohort bias | Active/absent denominators exported; persistence explicitly conditional; later participation evaluated | Population-wide absence/re-entry analysis remains optional additional work |
| Signal inference | Completed 500-wallet count-preserving timing-surrogate experiment with 999 replicates; fixed zero-power dominant-frequency handling | TD3 recognized as score-selected; full comparative TD3/TD5 interpretation/enrichment still needed |
| Presentation | Merged motivation into introduction, shortened abstract to 188 words, replaced dense profile figure, integrated generated results | Final journal formatting and full Overleaf render remain; built-in compiler cannot resolve multi-file figures |

## Reproduction

```powershell
python scripts/run_resolution_review.py
python scripts/run_monthly_count_validation.py --data-dir "C:/Users/sudet/Desktop/491-2/dataverse_files" --permutations 999
python scripts/run_spectral_timing_surrogates.py --data-dir "C:/Users/sudet/Desktop/491-2/dataverse_files"
python scripts/run_conditioned_network_review.py --raw-root "C:/Users/sudet/Desktop/491-2/dataverse_files"
python scripts/evaluate_monthly_participation.py
python scripts/package_review_revision.py
python scripts/test_review_revisions.py
```

New monthly states are not annual role IDs. Comparisons of their persistence
are representation sensitivity tests, not a relabelling of the old K5 roles.
Training uses a balanced random sample of active wallet-months from each of
January-June; common preprocessing and centroids are then frozen. Monthly
features normalize count totals and spans by calendar-month length. No token
value enters these features. A missing wallet-month is missing, not inactivity
in a measured behavioural state. Tests use July-December adjacent pairs and
triples only, with Holm correction across the twelve return tests (four triples
at each of three resolutions). The annual EOA universe was defined
retrospectively, which limits a prospective interpretation.

The broad annual sweep and robustness runs use one uniform 20,000-wallet
sample from the complete scaled feature file. They are exploratory diagnostics,
not full-population replications. Original scaling was fitted on annual data;
the sample sweep is not an out-of-time validation.

## Findings That Change The Interpretation

- The broad sample sweep favours K2 on silhouette and K5 on Davies-Bouldin; it does not uniquely justify K4-K6.
- Full-cohort overlap ARIs: K4/K5 0.626; K4/K6 0.517; K5/K6 0.642. Partitions are not assumed to nest.
- Corrected monthly persistence/chance: K4 55.5%/40.7%, K5 46.6%/31.0%, K6 37.0%/23.4%. All twelve held-out return tests have Holm p=0.012.
- State-only participation predictors beat constant prevalence but lose to direct activity logistic in every evaluation month.
- Timing surrogates support concentration beyond daily-count sparsity in the 500-wallet sample (three adjusted p=0.003).
- Unrestricted same-role monthly rejections: K4 12/12, K5 1/12, K6 11/12. Activity-conditioned rejections: K4 2/12, K5 12/12, K6 12/12. Full-mixing mutual information rejects in 12/12 months for every candidate and both nulls, within the declared testing families.
- Only 15.1% of raw transfers have two labelled EOA endpoints and are non-self transfers. The analysis does not cover the entire raw interaction population.
- In January's uniform 2,000-wallet sample, all 3,701 informative matched daily-direction amounts match raw/10^18; 52.9% match token-specific decimal normalization. This identifies a denomination problem, not an economic interpretation.

## Still Required Before Submission

1. Rebuild and compare token-aware annual representations; confirm units in every historical feature table.
2. Complete cohort sensitivity using the historical audits performed on the other computer. The 33-address evidence and annual pilot script are tracked. The original EOA-only scaler was added in commit f6ef25b; the annual restoration pilot has not yet been run here. Broader excluded-cohort sensitivity remains required.
3. Complete full-population cross-resolution signal associations and TD3/TD5 sensitivity.
4. Keep historical secondary docs clearly distinguished from current claims; finalize journal formatting, compile in Overleaf, and review every page.
5. Create a tagged, checked release after the remaining methodological and formatting work. The review revision is being shared on main as a working revision, not a submission-ready paper.
