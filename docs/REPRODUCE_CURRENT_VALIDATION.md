# Reproduce the controlled year-end analyses

Use Python with `pip install -r requirements.txt`. Run commands from the repo
root. All large inputs and intermediate matrices stay local and ignored by Git.
The raw files used here are in `tsv and wallet daily/tsv/` and
`tsv and wallet daily/wallet daily clean/`. Use the paths where your copies live.

## Annual preparation and fits

```powershell
python scripts/filter_year_end_count_features.py --cohort results_v3/year_end_2022_full_cohort/cohort_members.csv.gz --features data/processed/wallet_kmeans6_expanded_daily_features.csv --output data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv --manifest data/interim/year_end_2022_count_cohort/cohort_feature_manifest_reproduced.json
python scripts/scale_year_end_count_features.py --input data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv --matrix-output data/interim/year_end_2022_count_cohort/wallet_count_activity_scaled.npy --stats-output data/interim/year_end_2022_count_cohort/scaling_stats_reproduced.csv --manifest data/interim/year_end_2022_count_cohort/scaling_manifest_reproduced.json
python scripts/fit_year_end_annual_models.py --matrix data/interim/year_end_2022_count_cohort/wallet_count_activity_scaled.npy --wallet-source data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv --out-dir data/interim/year_end_2022_count_cohort/annual_fits_reproduced --k-values 2,3,4,5,6 --seeds 492,493,494 --threads 4
```

These commands refuse to overwrite existing preparation/fit artifacts. Use a
fresh version directory when reproducing them again. The filtered features,
scaling statistics and scaled matrix reproduced the archived hashes exactly.
Thirteen of fifteen annual label arrays matched byte-for-byte; K3 seed494 and
K6 seed493 differed under this runtime. The complete rerun is explicitly
documented in `annual/annual_reproduction_audit.json`. All seed492 reference
labels, and K3 seed493, matched. Numerical inertia reductions can also differ
across runtimes; current annual tables use the full reproduced run.

## Matched-estimator feature holdouts

```powershell
python scripts/run_year_end_k3_feature_holdouts.py --matrix data/interim/year_end_2022_count_cohort/wallet_count_activity_scaled.npy --features data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv --reference-labels data/interim/year_end_2022_count_cohort/annual_fits_reproduced/k3_seed492_labels.npy --out-dir results_v3/year_end_2022_count_cohort/annual/holdouts_matched
```

The holdouts now use MiniBatchKMeans, matching the annual seed492 fit settings:
ten initializations, batch 8192, maximum 200 iterations and four numerical
threads. Original KMeans holdout results are archived as historical evidence,
not used for the updated manuscript.

## Validated monthly states

```powershell
python scripts/run_monthly_count_validation.py --data-dir "tsv and wallet daily/wallet daily clean" --cohort results_v3/year_end_2022_full_cohort/cohort_members.csv.gz --out-dir data/interim/year_end_2022_monthly_k3_validated_ordered --k-values 2,3,4,5,6 --permutations 999 --seed 492 --sample-per-month 20000
```

Every source file is hashed and checked for wallet format, month, finite
nonnegative integer transaction counts and unique wallet-day rows. The cohort
join cache is checked against the supplied membership, and feature signatures
include source contents, cohort membership and preprocessing code. January--June
training uses frozen preprocessing and centroids for July--December. Twenty return
tests across K2--K6 form their own temporal Holm family. Cohort selection is retrospective;
this is not a prospective real-time wallet classifier.
Training rows are sorted by normalized wallet ID before sampling; the previous
DuckDB hash-aggregation row order was not reproducible across thread settings.
For K2 first-step switchers, the starting state is determined by the middle
state. Shuffling within middle-state groups therefore leaves return counts
constant; its p=1 must not be interpreted as negative evidence of temporal structure.

## Shared-sample network comparisons

```powershell
python scripts/run_year_end_network_comparison.py --raw-root "tsv and wallet daily/tsv" --wallet-source data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv --fit-dir data/interim/year_end_2022_count_cohort/annual_fits_reproduced --out-dir results_v3/year_end_2022_count_cohort/network_comparison --sample-edges 200000 --permutations 9999 --seed 492
```

The 84-test network family includes twelve months for five seed492 solutions
(K2--K6) and two additional K3 seeds. All solutions use the same monthly
within-cohort priority sample and common wallet permutations. The sampled graph
and endpoint-wallet label composition are preserved; degree-label association
is not controlled. Repeated transfer rows and self-transfers are retained.
Reports distinguish exact full-eligible-edge ratios from sampled permutation
statistics. The one-sided test looks for above-null same-label concentration;
failure to reject it is not evidence of equivalence.

There are 9,999 permutations because 999 cannot resolve significance for an
84-test Holm family: its smallest possible first adjusted value is 84/1000
= 0.084. This resolution decision was made before interpreting comparison
results. The compiled counter is tested against the reference NumPy statistic
with exactly the same permutations. Numba speeds computation without changing
the statistic or randomization.

Per-month checkpoints make the command resumable. A final network table and
`complete: true` manifest are written only after all 84 tests complete. Raw TSV
content hashes, label hashes and parameters are recorded. Do not compare raw
same-label ratios across K without their null expectations.

## Verification

```powershell
python -m unittest discover -s tests
```

After both completed runs, publish compact tables/figures and synchronize the
manuscript with actual results (the publication step refuses incomplete families):

```powershell
python -m scripts.finalize_year_end_validation --monthly-dir data/interim/year_end_2022_monthly_k3_validated_ordered
python -m scripts.synchronize_manuscript_validation
```

Compile `overleaf/main.tex` from its project directory with an IEEEtran-capable
LaTeX compiler (the Codex editor compiler also supports this project).
Run-generated CSVs, figures, settings, hashes and environment information form
the replication record; raw files and full matrices are intentionally excluded.
