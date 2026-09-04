# K5 Feature Holdout Validation

## Purpose

This analysis tests whether the Behavior K5 taxonomy is driven by one feature family alone.
For each holdout scenario, one behavioural feature group is removed, KMeans with K=5 is refit on a population-proportional EOA wallet sample, and the resulting labels are aligned back to the reference Behavior K5 labels using Hungarian matching.
The comparison uses ARI, NMI, exact agreement after matching, and per-role recovery rates.

## Summary

| Scenario | Removed features | Retained features | ARI | NMI | Matched agreement | Mean recovery | Min recovery |
|---|---:|---:|---:|---:|---:|---:|---:|
| all_features_resample_baseline | 0 | 33 | 0.4679 | 0.5343 | 0.6469 | 0.6336 | 0.3239 |
| activity_holdout | 8 | 25 | 0.4811 | 0.4820 | 0.6819 | 0.6803 | 0.3622 |
| value_flow_holdout | 15 | 18 | 0.2510 | 0.3403 | 0.4971 | 0.5317 | 0.1750 |
| directionality_holdout | 9 | 24 | 0.4788 | 0.4928 | 0.6939 | 0.6326 | 0.3218 |
| volatility_concentration_holdout | 9 | 24 | 0.3453 | 0.4547 | 0.6009 | 0.5549 | 0.0000 |

## Interpretation

The holdout test is circularity-aware because it does not ask whether the original K5 clusters differ on the same features used to produce them.
Instead, it asks whether a related five-role structure can still be recovered when one major behavioural feature family is removed.
High agreement after a holdout suggests that the reference taxonomy is not dependent on that feature family alone.
Low agreement identifies feature families that carry essential information for reproducing the K5 taxonomy.

The strongest holdout recovery is `directionality_holdout` with matched agreement `0.6939`.
The weakest holdout recovery is `value_flow_holdout` with matched agreement `0.4971`.
This means the paper should report the holdout validation as a robustness diagnostic rather than as proof that all feature groups are interchangeable.

## Paper Wording

To reduce circularity, we performed feature-family holdout validation.
Each major feature family was removed in turn, KMeans with K=5 was refit, and the resulting partition was aligned to the reference Behavior K5 taxonomy.
The results show which parts of the behavioural representation are necessary for recovering the taxonomy and whether the main roles persist when individual feature families are withheld.
