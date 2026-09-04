# K5 Feature Holdout Validation

## Purpose

This analysis tests whether the Behavior K5 taxonomy is driven by one feature family alone.
For each holdout scenario, one behavioural feature group is removed, KMeans with K=5 is refit on the 10,000-wallet population-proportional sample, and the resulting labels are aligned back to the reference Behavior K5 labels using Hungarian matching.
The comparison uses ARI, NMI, exact agreement after matching, and per-role recovery rates.

## Run Parameters

- Run scope: 10,000-wallet population-proportional sample
- Random state: 492
- MiniBatchKMeans batch size: 8192
- MiniBatchKMeans n_init: 2
- MiniBatchKMeans max_iter: 50

## Summary

| Scenario | Removed features | Retained features | ARI | NMI | Matched agreement | Mean recovery | Min recovery |
|---|---:|---:|---:|---:|---:|---:|---:|
| all_features_resample_baseline | 0 | 33 | 0.4854 | 0.5439 | 0.6466 | 0.6610 | 0.1799 |
| activity_holdout | 8 | 25 | 0.3883 | 0.4081 | 0.6442 | 0.6136 | 0.1371 |
| value_flow_holdout | 15 | 18 | 0.1699 | 0.3075 | 0.4340 | 0.4777 | 0.1850 |
| directionality_holdout | 9 | 24 | 0.4219 | 0.4667 | 0.6419 | 0.6542 | 0.1151 |
| volatility_concentration_holdout | 9 | 24 | 0.4173 | 0.4940 | 0.6164 | 0.6534 | 0.2752 |

## Interpretation

The holdout test is circularity-aware because it does not ask whether the original K5 clusters differ on the same features used to produce them.
Instead, it asks whether a related five-role structure can still be recovered when one major behavioural feature family is removed.
High agreement after a holdout suggests that the reference taxonomy is not dependent on that feature family alone.
Low agreement identifies feature families that carry essential information for reproducing the K5 taxonomy.

The strongest holdout recovery is `all_features_resample_baseline` with matched agreement `0.6466`.
The weakest holdout recovery is `value_flow_holdout` with matched agreement `0.4340`.
This means the paper should report the holdout validation as a robustness diagnostic rather than as proof that all feature groups are interchangeable.

## Paper Wording

To reduce circularity, we performed feature-family holdout validation.
Each major feature family was removed in turn, KMeans with K=5 was refit, and the resulting partition was aligned to the reference Behavior K5 taxonomy.
The results show which parts of the behavioural representation are necessary for recovering the taxonomy and whether the main roles persist when individual feature families are withheld.
