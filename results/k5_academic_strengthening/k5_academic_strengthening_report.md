# K5 Academic Strengthening Pack

## Purpose

This pack adds the remaining paper-strengthening analyses for the EOA-only K5 role taxonomy: per-cluster stability, consensus/co-membership stability, wallet trajectory types, centroid drift, and a consolidated role table.

## Consensus And Co-Membership Stability

KMeans was rerun on a stratified wallet sample using multiple random seeds. Candidate clusters were aligned back to the reference K5 labels with Hungarian matching, then ARI, NMI, exact matched agreement, per-cluster recovery, and sampled pair co-membership consensus were computed.

|       |    seed |   ari_vs_reference |   nmi_vs_reference |   exact_label_agreement_after_matching |
|:------|--------:|-------------------:|-------------------:|---------------------------------------:|
| count |   8     |           8        |          8         |                               8        |
| mean  | 454.5   |           0.508474 |          0.601975  |                               0.672485 |
| std   | 247.398 |           0.100407 |          0.0641092 |                               0.118682 |
| min   | 101     |           0.338496 |          0.4964    |                               0.46756  |
| 25%   | 277.75  |           0.476596 |          0.571166  |                               0.6282   |
| 50%   | 454.5   |           0.547728 |          0.6235    |                               0.69082  |
| 75%   | 631.25  |           0.568642 |          0.644495  |                               0.75607  |
| max   | 808     |           0.60872  |          0.666438  |                               0.80112  |

### Pair Co-Membership Consensus

| pair_type                   |   sampled_pairs |   mean_consensus |   median_consensus |   share_consensus_ge_0_8 |   share_consensus_le_0_2 |
|:----------------------------|----------------:|-----------------:|-------------------:|-------------------------:|-------------------------:|
| same_reference_cluster      |           50012 |         0.673556 |              0.75  |                0.351296  |                0.0524674 |
| different_reference_cluster |          199978 |         0.132035 |              0     |                0.0210773 |                0.742602  |
| within_C0                   |           10118 |         0.899857 |              1     |                0.754793  |                0         |
| within_C1                   |           10048 |         0.627986 |              0.625 |                0.272393  |                0.0777269 |
| within_C2                   |            9881 |         0.655488 |              0.75  |                0.303411  |                0.0700334 |
| within_C3                   |           10074 |         0.600978 |              0.625 |                0.225432  |                0.0668056 |
| within_C4                   |            9891 |         0.580326 |              0.625 |                0.194722  |                0.0483268 |

Interpretation: high within-cluster consensus means wallets assigned to the same reference role tend to remain together across reruns. A low different-cluster consensus baseline means the model is not simply putting most wallets together regardless of role.

## Wallet Trajectory Types

| trajectory_type          |   wallet_count |   mean_months_observed |   mean_switch_count |   mean_two_step_return_count |   wallet_share |
|:-------------------------|---------------:|-----------------------:|--------------------:|-----------------------------:|---------------:|
| returner                 |         850818 |                6.77538 |             3.60125 |                       1.5047 |      0.348144  |
| one_time_switcher        |         595839 |                3.63423 |             1       |                       0      |      0.24381   |
| persistent               |         389191 |                3.41688 |             0       |                       0      |      0.159252  |
| multi_step_mover         |         255006 |                5.62891 |             2.18576 |                       0      |      0.104345  |
| insufficient_observation |         197626 |                1       |             0       |                       0      |      0.0808661 |
| volatile_switcher        |         122250 |                6.7274  |             3.71312 |                       0      |      0.0500232 |
| mostly_stable_with_noise |          33138 |                8.33545 |             2.29576 |                       0      |      0.0135597 |

Interpretation: this converts monthly state sequences into readable behavioural patterns. It complements the two-step return test by showing whether wallets are persistent, returners, one-time switchers, or more volatile movers.

## Monthly Centroid Drift

|   cluster |   mean_l2_drift |   max_l2_drift |   min_l2_drift |   mean_l1_abs_drift |   max_drift_month |
|----------:|----------------:|---------------:|---------------:|--------------------:|------------------:|
|         0 |         2.91189 |        3.06223 |        2.8064  |            0.313465 |            202206 |
|         1 |         3.22426 |        3.81569 |        2.83506 |            0.394415 |            202208 |
|         2 |         4.82652 |        5.19468 |        4.54321 |            0.559191 |            202209 |
|         3 |         3.3041  |        3.50848 |        3.05608 |            0.332224 |            202210 |
|         4 |         3.7294  |        3.89973 |        3.56188 |            0.380936 |            202202 |

Interpretation: centroid drift checks whether each monthly state has the same feature meaning as its full-year prototype. Higher drift means the role is more context-sensitive and should be described cautiously.

## Per-Cluster Stability Table

|   cluster | behavior_label                                      |   wallet_count |   wallet_share |   matched_recovery_mean |   matched_recovery_min |   self_transition_probability |   transition_entropy_bits |   mean_l2_drift |   max_l2_drift | dominant_trajectory_type   |   dominant_trajectory_share |   net_external_in_minus_out | role_reliability_summary   | interpretation_caution                                  |
|----------:|:----------------------------------------------------|---------------:|---------------:|------------------------:|-----------------------:|------------------------------:|--------------------------:|----------------:|---------------:|:---------------------------|----------------------------:|----------------------------:|:---------------------------|:--------------------------------------------------------|
|         0 | small-value-flow                                    |         776004 |      0.317531  |                0.8441   |                 0.0918 |                      0.485931 |                   1.52543 |         2.91189 |        3.06223 | one_time_switcher          |                    0.327147 |                      120547 | moderate                   | seed-sensitive in at least one rerun                    |
|         1 | value_scale-leaning                                 |         923286 |      0.377797  |                0.404525 |                 0      |                      0.446783 |                   1.72727 |         3.22426 |        3.81569 | returner                   |                    0.370098 |                      464507 | fragile                    | lower seed/subsample recovery                           |
|         2 | high-transaction, outflow-leaning                   |         154864 |      0.0633684 |                0.765125 |                 0.5612 |                      0.558013 |                   1.54579 |         4.82652 |        5.19468 | returner                   |                    0.365473 |                     -330125 | moderate                   | small role; higher monthly centroid drift               |
|         3 | high-transaction, large-value-flow, bursty-volatile |         183079 |      0.0749136 |                0.6415   |                 0.3296 |                      0.412355 |                   1.98442 |         3.3041  |        3.50848 | one_time_switcher          |                    0.274213 |                     -624611 | fragile                    | small role; seed-sensitive in at least one rerun        |
|         4 | persistent                                          |         406635 |      0.16639   |                0.707175 |                 0.5504 |                      0.284228 |                   2.21002 |         3.7294  |        3.89973 | returner                   |                    0.514519 |                      369682 | fragile                    | low temporal persistence; higher monthly centroid drift |

## Final K5 Role Interpretation Table

|   cluster | behavior_label                                      |   wallet_share | top_high_features                                                                                                                                            | top_low_features                                                                                                                                                    |   self_transition_probability | top_destinations             |   net_external_in_minus_out |   matched_recovery_mean |   mean_l2_drift | dominant_trajectory_type   | role_reliability_summary   | interpretation_caution                                  |
|----------:|:----------------------------------------------------|---------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------:|:-----------------------------|----------------------------:|------------------------:|----------------:|:---------------------------|:---------------------------|:--------------------------------------------------------|
|         0 | small-value-flow                                    |      0.317531  | out_active_day_ratio=0.30; both_active_day_ratio=0.28; both_active_days=0.16; out_active_days=0.15; activity_density=0.01; tx_concentration_ratio=0.00       | total_flow_sum=-0.76; max_daily_total_flow=-0.71; total_in_sum=-0.69; max_daily_total_in=-0.67; avg_daily_total_flow=-0.66; std_daily_total_flow=-0.64              |                      0.485931 | C0=0.486; C2=0.369; C1=0.130 |                      120547 |                0.8441   |         2.91189 | one_time_switcher          | moderate                   | seed-sensitive in at least one rerun                    |
|         1 | value_scale-leaning                                 |      0.377797  | avg_daily_net_flow=0.69; total_net_flow_sum=0.62; in_out_day_balance=0.41; flow_concentration_ratio=0.26; avg_daily_total_out=0.24; std_daily_total_out=0.24 | out_active_day_ratio=-0.41; both_active_day_ratio=-0.29; avg_daily_tx_count=-0.25; activity_density=-0.24; both_active_days=-0.21; out_active_days=-0.18            |                      0.446783 | C1=0.447; C2=0.339; C0=0.170 |                      464507 |                0.404525 |         3.22426 | returner                   | fragile                    | lower seed/subsample recovery                           |
|         2 | high-transaction, outflow-leaning                   |      0.0633684 | activity_density=5.84; tx_concentration_ratio=1.92; avg_daily_tx_count=1.71; max_daily_tx_count=0.91; out_active_day_ratio=0.70; std_daily_tx_count=0.63     | activity_span_days=-2.43; active_days_observed=-1.17; in_active_days=-0.89; out_active_days=-0.69; std_daily_total_flow=-0.64; std_daily_total_in=-0.62             |                      0.558013 | C2=0.558; C0=0.236; C1=0.186 |                     -330125 |                0.765125 |         4.82652 | returner                   | moderate                   | small role; higher monthly centroid drift               |
|         3 | high-transaction, large-value-flow, bursty-volatile |      0.0749136 | avg_daily_net_flow=1.87; avg_daily_total_out=1.63; total_net_flow_sum=1.60; std_daily_total_out=1.59; max_daily_total_out=1.42; total_out_sum=1.35           | tx_concentration_ratio=-0.21; flow_concentration_ratio=0.01; in_out_day_balance=0.05; in_active_day_ratio=0.06; out_active_day_ratio=0.08; activity_span_days=0.13  |                      0.412355 | C3=0.412; C1=0.278; C2=0.187 |                     -624611 |                0.6415   |         3.3041  | one_time_switcher          | fragile                    | small role; seed-sensitive in at least one rerun        |
|         4 | persistent                                          |      0.16639   | total_tx=1.20; active_days_observed=1.16; out_active_days=1.09; total_flow_cv=1.08; in_active_days=1.02; both_active_days=0.79                               | tx_concentration_ratio=-0.49; in_active_day_ratio=-0.05; in_out_day_balance=-0.05; out_active_day_ratio=0.11; both_active_day_ratio=0.12; avg_daily_total_flow=0.17 |                      0.284228 | C4=0.284; C1=0.282; C0=0.187 |                      369682 |                0.707175 |         3.7294  | returner                   | fragile                    | low temporal persistence; higher monthly centroid drift |

## Paper-Ready Claim

The K5 taxonomy is best described as a behaviour-state taxonomy rather than a transaction-community partition. Its strongest support comes from feature-space separation, seed/subsample recovery, monthly persistence, and structured temporal trajectories. Network evidence should remain calibrated because K5 role-to-role flows are structured, but same-role transaction concentration was not stronger than the shuffled-label null test.