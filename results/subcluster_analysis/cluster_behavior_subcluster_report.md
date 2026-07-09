# Cluster Behavior and Internal Subcluster Analysis

This analysis studies whether each KMeans6 cluster contains meaningful behavioral subtypes. It uses the robust-scaled expanded daily behavior features.

## Mathematical Setup

Let `C_k` be one main KMeans6 cluster. For wallets `i in C_k`, each wallet has expanded behavior vector `x_i in R^33`. For each main cluster, we fit candidate internal partitions `P_k(r)` for `r = 2,...,8` using MiniBatchKMeans. The preferred internal subcluster count is selected by maximizing silhouette subject to a minimum subcluster share constraint.

Silhouette for wallet `i` is `s(i) = (b(i) - a(i)) / max(a(i), b(i))`, where `a(i)` is mean distance to its own subcluster and `b(i)` is the best alternative-subcluster distance. Larger values imply stronger internal subcluster structure.

For each main cluster and feature, we test `H0: F_0 = F_1 = ... = F_r` across internal subclusters using Kruskal-Wallis. Pairwise internal differences use Mann-Whitney U and Cliff's delta: `delta = P(X_a > X_b) - P(X_a < X_b)`.

## Internal Heterogeneity Summary

|   cluster |   sampled_wallets |   selected_subcluster_k |   selected_silhouette |   selected_davies_bouldin |   selected_calinski_harabasz |   min_subcluster_share | subcluster_sizes          |   globally_significant_features_q05 |
|----------:|------------------:|------------------------:|----------------------:|--------------------------:|-----------------------------:|-----------------------:|:--------------------------|------------------------------------:|
|         0 |             12000 |                       3 |              0.180152 |                  1.7461   |                      2753.6  |               0.240667 | S0=2888; S1=5660; S2=3452 |                                  32 |
|         1 |             12000 |                       2 |              0.216536 |                  1.90615  |                      2653.32 |               0.384667 | S0=7384; S1=4616          |                                  33 |
|         2 |             12000 |                       2 |              0.184814 |                  2.01547  |                      1957.7  |               0.2625   | S0=3150; S1=8850          |                                  31 |
|         3 |             12000 |                       2 |              0.364019 |                  1.24469  |                      5461.27 |               0.228583 | S0=9257; S1=2743          |                                  30 |
|         4 |             12000 |                       2 |              0.243147 |                  1.62366  |                      2935.28 |               0.2195   | S0=2634; S1=9366          |                                  33 |
|         5 |             12000 |                       2 |              0.726391 |                  0.702299 |                      9856.36 |               0.0525   | S0=630; S1=11370          |                                  33 |

## Behavioral Subtypes

|   cluster |   subcluster |   sampled_wallets | behavior_label                                                                     | top_high_features                                                                                                                   | top_low_features                                                                                                                            |   activity_intensity_score |   activity_persistence_score |   value_scale_score |   directionality_score |   temporal_irregularity_score |
|----------:|-------------:|------------------:|:-----------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------|---------------------------:|-----------------------------:|--------------------:|-----------------------:|------------------------------:|
|         0 |            0 |              2888 | temporal_irregularity-leaning                                                      | tx_concentration_ratio=1.48; std_daily_tx_count=1.05; avg_daily_tx_count=0.91; tx_count_cv=0.80; max_daily_tx_count=0.63            | in_active_days=-0.64; active_days_observed=-0.61; out_active_days=-0.40; activity_density=-0.28; activity_span_days=-0.24                   |                  0.186283  |                   -0.354805  |          -0.0168875 |           -0.0839776   |                    0.363291   |
|         0 |            1 |              5660 | activity_intensity-leaning                                                         | out_active_days=0.40; total_tx=0.35; both_active_days=0.29; active_days_observed=0.24; activity_span_days=0.24                      | avg_daily_total_in=-0.19; avg_daily_total_flow=-0.18; std_daily_net_flow=-0.18; max_daily_total_in=-0.16; activity_density=-0.16            |                  0.222762  |                    0.198319  |          -0.0749991 |            0.000193071 |                   -0.00578329 |
|         0 |            2 |              3452 | bursty/volatile                                                                    | std_daily_total_out=1.19; avg_daily_total_out=1.14; max_daily_total_out=1.01; total_out_sum=0.94; std_daily_net_flow=0.75           | avg_daily_net_flow=-1.20; total_net_flow_sum=-1.20; in_active_day_ratio=-0.26; activity_density=-0.09; both_active_day_ratio=-0.07          |                  0.187644  |                    0.193625  |           0.384439  |           -0.0979706   |                    0.456901   |
|         1 |            0 |              7384 | high transaction intensity, persistent activity                                    | total_tx=1.52; in_active_days=1.48; total_flow_cv=1.47; out_active_days=1.45; active_days_observed=1.41                             | tx_concentration_ratio=-0.53; in_active_day_ratio=-0.04; out_active_day_ratio=-0.01; both_active_day_ratio=0.00; in_out_day_balance=0.09    |                  1.05109   |                    0.986168  |           0.423179  |            0.0094415   |                    0.425882   |
|         1 |            1 |              4616 | high transaction intensity, persistent activity, large-value flow, bursty/volatile | total_tx=2.08; avg_daily_net_flow=1.86; max_daily_tx_count=1.71; total_net_flow_sum=1.67; in_active_days=1.63                       | tx_concentration_ratio=-0.47; flow_concentration_ratio=-0.05; in_out_day_balance=-0.02; in_active_day_ratio=0.13; out_active_day_ratio=0.19 |                  1.64836   |                    1.20634   |           1.32489   |            0.157892    |                    0.930949   |
|         2 |            0 |              3150 | activity_intensity-leaning                                                         | both_active_day_ratio=0.70; out_active_day_ratio=0.51; avg_daily_total_out=0.26; std_daily_total_out=0.25; in_active_day_ratio=0.24 | max_daily_tx_count=-0.50; tx_count_cv=-0.50; in_active_days=-0.44; total_tx=-0.37; in_out_day_balance=-0.35                                 |                 -0.296998  |                   -0.146071  |           0.0150645 |            0.272759    |                   -0.126822   |
|         2 |            1 |              8850 | small-value flow                                                                   | out_active_day_ratio=0.18; activity_density=0.17; both_active_days=0.16; both_active_day_ratio=0.16; out_active_days=0.00           | total_flow_sum=-0.78; max_daily_total_flow=-0.74; total_in_sum=-0.70; avg_daily_total_flow=-0.68; max_daily_total_in=-0.67                  |                 -0.242976  |                   -0.0466896 |          -0.52643   |           -0.00986605  |                   -0.424625   |
|         3 |            0 |              9257 | high transaction intensity, directional imbalance                                  | activity_density=6.39; tx_concentration_ratio=3.59; avg_daily_tx_count=3.13; max_daily_tx_count=1.21; both_active_day_ratio=1.20    | activity_span_days=-2.81; in_active_days=-1.64; active_days_observed=-1.30; out_active_days=-1.09; total_flow_cv=-0.91                      |                  0.779521  |                    0.0701136 |          -0.015152  |            0.54495     |                    0.0776228  |
|         3 |            1 |              2743 | high transaction intensity, directional imbalance, bursty/volatile                 | avg_daily_tx_count=6.62; std_daily_tx_count=5.55; max_daily_tx_count=4.17; tx_concentration_ratio=3.44; total_tx=2.28               | activity_span_days=-1.31; active_days_observed=-0.79; in_active_days=-0.64; in_out_day_balance=-0.35; out_active_days=-0.18                 |                  3.06943   |                   -0.153329  |           0.0108672 |            0.54495     |                    1.23811    |
|         4 |            0 |              2634 | large-value flow, bursty/volatile                                                  | avg_daily_net_flow=1.66; total_net_flow_sum=1.41; std_daily_total_out=1.09; avg_daily_total_out=1.07; max_daily_total_out=0.91      | out_active_day_ratio=-0.31; both_active_day_ratio=-0.18; activity_density=-0.12; in_active_day_ratio=-0.09; both_active_days=0.00           |                  0.0424864 |                    0.0145529 |           0.943998  |           -0.0588708   |                    0.478609   |
|         4 |            1 |              9366 | value_scale-leaning                                                                | avg_daily_net_flow=0.94; total_net_flow_sum=0.87; in_out_day_balance=0.65; flow_concentration_ratio=0.54; total_flow_cv=0.48        | out_active_day_ratio=-0.54; both_active_day_ratio=-0.45; avg_daily_tx_count=-0.34; avg_daily_total_out=-0.26; max_daily_tx_count=-0.22      |                 -0.14152   |                   -0.0480808 |           0.169209  |           -0.0909674   |                    0.113637   |
|         5 |            0 |               630 | high transaction intensity, persistent activity, large-value flow, bursty/volatile | avg_daily_net_flow=9.01; total_net_flow_sum=6.83; avg_daily_total_in=6.66; avg_daily_total_flow=6.56; max_daily_total_flow=5.83     | out_active_day_ratio=-0.69; tx_concentration_ratio=-0.41; both_active_day_ratio=-0.40; avg_daily_tx_count=0.18; both_active_days=0.29       |                  0.988363  |                    0.806798  |           4.96054   |            0.0496628   |                    2.15228    |
|         5 |            1 |             11370 | large-value flow                                                                   | avg_daily_net_flow=2.04; total_net_flow_sum=1.68; in_out_day_balance=1.48; std_daily_net_flow=0.97; avg_daily_total_in=0.97         | out_active_day_ratio=-1.13; out_active_days=-1.09; both_active_day_ratio=-0.72; total_out_sum=-0.54; max_daily_total_out=-0.53              |                 -0.0424988 |                   -0.263197  |           0.66779   |            0.0325415   |                    0.40046    |

## Best Internal k Diagnostics

|   cluster |   candidate_k |   silhouette |   davies_bouldin |   calinski_harabasz |   min_subcluster_share |
|----------:|--------------:|-------------:|-----------------:|--------------------:|-----------------------:|
|         0 |             3 |     0.180152 |         1.7461   |             2753.6  |               0.240667 |
|         1 |             2 |     0.216536 |         1.90615  |             2653.32 |               0.384667 |
|         2 |             2 |     0.184814 |         2.01547  |             1957.7  |               0.2625   |
|         3 |             2 |     0.364019 |         1.24469  |             5461.27 |               0.228583 |
|         4 |             2 |     0.243147 |         1.62366  |             2935.28 |               0.2195   |
|         5 |             2 |     0.726391 |         0.702299 |             9856.36 |               0.0525   |

## Most Important Within-Cluster Separating Features

| feature              |   kruskal_stat |   p_value |   q_value_bh |   cluster |
|:---------------------|---------------:|----------:|-------------:|----------:|
| max_daily_total_out  |        7016.2  |         0 |            0 |         0 |
| max_daily_total_flow |        6993.34 |         0 |            0 |         0 |
| total_out_sum        |        6989.97 |         0 |            0 |         0 |
| std_daily_total_out  |        6989.2  |         0 |            0 |         0 |
| std_daily_total_flow |        6968.77 |         0 |            0 |         0 |
| total_flow_sum       |        6958.27 |         0 |            0 |         0 |
| avg_daily_total_out  |        6920.19 |         0 |            0 |         0 |
| avg_daily_total_flow |        6892.78 |         0 |            0 |         0 |
| total_out_sum        |        6493.34 |         0 |            0 |         1 |
| total_flow_sum       |        6337.63 |         0 |            0 |         1 |
| avg_daily_total_out  |        6322.85 |         0 |            0 |         1 |
| max_daily_total_out  |        6306.74 |         0 |            0 |         1 |
| std_daily_total_out  |        6263.81 |         0 |            0 |         1 |
| total_in_sum         |        6190.98 |         0 |            0 |         1 |
| avg_daily_total_flow |        6065.89 |         0 |            0 |         1 |
| max_daily_total_flow |        5995.6  |         0 |            0 |         1 |
| avg_daily_total_out  |        8473.99 |         0 |            0 |         2 |
| std_daily_total_flow |        8239.26 |         0 |            0 |         2 |
| max_daily_total_out  |        8117.28 |         0 |            0 |         2 |
| avg_daily_total_in   |        8076.79 |         0 |            0 |         2 |
| max_daily_total_flow |        8073.84 |         0 |            0 |         2 |
| std_daily_total_out  |        8042.37 |         0 |            0 |         2 |
| avg_daily_total_flow |        8030.87 |         0 |            0 |         2 |
| total_out_sum        |        7945.22 |         0 |            0 |         2 |
| std_daily_tx_count   |        6389.19 |         0 |            0 |         3 |
| tx_count_cv          |        5180.34 |         0 |            0 |         3 |
| max_daily_tx_count   |        4932.41 |         0 |            0 |         3 |
| total_tx             |        4837.06 |         0 |            0 |         3 |
| activity_density     |        4463.46 |         0 |            0 |         3 |
| activity_span_days   |        4410.94 |         0 |            0 |         3 |
| avg_daily_tx_count   |        2892.67 |         0 |            0 |         3 |
| total_flow_cv        |        2840.79 |         0 |            0 |         3 |
| avg_daily_total_out  |        5600.94 |         0 |            0 |         4 |
| std_daily_total_out  |        5561.12 |         0 |            0 |         4 |
| avg_daily_total_flow |        5556.62 |         0 |            0 |         4 |
| max_daily_total_out  |        5541.03 |         0 |            0 |         4 |
| total_out_sum        |        5504.95 |         0 |            0 |         4 |
| total_flow_sum       |        5468.11 |         0 |            0 |         4 |
| avg_daily_total_in   |        5414.55 |         0 |            0 |         4 |
| std_daily_total_flow |        5375.42 |         0 |            0 |         4 |
| max_daily_total_in   |        1790.44 |         0 |            0 |         5 |
| max_daily_total_flow |        1790.44 |         0 |            0 |         5 |
| total_net_flow_sum   |        1790.44 |         0 |            0 |         5 |
| total_in_sum         |        1790.44 |         0 |            0 |         5 |
| total_flow_sum       |        1790.44 |         0 |            0 |         5 |
| avg_daily_net_flow   |        1790.01 |         0 |            0 |         5 |
| avg_daily_total_in   |        1790.01 |         0 |            0 |         5 |
| avg_daily_total_flow |        1790.01 |         0 |            0 |         5 |

## Strongest Pairwise Subcluster Separations

|   subcluster_a |   subcluster_b |   significant_features |   mean_abs_cliffs_delta |   max_abs_cliffs_delta |   cluster |
|---------------:|---------------:|-----------------------:|------------------------:|-----------------------:|----------:|
|              0 |              1 |                     33 |                0.656136 |               0.999948 |         5 |
|              0 |              2 |                     32 |                0.639567 |               0.923209 |         0 |
|              0 |              1 |                     33 |                0.520029 |               0.949224 |         4 |
|              1 |              2 |                     30 |                0.507767 |               0.995364 |         0 |
|              0 |              1 |                     31 |                0.499473 |               0.963354 |         2 |
|              0 |              1 |                     33 |                0.495241 |               0.872944 |         1 |
|              0 |              1 |                     30 |                0.43129  |               0.97885  |         3 |
|              0 |              1 |                     29 |                0.358204 |               0.972214 |         0 |

## Interpretation

A main cluster should be treated as internally heterogeneous when it has: positive internal silhouette, multiple statistically significant separating features, large Cliff's delta between subclusters, and interpretable subtype profiles. Under this criterion, the KMeans6 clusters are not merely six homogeneous blocks; they contain behavioral subtypes such as high-volume persistent wallets, bursty short-lived wallets, receiver/sink-like wallets, and large-value directional wallets.
