# Verified EOA restoration: annual sensitivity pilot in the V3 revision

Completed 2026-10-20. Existing annual cohort and published outputs were not replaced.

## Scope

V3 continues to use the archived annual 33-feature cohort. Its new six-feature monthly count models are separate. This run checks the annual-resolution V3 manifest for feature order and population size and adds 33 positively evidenced historical EOAs to 2,443,868 baseline wallets (expanded n=2,443,901). It does not refit the V3 monthly models or rerun temporal/network inference. The revision manifest does not provide a full annual input-file hash, so remote byte-for-byte data identity was not established.

Original scaling and legacy token representation were frozen. Scaler reconstruction was checked against 64 baseline rows. Pooled token amounts are not interpreted as economic volume.

## Summary

|   k |   archival_agreement |   archival_ari |   paired_changed_min |   paired_changed_max |   paired_ari_min |   paired_ari_max |   seed_changed_min |   seed_changed_max |   max_abs_share_delta_pp |   max_abs_scaled_profile_delta |
|----:|---------------------:|---------------:|---------------------:|---------------------:|-----------------:|-----------------:|-------------------:|-------------------:|-------------------------:|-------------------------------:|
|   4 |             0.971868 |       0.928636 |                   17 |                  106 |         0.999857 |         0.999979 |              12317 |              19202 |               0.00316908 |                    0.00199467  |
|   5 |             1        |       1        |                   29 |                  134 |         0.999854 |         0.999969 |              18180 |              20834 |               0.00199193 |                    0.000726044 |
|   6 |             0.739983 |       0.565784 |                   26 |                  124 |         0.999873 |         0.999976 |              23369 |              26559 |               0.00163276 |                    0.00511503  |

All nine paired comparisons have ARI > 0.99985. Shared-wallet changes are much smaller than the observed warm-start seed variability in these runs. This is evidence of a small annual perturbation for these 33 accounts under the controlled fitted models, not evidence about the whole excluded population.

## Archival reconstruction limitation

Original estimator files were absent. K5 reconstructed archival labels exactly after alignment. K4 agreement was about 97.19%; K6 agreement was about 74.00%. Consequently fixed-model assignments for K4/K6 refer to reconstructed estimators, not the original missing models. Near-invariance within the paired K6 runs cannot be claimed as direct robustness of the archived K6 partition. The pilot environment is recorded separately from the original V3 environment.

Each baseline/expanded pair starts from the same reconstructed reference centers and uses the same random seed, with batch_size=8192, max_iter=200, n_init=1. Dataset length changes MiniBatchKMeans sampling; paired changes include schedule sensitivity. Seed variability here is warm-start variability from common reference centers, not arbitrary-start or population uncertainty.

## Activity

{
  "added_wallet_count": 33,
  "baseline_wallet_count": 2443868,
  "added_wallet_share_of_expanded": 1.3503001962845467e-05,
  "baseline_wallet_transfer_count": 182828087.0,
  "added_wallet_transfer_count": 1646.0,
  "added_wallet_days": 488,
  "added_transfer_count_share_of_expanded": 9.002912015410536e-06
}

Wallet transfer counts are not unique Ethereum transaction counts or economic volume. Fixed reconstructed assignments of the 33 accounts are in fixed_model_added_assignments.csv.

## Validation and next steps

Validated all 9 K/seed pairs, 45 cluster-size rows, 1,485 feature-profile rows, 99 fixed assignment rows, cohort totals, and 33 unique additions per K. ANNUAL_COMPLETE is present. No missing annual pilot stage remains.

Next: address original-model reconstruction limits (especially K6), apply a systematic population-wide EOA/delegation rule, and evaluate separate monthly/network sensitivities before making downstream or final-cohort claims. No data was pushed by this run.
