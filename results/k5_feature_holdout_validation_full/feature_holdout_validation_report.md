# K5 Feature Holdout Validation

## Purpose

This analysis tests whether the Behavior K5 taxonomy is driven by one feature family alone.
For each holdout scenario, one behavioural feature group is removed, KMeans with K=5 is refit on the full EOA population, and the resulting labels are aligned back to the reference Behavior K5 labels using Hungarian matching.
The comparison uses ARI, NMI, exact agreement after matching, and per-role recovery rates.

## Run Parameters

- Run scope: full EOA population
- Random state: 492
- MiniBatchKMeans batch size: 8192
- MiniBatchKMeans n_init: 10
- MiniBatchKMeans max_iter: 200

## Summary

| Scenario | Removed features | Retained features | ARI | NMI | Matched agreement | Mean recovery | Min recovery |
|---|---:|---:|---:|---:|---:|---:|---:|
| all_features_resample_baseline | 0 | 33 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| activity_holdout | 8 | 25 | 0.4484 | 0.4478 | 0.6866 | 0.6465 | 0.2162 |
| value_flow_holdout | 15 | 18 | 0.2391 | 0.3239 | 0.4811 | 0.4429 | 0.0796 |
| directionality_holdout | 9 | 24 | 0.4616 | 0.4916 | 0.6708 | 0.6822 | 0.1039 |
| volatility_concentration_holdout | 9 | 24 | 0.5032 | 0.5205 | 0.6535 | 0.6691 | 0.3152 |

## Interpretation

The holdout test is circularity-aware because it does not ask whether the original K5 clusters differ on the same features used to produce them.
Instead, it asks whether a related five-role structure can still be recovered when one major behavioural feature family is removed.
High agreement after a holdout suggests that the reference taxonomy is not dependent on that feature family alone.
Low agreement identifies feature families that carry essential information for reproducing the K5 taxonomy.

The strongest holdout recovery is `all_features_resample_baseline` with matched agreement `1.0000`.
The weakest holdout recovery is `value_flow_holdout` with matched agreement `0.4811`.
This means the paper should report the holdout validation as a robustness diagnostic rather than as proof that all feature groups are interchangeable.

## Paper Wording

To reduce circularity, we performed feature-family holdout validation.
Each major feature family was removed in turn, KMeans with K=5 was refit, and the resulting partition was aligned to the reference Behavior K5 taxonomy.
The results show which parts of the behavioural representation are necessary for recovering the taxonomy and whether the main roles persist when individual feature families are withheld.
