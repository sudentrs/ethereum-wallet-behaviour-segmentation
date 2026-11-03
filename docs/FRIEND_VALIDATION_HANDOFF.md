# Prompt for the computer holding the raw monthly data

Work in the `ethereum-wallet-behaviour-segmentation` repository. Complete the
missing validation of the current manuscript, `overleaf/main.tex`, based on
commit `ecb9398` and the year-end 2022 code-free cohort. Inspect local changes
before updating from origin; preserve unrelated work. Some corrections may
already exist in the checkout: inspect before editing or rerunning.

Use only the 2,508,997 addresses in
`results_v3/year_end_2022_full_cohort/cohort_members.csv.gz`. Verify the cohort
hash against `YEAR_END_READY.json`. The definition is empty code at Ethereum
block 16,308,189, not continuous EOA identity. Do not change this definition,
pool token amounts, reuse legacy K4/K5/K6 network results as current evidence,
or make new RPC calls.

1. Locate all twelve `202201.tsv` through `202212.tsv` ERC-20 transfer files
   and all twelve `wallet_daily_clean_202201.csv` through
   `wallet_daily_clean_202212.csv` daily inputs. Locate the corrected annual
   feature CSV, robust-scaled NPY matrix, annual K3 seed-492 labels and model.
   The manifests use `data/interim/year_end_2022_count_cohort/` and the
   reference labels were in `annual_fits_final2/k3_seed492_labels.npy`.
   Check hashes, row order and membership before trusting these files.

2. Correct the feature-family holdouts. The current annual models use
   MiniBatchKMeans, whereas the original holdout script used KMeans.
   Use the same estimator and full-model settings for all three removals:
   seed 492, n_init=10, batch_size=8192, max_iter=200, four numerical threads.
   Preserve the same per-feature transformations and scaler; drop only the
   selected feature columns. First reproduce the full K3 reference and
   report any hash or label mismatch. If it cannot be reproduced, document
   the discrepancy rather than silently swapping the reference. Save old
   results separately and publish the corrected results with estimator,
   parameters, versions, feature lists and input/output hashes.

3. Restore source validation in `run_monthly_count_validation.py` before
   rerunning the frozen monthly K3 analysis: normalized 40-character wallet
   identifiers (optional 0x removed), correct month for every date, finite
   nonnegative integer counts, unique normalized wallet-day rows, and a
   cohort parquet cache that matches the supplied cohort. Zero-count days
   are inactive, not extra active days. Cache signatures must invalidate
   old results after code or membership changes. Use January--June training,
   July--December evaluation, seed 492, 20,000 sampled wallet-months per
   training month, k=3 and 999 permutations. Keep annual and monthly labels
   distinct. State the actual Holm family size (four return tests for K3),
   rather than calling it twelve tests. Record data-validation outcomes.

4. Run the corrected-cohort ANNUAL K3 network null test for all twelve
   months with `scripts/run_monthly_network_null_validation.py`, using
   aligned `--labels-npy`, `--wallet-source`, and `--raw-root`. Use 200,000
   sampled eligible transfer rows per month, 999 permutations and seed 492.
   Normalize wallet identifiers identically in labels and transfers. The
   null shuffles wallet labels over the fixed sampled graph; it is not a
   degree-preserving rewiring null. Keep this null definition explicit.
   Save exact eligible-edge counts/coverage, exact same-cluster ratios,
   sampled observed/null statistics, raw p-values, and Holm-adjusted
   p-values across the twelve months. Validate sample sizes and arguments;
   record input fingerprints, settings and label hashes in a manifest.
   Ensure partial/incomplete runs cannot look like completed evidence.
   If a month is missing or no eligible edges exist, report the failure.

5. Synchronize `overleaf/main.tex`, README and CURRENT_MANUSCRIPT_STATUS
   with verified outputs. The original adjacent-month sample-size range
   has a typo: CSVs show 676,741--786,661, not 571,659--786,661 (use new
   verified bounds if reruns differ). Document log1p transforms of annual
   count/duration features before median/IQR scaling, and the actual
   MiniBatchKMeans algorithm. Update holdout values after the matched
   estimator run. Add a network claim only if the corrected result supports
   it; otherwise report the null/negative result and limitations. Do not
   manufacture a claim or select a favorable subset of months.

6. Add targeted synthetic tests for validation, cache changes and label
   alignment; run them. Regenerate affected figures/tables, compile the
   manuscript, and inspect the PDF for broken references and layout.
   Record command lines and versions for clean-checkout reproduction.

Return a concise report of completed work, new statistics, test and compile
results, and any remaining blockers. Commit only relevant code, manuscript,
manifests and compact results; keep secrets, raw data, full matrices and
large labels out of Git. Push the resulting commit to the repository only
if the human authorizes it. We need the commit and compact artifacts back
on the other computer; local data paths alone are not a handoff.
