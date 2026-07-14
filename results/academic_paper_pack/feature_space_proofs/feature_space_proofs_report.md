# Feature-Space Proofs For EOA K4/K5/K6

## Purpose

This reproduces the feature-space proof style used in the earlier six-cluster work: KNN neighbourhood structure, global feature-separation tests, and pairwise cluster-separation tests.

## KNN Feature-Network Quality

|   k |   sample_wallets |   nodes |   edges |     density |   intra_cluster_edge_ratio |   label_modularity |   attribute_assortativity |   detected_communities |   ari_detected_vs_labels |
|----:|-----------------:|--------:|--------:|------------:|---------------------------:|-------------------:|--------------------------:|-----------------------:|-------------------------:|
|   4 |            20000 |   20000 |  140529 | 0.00070268  |                   0.870717 |           0.620141 |                  0.827407 |                     24 |                 0.190766 |
|   5 |            25000 |   25000 |  175815 | 0.000562631 |                   0.853937 |           0.653519 |                  0.81725  |                     22 |                 0.233549 |
|   6 |            30000 |   30000 |  210757 | 0.000468365 |                   0.847687 |           0.680625 |                  0.817066 |                     22 |                 0.253958 |

## Strongest Global Feature Separations

|   k | feature              |   kruskal_stat |   p_value |   epsilon_squared |   q_value_bh |
|----:|:---------------------|---------------:|----------:|------------------:|-------------:|
|   4 | active_days_observed |        12141.7 |         0 |          0.607056 |            0 |
|   4 | activity_span_days   |        12012   |         0 |          0.600568 |            0 |
|   4 | in_active_days       |        11777.8 |         0 |          0.588856 |            0 |
|   4 | activity_density     |        10800.6 |         0 |          0.539989 |            0 |
|   4 | out_active_days      |        10667.4 |         0 |          0.533325 |            0 |
|   4 | total_in_sum         |        10588.4 |         0 |          0.529375 |            0 |
|   4 | total_flow_sum       |        10491   |         0 |          0.524504 |            0 |
|   4 | max_daily_total_in   |        10490.3 |         0 |          0.524469 |            0 |
|   5 | std_daily_total_in   |        17055.3 |         0 |          0.68219  |            0 |
|   5 | std_daily_total_flow |        17022.9 |         0 |          0.680893 |            0 |
|   5 | total_in_sum         |        16968.2 |         0 |          0.678704 |            0 |
|   5 | total_flow_sum       |        16878.9 |         0 |          0.675131 |            0 |
|   5 | max_daily_total_in   |        16869.9 |         0 |          0.674772 |            0 |
|   5 | max_daily_total_flow |        16779.1 |         0 |          0.671138 |            0 |
|   5 | avg_daily_total_in   |        16225.4 |         0 |          0.648984 |            0 |
|   5 | std_daily_net_flow   |        16155.6 |         0 |          0.646192 |            0 |
|   6 | std_daily_total_flow |        19311.1 |         0 |          0.643664 |            0 |
|   6 | std_daily_total_in   |        19220.6 |         0 |          0.640648 |            0 |
|   6 | total_flow_sum       |        18920.7 |         0 |          0.63065  |            0 |
|   6 | total_in_sum         |        18916.9 |         0 |          0.630524 |            0 |
|   6 | max_daily_total_in   |        18812.2 |         0 |          0.627031 |            0 |
|   6 | max_daily_total_flow |        18807.7 |         0 |          0.626881 |            0 |
|   6 | std_daily_net_flow   |        18302.5 |         0 |          0.610037 |            0 |
|   6 | avg_daily_total_flow |        18218.3 |         0 |          0.607232 |            0 |

## Strongest Pairwise Feature Separations

|   k |   cluster_a |   cluster_b | feature              |   median_a |   median_b |   median_difference_a_minus_b |   p_value |   cliffs_delta |   effect_size_abs |   q_value_bh |
|----:|------------:|------------:|:---------------------|-----------:|-----------:|------------------------------:|----------:|---------------:|------------------:|-------------:|
|   4 |           0 |           3 | activity_span_days   |   0.369422 | -2.24461   |                      2.61403  |         0 |       0.984161 |          0.984161 |            0 |
|   4 |           1 |           3 | activity_span_days   |   0.156987 | -2.24461   |                      2.4016   |         0 |       0.976919 |          0.976919 |            0 |
|   4 |           0 |           1 | total_tx             |   1.60174  | -0.0513689 |                      1.65311  |         0 |       0.972791 |          0.972791 |            0 |
|   4 |           0 |           3 | active_days_observed |   1.40234  | -0.911514  |                      2.31386  |         0 |       0.965353 |          0.965353 |            0 |
|   4 |           0 |           2 | total_in_sum         |   0.518532 | -0.691888  |                      1.21042  |         0 |       0.965139 |          0.965139 |            0 |
|   4 |           0 |           2 | max_daily_total_in   |   0.529005 | -0.670388  |                      1.19939  |         0 |       0.964243 |          0.964243 |            0 |
|   4 |           0 |           2 | total_flow_sum       |   0.553984 | -0.763725  |                      1.31771  |         0 |       0.962698 |          0.962698 |            0 |
|   4 |           0 |           2 | max_daily_total_flow |   0.561982 | -0.714901  |                      1.27688  |         0 |       0.961538 |          0.961538 |            0 |
|   4 |           0 |           3 | in_active_days       |   1.31396  | -0.885014  |                      2.19898  |         0 |       0.96007  |          0.96007  |            0 |
|   4 |           0 |           2 | std_daily_total_in   |   0.531442 | -0.616639  |                      1.14808  |         0 |       0.957852 |          0.957852 |            0 |
|   4 |           1 |           2 | max_daily_total_in   |   0.234559 | -0.670388  |                      0.904947 |         0 |       0.957341 |          0.957341 |            0 |
|   4 |           0 |           2 | std_daily_total_flow |   0.542105 | -0.635765  |                      1.17787  |         0 |       0.955117 |          0.955117 |            0 |
|   5 |           0 |           3 | max_daily_total_flow |  -0.714901 |  1.08544   |                     -1.80034  |         0 |      -0.999987 |          0.999987 |            0 |
|   5 |           0 |           3 | total_flow_sum       |  -0.763726 |  1.08182   |                     -1.84554  |         0 |      -0.999982 |          0.999982 |            0 |
|   5 |           0 |           3 | max_daily_total_in   |  -0.670388 |  1.07772   |                     -1.74811  |         0 |      -0.999956 |          0.999956 |            0 |
|   5 |           0 |           3 | avg_daily_total_flow |  -0.663512 |  1.15873   |                     -1.82225  |         0 |      -0.999955 |          0.999955 |            0 |
|   5 |           0 |           3 | total_in_sum         |  -0.691888 |  1.05237   |                     -1.74425  |         0 |      -0.999944 |          0.999944 |            0 |
|   5 |           0 |           3 | avg_daily_total_in   |  -0.626986 |  1.19302   |                     -1.82001  |         0 |      -0.999914 |          0.999914 |            0 |
|   5 |           0 |           3 | std_daily_total_flow |  -0.635765 |  1.10792   |                     -1.74368  |         0 |      -0.999146 |          0.999146 |            0 |
|   5 |           0 |           3 | std_daily_total_in   |  -0.616639 |  1.15135   |                     -1.76799  |         0 |      -0.999122 |          0.999122 |            0 |
|   5 |           2 |           4 | activity_span_days   |  -2.43397  |  0.372025  |                     -2.806    |         0 |      -0.998555 |          0.998555 |            0 |
|   5 |           1 |           2 | activity_span_days   |   0.125219 | -2.43397   |                      2.55919  |         0 |       0.989464 |          0.989464 |            0 |
|   5 |           0 |           3 | std_daily_net_flow   |  -0.578318 |  1.15728   |                     -1.7356   |         0 |      -0.987741 |          0.987741 |            0 |
|   5 |           0 |           3 | max_daily_total_out  |  -0.534178 |  1.42194   |                     -1.95612  |         0 |      -0.987243 |          0.987243 |            0 |
|   6 |           1 |           3 | std_daily_total_flow |  -0.635765 |  1.12239   |                     -1.75816  |         0 |      -1        |          1        |            0 |
|   6 |           1 |           3 | max_daily_total_flow |  -0.714901 |  1.10314   |                     -1.81804  |         0 |      -0.999999 |          0.999999 |            0 |
|   6 |           1 |           3 | total_flow_sum       |  -0.763726 |  1.10268   |                     -1.8664   |         0 |      -0.999999 |          0.999999 |            0 |
|   6 |           1 |           3 | avg_daily_total_flow |  -0.663512 |  1.17492   |                     -1.83843  |         0 |      -0.999999 |          0.999999 |            0 |
|   6 |           1 |           3 | avg_daily_total_in   |  -0.626986 |  1.21635   |                     -1.84334  |         0 |      -0.999865 |          0.999865 |            0 |
|   6 |           1 |           3 | std_daily_total_in   |  -0.616639 |  1.17319   |                     -1.78983  |         0 |      -0.999855 |          0.999855 |            0 |
|   6 |           1 |           3 | total_in_sum         |  -0.691888 |  1.07726   |                     -1.76915  |         0 |      -0.999852 |          0.999852 |            0 |
|   6 |           1 |           3 | max_daily_total_in   |  -0.670388 |  1.10078   |                     -1.77116  |         0 |      -0.99985  |          0.99985  |            0 |
|   6 |           2 |           4 | activity_span_days   |  -2.55013  |  0.384905  |                     -2.93503  |         0 |      -0.999358 |          0.999358 |            0 |
|   6 |           0 |           2 | activity_span_days   |   0.197363 | -2.55013   |                      2.74749  |         0 |       0.996163 |          0.996163 |            0 |
|   6 |           1 |           3 | std_daily_net_flow   |  -0.578318 |  1.18466   |                     -1.76298  |         0 |      -0.995091 |          0.995091 |            0 |
|   6 |           0 |           2 | activity_density     |  -0.194003 |  5.92168   |                     -6.11568  |         0 |      -0.992785 |          0.992785 |            0 |

## Interpretation

High intra-cluster KNN edge ratios and positive modularity show that cluster labels are visible in local feature-space neighbourhoods. Kruskal-Wallis and Mann-Whitney/Cliff's-delta tests confirm that cluster profiles differ on engineered behavioural features. These tests validate feature-space separation, not real-world identity labels.