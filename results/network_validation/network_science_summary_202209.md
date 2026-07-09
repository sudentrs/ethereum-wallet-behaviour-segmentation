# Network Science Cluster Analysis - 202209

## Supervisor Questions Mapped to Outputs

- Daha farkli clusterlara ayrilabilir mi: `alternative_k_clusterability.csv/png` checks k=3..10 against silhouette and ARI.
- Clusterlari daha fazla nasil tanimlayabiliriz: `cluster_behavior_labels.csv` gives behavior labels and strongest features.
- Farkli clusterlar istatistiksel olarak ne kadar farkli: `cluster_global_statistical_tests.csv` and `cluster_pairwise_statistical_tests.csv` use Kruskal-Wallis, Mann-Whitney U, Cliff's delta, and BH-FDR q-values.
- C1 ve C4 arasinda baglanti yok gibi ama zamanla degisiyor mu: `c1_c4_daily_connection_timeseries.csv/png` tracks C1->C4 and C4->C1 by day.
- Clusterlar manali insan davranislari ifade ediyor mu: behavior labels should be interpreted as wallet behavior types, then checked against event/context knowledge.

## Cluster Behavior Labels

|   cluster | behavior_label                                                                         | top_high_features                                                                                                                     | top_low_features                                                                                                                            |   activity_score |   flow_size_score |   direction_score |   volatility_score |
|----------:|:---------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------|-----------------:|------------------:|------------------:|-------------------:|
|         0 | activity-leaning                                                                       | tx_concentration_ratio=0.24; avg_daily_total_out=0.24; std_daily_tx_count=0.23; std_daily_total_out=0.21; max_daily_total_out=0.18    | total_net_flow_sum=-0.64; avg_daily_net_flow=-0.57; std_daily_net_flow=-0.27; max_daily_total_in=-0.26; total_in_sum=-0.25                  |        0.0796091 |        -0.172728  |        0.00275213 |         -0.0674267 |
|         1 | high activity, large value flow, directional/inflow-outflow imbalance, bursty/volatile | total_tx=1.00; max_daily_tx_count=0.91; active_days_observed=0.90; activity_density=0.89; in_active_days=0.88                         | tx_concentration_ratio=-0.45; in_out_day_balance=-0.13; flow_concentration_ratio=-0.00; in_active_day_ratio=0.03; out_active_day_ratio=0.22 |        0.613228  |         0.367494  |        0.418421   |          0.507461  |
|         2 | low activity                                                                           | out_active_day_ratio=0.39; both_active_day_ratio=0.38; tx_concentration_ratio=0.14; in_active_day_ratio=0.12; both_active_days=-0.00  | total_flow_sum=-1.34; total_in_sum=-1.31; max_daily_total_flow=-1.26; max_daily_total_in=-1.25; std_daily_total_flow=-1.13                  |       -0.355651  |        -0.866141  |       -0.0204436  |         -0.83018   |
|         3 | high activity                                                                          | tx_concentration_ratio=5.24; activity_density=4.51; avg_daily_tx_count=4.42; std_daily_tx_count=2.17; max_daily_tx_count=1.62         | activity_span_days=-3.86; active_days_observed=-1.26; in_active_days=-1.15; std_daily_total_flow=-0.92; std_daily_net_flow=-0.92            |        1.43458   |        -0.228381  |        0.0265916  |         -0.28162   |
|         4 | flow_size-leaning                                                                      | in_out_day_balance=0.38; flow_concentration_ratio=0.34; avg_daily_net_flow=0.29; total_net_flow_sum=0.22; tx_concentration_ratio=0.12 | both_active_days=-0.43; out_active_day_ratio=-0.43; avg_daily_tx_count=-0.37; both_active_day_ratio=-0.36; out_active_days=-0.34            |       -0.161133  |         0.0843891 |       -0.197405   |         -0.010666  |
|         5 | large value flow, bursty/volatile                                                      | avg_daily_net_flow=1.19; avg_daily_total_in=1.17; avg_daily_total_flow=1.10; std_daily_total_in=1.10; max_daily_total_in=1.08         | out_active_day_ratio=-0.89; both_active_day_ratio=-0.58; total_out_sum=-0.58; max_daily_total_out=-0.57; std_daily_total_out=-0.53          |        0.0395338 |         0.703614  |       -0.148639   |          0.510201  |

## KNN Network Quality

|   nodes |   edges |    density |   intra_cluster_edge_ratio |   inter_cluster_edge_ratio |   label_modularity |   detected_communities |   ari_detected_vs_kmeans6 |
|--------:|--------:|-----------:|---------------------------:|---------------------------:|-------------------:|-----------------------:|--------------------------:|
|   14717 |   44281 | 0.00040892 |                   0.894898 |                   0.105102 |           0.728067 |                     91 |                  0.299076 |

## Alternative k Check

|   k |   silhouette |   ari_vs_kmeans6 |   inertia |
|----:|-------------:|-----------------:|----------:|
|   3 |     0.253971 |         0.27589  |    520025 |
|   4 |     0.202136 |         0.277042 |    438813 |
|   5 |     0.1802   |         0.259031 |    431197 |
|   6 |     0.20675  |         0.396941 |    339974 |
|   7 |     0.161232 |         0.470915 |    325032 |
|   8 |     0.182916 |         0.422535 |    270310 |
|   9 |     0.17592  |         0.361921 |    260270 |
|  10 |     0.183981 |         0.396685 |    240190 |

## Strongest Pairwise Statistical Differences

|   cluster_a |   cluster_b | feature            |     median_a |         median_b |   median_difference_a_minus_b |   mannwhitney_u |   p_value |   cliffs_delta |   effect_size_abs |   q_value_bh |
|------------:|------------:|:-------------------|-------------:|-----------------:|------------------------------:|----------------:|----------:|---------------:|------------------:|-------------:|
|           2 |           5 | avg_daily_net_flow |  3.59019e-27 |      1.67777e+08 |                  -1.67777e+08 |     0           |         0 |      -1        |          1        |            0 |
|           0 |           5 | avg_daily_net_flow |  0           |      1.67777e+08 |                  -1.67777e+08 |     0           |         0 |      -1        |          1        |            0 |
|           0 |           5 | total_net_flow_sum |  0           |      2.364e+09   |                  -2.364e+09   |     0           |         0 |      -1        |          1        |            0 |
|           2 |           5 | total_net_flow_sum |  5.16988e-26 |      2.364e+09   |                  -2.364e+09   |     0           |         0 |      -1        |          1        |            0 |
|           2 |           4 | total_net_flow_sum |  5.16988e-26 | 175959           |             -175959           |  6736           |         0 |      -0.997844 |          0.997844 |            0 |
|           2 |           4 | avg_daily_net_flow |  3.59019e-27 |  10252.6         |              -10252.6         |  9253           |         0 |      -0.997039 |          0.997039 |            0 |
|           3 |           4 | avg_daily_tx_count | 15           |      1.55556     |                  13.4444      |     6.23793e+06 |         0 |       0.996137 |          0.996137 |            0 |
|           2 |           5 | std_daily_net_flow |  9.83509e-10 |      4.0953e+08  |                  -4.0953e+08  | 18414.5         |         0 |      -0.994107 |          0.994107 |            0 |
|           2 |           3 | avg_daily_tx_count |  1.75        |     15           |                 -13.25        | 18650.5         |         0 |      -0.994032 |          0.994032 |            0 |
|           2 |           3 | max_daily_tx_count |  3           |     28           |                 -25           | 20440.5         |         0 |      -0.993459 |          0.993459 |            0 |
|           2 |           5 | max_daily_total_in |  1.6756e-08  |      1.775e+09   |                  -1.775e+09   | 22620.5         |         0 |      -0.992761 |          0.992761 |            0 |
|           2 |           5 | total_in_sum       |  5.62494e-08 |      2.364e+09   |                  -2.364e+09   | 25764           |         0 |      -0.991756 |          0.991756 |            0 |

## Globally Most Different Features

| feature              |   kruskal_stat |   p_value |   q_value_bh |
|:---------------------|---------------:|----------:|-------------:|
| active_days_observed |        7248.98 |         0 |            0 |
| activity_span_days   |        7469.58 |         0 |            0 |
| activity_density     |        5395.82 |         0 |            0 |
| total_tx             |        5353.93 |         0 |            0 |
| total_in_sum         |        8116.01 |         0 |            0 |
| total_out_sum        |        4151.54 |         0 |            0 |
| total_net_flow_sum   |       10506    |         0 |            0 |
| total_flow_sum       |        7731.36 |         0 |            0 |
| avg_daily_tx_count   |        7727.75 |         0 |            0 |
| avg_daily_total_in   |        7614.64 |         0 |            0 |
| avg_daily_total_out  |        3954.84 |         0 |            0 |
| avg_daily_net_flow   |       10330.7  |         0 |            0 |