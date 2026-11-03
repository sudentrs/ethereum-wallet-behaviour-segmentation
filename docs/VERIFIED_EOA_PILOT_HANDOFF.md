> Historical handoff: the K4-only status below describes the earlier interrupted run. The subsequently completed K4/K5/K6 annual pilot (nine paired fits) is documented in results_v3/eoa_restoration_pilot/README.md. This legacy pilot is separate from the current 2,508,997-address year-end manuscript.

# Verified EOA restoration pilot: handoff

## Status

The pilot was stopped at the user's request to move execution to another computer. K4 completed; K5 and K6 did not. All outputs are exploratory and separate from the existing cohort. No cohort, paper table, or archived cluster label was replaced.

## Completed historical audit

Two disjoint samples contain 4,692 retained EOA-labelled addresses and 120 excluded addresses. All retained addresses had empty code at the 12 observed month-end blocks in 2022. Of the 120 exclusions, 33 had empty code at every observed month end, 50 changed from empty to nonempty code across observations, and 37 had code throughout the observed month ends.

At pinned current-code block 26235924, 31 of the 33 carried exact EIP-7702 delegation indicators; two had empty code. All 33 had original cached code lengths of 23 bytes, but original raw code is unavailable, so the earlier code type for the two currently empty accounts is not established.

All 120 were searched for positive 2022 top-level sender evidence. Each of the 33 has a fetched transaction, receipt and header establishing a successful 2022 transaction with an exact outer sender match and hash inclusion in its block. Code was empty before and after the transaction block. The other 87 had no indexed external match; this is not proof of absence. JSON evidence is local under data/interim/excluded_code_type_audit/origination_evidence/.

## Annual pilot implementation

Script: scripts/run_verified_eoa_restoration_pilot.py

1. Select exactly the 33 positively evidenced addresses from historical_origination_audit.csv; assert uniqueness and exclusion from the baseline.
2. Load all 2,443,868 baseline wallets and the 33 existing scaled features.
3. Extract the restored addresses' raw features from the mixed-population table.
4. Apply the saved EOA-only scaler, using its explicit raw/log1p/signed_log1p transformations; do not refit it. Check reconstruction against 64 existing baseline rows.
5. Reconstruct absent K4/K5/K6 MiniBatchKMeans estimators using seed 492, batch_size 8192, n_init 10 and max_iter 200. Measure agreement with archived labels rather than assuming exact reproduction.
6. Predict the 33 added wallets with these reconstructed fixed estimators.
7. For each K and seeds 492,493,494, fit baseline and expanded datasets from identical initial reference centers, n_init 1 and the same other settings. Hungarian-align labels; measure shared-wallet ARI/NMI/agreement, cluster counts/shares and median profiles.
8. Compare paired changes with baseline seed-to-seed variation. Save models and labels separately, plus cohort activity counts.

Important: because MiniBatchKMeans samples batches using dataset length, the same random seed and initial centers do not force identical batch schedules after 33 rows are added. Paired changes include this algorithmic schedule effect. Three seeds provide a small exploratory comparison, not a full uncertainty analysis.

The legacy token representation is intentionally frozen to isolate this pilot. Do not interpret pooled token amounts as economic volume. No monthly-state sensitivity, temporal-null rerun, or network sensitivity is implemented by this script.

## Required files on the other computer

Preserve the repository-relative layout. These ignored large/local inputs must be copied explicitly; a Git clone alone is insufficient:

```
scripts/run_verified_eoa_restoration_pilot.py
data/interim/excluded_code_type_audit/historical_origination_audit.csv
data/processed/wallet_kmeans6_expanded_daily_features.csv
data/processed/wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled_scaling_stats.csv
results/eoa_only_kmeans6/wallet_eoa_only_kmeans6_features_robust_scaled.csv
results/eoa_only_kmeans4/wallet_eoa_only_kmeans_clusters.csv
results/eoa_only_kmeans5/wallet_eoa_only_kmeans_clusters.csv
results/eoa_only_kmeans6/wallet_eoa_only_kmeans_clusters.csv
```

Copy data/interim/excluded_code_type_audit/ in full if the receiving computer also needs the audit evidence. Do not copy the API key for the annual pilot: it makes no network calls.

For later downstream work, also transfer data/processed/wallet_daily_2022.csv, results_v2/temporal_k4_k5_k6/, the original 2022 monthly transfer TSVs, and relevant scripts and prototypes. The expected raw TSV location is ../dataverse_files or data/raw, but neither location supplied files in this workspace. The raw location is still needed for network analysis; annual features cannot recover counterparties.

## Environment and execution

Use Python 3.12. The environment used for the partial run was:

```
numpy==1.26.4
pandas==2.3.1
scipy==1.13.1
scikit-learn==1.8.0
joblib==1.4.2
threadpoolctl==3.5.0
```

From the repository root:

```powershell
python -m pip install numpy==1.26.4 pandas==2.3.1 scipy==1.13.1 scikit-learn==1.8.0 joblib==1.4.2 threadpoolctl==3.5.0
python -u scripts/run_verified_eoa_restoration_pilot.py
```

The script caps computational thread pools at four. It reads large tables and keeps baseline and expanded matrices in memory. Memory usage was not benchmarked; 16 GB RAM is a reasonable practical starting point rather than a verified requirement.

Outputs: data/interim/verified_eoa_restoration_pilot/. This script starts from scratch, not from partial fit checkpoints. Existing pilot files in this output directory are overwritten as stages complete. Use a clean copy of the project for the receiving run or preserve old exploratory outputs separately. Only ANNUAL_COMPLETE confirms all K values and final annual activity outputs completed; its presence does not mean downstream temporal/network work completed.

## Partial K4 findings: do not present as completed K4/K5/K6 results

The reconstructed K4 estimator did NOT exactly reproduce archived assignments: ARI 0.928636; aligned agreement 97.1868%; 68,752 shared wallets differed. Fixed-estimator predictions therefore refer to a reconstruction, not the original saved estimator, which is unavailable.

Within the controlled K4 pilot:

| Seed | Baseline versus expanded ARI | Changed shared wallets |
|---|---:|---:|
| 492 | 0.9999786 | 17 |
| 493 | 0.9999266 | 54 |
| 494 | 0.9998570 | 106 |

Baseline variation across seeds changed 12,317–19,202 aligned shared-wallet labels (ARI 0.977906–0.984983). The 33-address perturbation was much smaller than this seed variation in these K4 runs. This does not establish robustness for K5/K6, temporal results, network conclusions, or a systematic full-cohort correction.

## Remaining work

- Complete the annual pilot on the other computer and inspect archival reconstruction agreement for every K.
- Treat failed exact archival reproduction as an explicit limitation; avoid calling reconstructed predictions original frozen-model predictions.
- Measure restored monthly activity and temporal contributions with documented scaler/prototype choices, preserving the existing annual-versus-monthly window caveat.
- With original transfer edges, measure network participation and assess network sensitivity.
- Design a population-wide corrected filter rather than restoring only addresses selected for these samples.
- Combine final cohort and token-representation corrections into a separate documented rebuild.
