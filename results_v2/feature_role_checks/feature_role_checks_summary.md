# Feature and Role Checks V2

## Outputs

- `persistence_holdout_summary.csv`: missing temporal-persistence holdout row for Table V.
- `feature_holdout_summary_with_persistence.csv`: previous full holdout table plus the new persistence row.
- `internal_metrics_k4_k5_k6.csv`: K4/K5/K6 silhouette, Davies-Bouldin, seed stability, and size balance for Table III.
- `k5_profile_heatmap.pdf/png`: robust-scaled feature median heatmap for Behaviour K5.
- `k5_raw_role_medians.csv`: raw median features for correcting C2/C4 role descriptions.
- `burstiness_formula_check.md`: formula note for replacing the misleading burstiness wording.

## Persistence Holdout Result

| scenario                     |   sample_wallets |   removed_feature_count |   retained_feature_count |   ari_vs_reference |   nmi_vs_reference |   exact_agreement_after_matching |   mean_cluster_recovery_after_matching |   min_cluster_recovery_after_matching | removed_features                                                                                                                                                                |
|:-----------------------------|-----------------:|------------------------:|-------------------------:|-------------------:|-------------------:|---------------------------------:|---------------------------------------:|--------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| temporal_persistence_holdout |          2443868 |                       9 |                       24 |           0.423956 |           0.410622 |                         0.627132 |                               0.591116 |                              0.186258 | active_days_observed; activity_span_days; activity_density; in_active_days; out_active_days; both_active_days; in_active_day_ratio; out_active_day_ratio; both_active_day_ratio |

## Combined Holdout Table

| scenario                         |   ari_vs_reference |   nmi_vs_reference |   exact_agreement_after_matching |   mean_cluster_recovery_after_matching |   min_cluster_recovery_after_matching |
|:---------------------------------|-------------------:|-------------------:|---------------------------------:|---------------------------------------:|--------------------------------------:|
| all_features_resample_baseline   |           1        |           1        |                         1        |                               1        |                             1         |
| activity_holdout                 |           0.448444 |           0.447758 |                         0.686555 |                               0.646496 |                             0.216203  |
| value_flow_holdout               |           0.239137 |           0.323874 |                         0.481052 |                               0.442874 |                             0.0795995 |
| directionality_holdout           |           0.461569 |           0.491557 |                         0.670766 |                               0.682226 |                             0.103929  |
| volatility_concentration_holdout |           0.503153 |           0.520475 |                         0.653463 |                               0.669072 |                             0.315226  |
| temporal_persistence_holdout     |           0.423956 |           0.410622 |                         0.627132 |                               0.591116 |                             0.186258  |

## Internal Metrics

|   k |   min_cluster_share |   max_cluster_share |   seed_stability_ari |   seed_stability_nmi |   silhouette_mean |   silhouette_std |   davies_bouldin_mean |
|----:|--------------------:|--------------------:|---------------------:|---------------------:|------------------:|-----------------:|----------------------:|
|   4 |           0.0812699 |            0.395621 |             0.58936  |             0.620588 |          0.163333 |       0.00534107 |               1.68596 |
|   5 |           0.0633684 |            0.377797 |             0.712603 |             0.687235 |          0.156608 |       0.00628956 |               1.73913 |
|   6 |           0.0614063 |            0.304972 |             0.484808 |             0.520046 |          0.153641 |       0.0084625  |               1.72131 |

## C2/C4 Wording Check

C2 median active days: `3.00`; median total transactions: `15.00`; median transactions per active day: `5.00`.
C4 median active days: `29.00`; median total transactions: `65.00`; median transactions per active day: `2.29`.

Interpretation: C2 should be described as concentrated high transaction intensity over few active days, not persistent dense activity across the year.
C4 can be described as the most persistent/high-active-day K5 role, but not as continuously active across the full year.

## Burstiness Wording

`tx_burstiness_cv` is a coefficient of variation on active-day transaction counts. It can exceed 1. Use this name/formula in the paper rather than the standard burstiness coefficient.
