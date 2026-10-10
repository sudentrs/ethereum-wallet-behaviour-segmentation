# Feature and Role Checks V2

## Outputs

- `feature_holdout_summary_k4_k5_k6.csv`: comparable feature-family holdout validation for K4, K5, and K6.
- `feature_holdout_cluster_recovery_k4_k5_k6.csv`: per-role recovery rates after Hungarian matching.
- `internal_metrics_k4_k5_k6.csv`: K4/K5/K6 silhouette, Davies-Bouldin, seed stability, and size balance for Table III.
- `k4_profile_heatmap.pdf/png`, `k5_profile_heatmap.pdf/png`, `k6_profile_heatmap.pdf/png`: robust-scaled feature median heatmaps.
- `k4_raw_role_medians.csv`, `k5_raw_role_medians.csv`, `k6_raw_role_medians.csv`: raw medians for role interpretation.
- `raw_role_medians_k4_k5_k6.csv`: combined raw median table.
- `burstiness_formula_check.md`: formula note for replacing misleading burstiness wording.

## Internal Metrics

|   k |   min_cluster_share |   max_cluster_share |   seed_stability_ari |   seed_stability_nmi |   silhouette_mean |   silhouette_std |   davies_bouldin_mean |
|----:|--------------------:|--------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------------:|
|   4 |           0.0812699 |            0.395621 |             0.58936  |             0.620588 |          0.163333 |       0.00534107 |               1.68596 |
|   5 |           0.0633684 |            0.377797 |             0.712603 |             0.687235 |          0.156608 |       0.00628956 |               1.73913 |
|   6 |           0.0614063 |            0.304972 |             0.484808 |             0.520046 |          0.153641 |       0.0084625  |               1.72131 |

## Feature Holdout Comparison

|   k | scenario                         |   ari_vs_reference |   nmi_vs_reference |   exact_agreement_after_matching |   mean_cluster_recovery_after_matching |   min_cluster_recovery_after_matching |
|----:|:---------------------------------|-------------------:|-------------------:|---------------------------------:|---------------------------------------:|--------------------------------------:|
|   4 | all_features_resample_baseline   |           1        |           1        |                         1        |                               1        |                            1          |
|   4 | activity_holdout                 |           0.472606 |           0.425783 |                         0.693072 |                               0.60837  |                            0.237668   |
|   4 | value_flow_holdout               |           0.266245 |           0.35858  |                         0.556533 |                               0.633508 |                            0.24234    |
|   4 | directionality_holdout           |           0.614947 |           0.581996 |                         0.850735 |                               0.821731 |                            0.74371    |
|   4 | volatility_concentration_holdout |           0.507022 |           0.537779 |                         0.802882 |                               0.826433 |                            0.649508   |
|   4 | temporal_persistence_holdout     |           0.496588 |           0.430369 |                         0.745948 |                               0.706745 |                            0.608178   |
|   5 | all_features_resample_baseline   |           1        |           1        |                         1        |                               1        |                            1          |
|   5 | activity_holdout                 |           0.370247 |           0.401116 |                         0.611374 |                               0.613488 |                            0.322677   |
|   5 | value_flow_holdout               |           0.239137 |           0.323874 |                         0.481052 |                               0.442874 |                            0.0795995  |
|   5 | directionality_holdout           |           0.46157  |           0.491557 |                         0.670766 |                               0.682226 |                            0.103929   |
|   5 | volatility_concentration_holdout |           0.503153 |           0.520475 |                         0.653463 |                               0.669072 |                            0.315226   |
|   5 | temporal_persistence_holdout     |           0.412601 |           0.428822 |                         0.643622 |                               0.670433 |                            0.48019    |
|   6 | all_features_resample_baseline   |           1        |           1        |                         1        |                               1        |                            1          |
|   6 | activity_holdout                 |           0.527376 |           0.529022 |                         0.730725 |                               0.731523 |                            0.548521   |
|   6 | value_flow_holdout               |           0.302259 |           0.382036 |                         0.590307 |                               0.527453 |                            0.0765082  |
|   6 | directionality_holdout           |           0.421856 |           0.464694 |                         0.622777 |                               0.605231 |                            0.329652   |
|   6 | volatility_concentration_holdout |           0.607423 |           0.583562 |                         0.742717 |                               0.614765 |                            0.00760519 |
|   6 | temporal_persistence_holdout     |           0.461431 |           0.437342 |                         0.656962 |                               0.616003 |                            0.25972    |

## Temporal Persistence Holdout

|   k | scenario                     |   ari_vs_reference |   nmi_vs_reference |   exact_agreement_after_matching |   mean_cluster_recovery_after_matching |   min_cluster_recovery_after_matching |
|----:|:-----------------------------|-------------------:|-------------------:|---------------------------------:|---------------------------------------:|--------------------------------------:|
|   4 | temporal_persistence_holdout |           0.496588 |           0.430369 |                         0.745948 |                               0.706745 |                              0.608178 |
|   5 | temporal_persistence_holdout |           0.412601 |           0.428822 |                         0.643622 |                               0.670433 |                              0.48019  |
|   6 | temporal_persistence_holdout |           0.461431 |           0.437342 |                         0.656962 |                               0.616003 |                              0.25972  |

## Strongest Holdout Recovery Per K

|   k | scenario                         |   ari_vs_reference |   nmi_vs_reference |   exact_agreement_after_matching |   mean_cluster_recovery_after_matching |   min_cluster_recovery_after_matching |
|----:|:---------------------------------|-------------------:|-------------------:|---------------------------------:|---------------------------------------:|--------------------------------------:|
|   4 | directionality_holdout           |           0.614947 |           0.581996 |                         0.850735 |                               0.821731 |                            0.74371    |
|   5 | directionality_holdout           |           0.46157  |           0.491557 |                         0.670766 |                               0.682226 |                            0.103929   |
|   6 | volatility_concentration_holdout |           0.607423 |           0.583562 |                         0.742717 |                               0.614765 |                            0.00760519 |

## Weakest Holdout Recovery Per K

|   k | scenario           |   ari_vs_reference |   nmi_vs_reference |   exact_agreement_after_matching |   mean_cluster_recovery_after_matching |   min_cluster_recovery_after_matching |
|----:|:-------------------|-------------------:|-------------------:|---------------------------------:|---------------------------------------:|--------------------------------------:|
|   4 | value_flow_holdout |           0.266245 |           0.35858  |                         0.556533 |                               0.633508 |                             0.24234   |
|   5 | value_flow_holdout |           0.239137 |           0.323874 |                         0.481052 |                               0.442874 |                             0.0795995 |
|   6 | value_flow_holdout |           0.302259 |           0.382036 |                         0.590307 |                               0.527453 |                             0.0765082 |

## Role-Wording Notes

Use the raw median tables to describe each role cautiously.
For K5, C2 remains a concentrated high-intensity role over few active days rather than a persistent dense role.
For K5, C4 remains the most persistent/high-active-day K5 role, but the median active-day count is still far from continuous full-year activity.

## Burstiness Wording

`tx_burstiness_cv` is a coefficient of variation on active-day transaction counts. It can exceed 1. Use this name/formula in the paper rather than the standard burstiness coefficient.
