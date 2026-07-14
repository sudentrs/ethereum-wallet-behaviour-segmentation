# EOA-Only K5 Transaction-Network Validation - 202209

## Purpose

This analysis checks whether the EOA-only KMeans5 wallet roles also appear in the real transaction network. A defensible behavioural taxonomy should not only separate wallets in feature space; wallets with the same or related roles should show non-random interaction structure.

## Main Metrics

|   month |   cluster_wallets |   raw_rows_read |   rows_with_both_cluster_labels |   coverage_ratio |   total_cluster_labeled_tx |   self_loop_tx |   self_loop_ratio_all_labeled_tx |   sample_edges |   observed_sample_same_cluster_ratio |   null_mean |   null_std |   null_max |   p_value_upper |   sample_wallet_graph_nodes |   sample_wallet_graph_edges |   sample_wallet_graph_density |   sample_wallet_label_modularity |   sample_wallet_attribute_assortativity |   sample_wallet_intra_cluster_edge_ratio |
|--------:|------------------:|----------------:|--------------------------------:|-----------------:|---------------------------:|---------------:|---------------------------------:|---------------:|-------------------------------------:|------------:|-----------:|-----------:|----------------:|----------------------------:|----------------------------:|------------------------------:|---------------------------------:|----------------------------------------:|-----------------------------------------:|
|  202209 |           2443868 |        23178780 |                         3671344 |         0.158392 |                    3671344 |         936419 |                         0.255062 |         200000 |                              0.29554 |    0.298159 |  0.0163626 |   0.332275 |        0.564356 |                      151251 |                      158487 |                   1.38557e-05 |                     -0.000607574 |                              -0.0750724 |                                  0.29554 |

## Role-To-Role Transaction Count Matrix

|    |      0 |      1 |     2 |      3 |      4 |
|---:|-------:|-------:|------:|-------:|-------:|
|  0 |  55244 |  11462 | 11355 | 243025 |  77792 |
|  1 |  16935 |  27763 |  5417 |  94116 |  33245 |
|  2 |  20136 | 167337 | 19322 |  66547 | 174738 |
|  3 | 282770 | 378055 | 43544 | 532769 | 596179 |
|  4 | 144340 |  57366 | 38317 | 272249 | 301321 |

## Cluster Network Centrality

|   cluster |   weighted_out_degree |   weighted_in_degree |   self_loop_tx |   external_out_tx |   external_in_tx |   net_external_in_minus_out |
|----------:|----------------------:|---------------------:|---------------:|------------------:|-----------------:|----------------------------:|
|         0 |      398878           |     519425           |          55244 |  343634           |           464181 |                      120547 |
|         1 |      177476           |     641983           |          27763 |  149713           |           614220 |                      464507 |
|         2 |      448080           |     117955           |          19322 |  428758           |            98633 |                     -330125 |
|         3 |           1.83332e+06 |          1.20871e+06 |         532769 |       1.30055e+06 |           675937 |                     -624611 |
|         4 |      813593           |          1.18328e+06 |         301321 |  512272           |           881954 |                      369682 |

## Interpretation

The key proof-style check is the random-label comparison. It shuffles wallet cluster labels while preserving the same sampled transaction pairs. If the observed same-cluster transaction ratio is above the randomized ratios, then the K5 labels are aligned with transaction-network structure rather than behaving like arbitrary labels.

For this K5 run, the observed sampled same-cluster ratio was `0.2955`, while the randomized-label null mean was `0.2982` with an upper-tail p-value of `0.5644`. Therefore, this specific same-cluster network test does **not** support the claim that K5 roles form stronger within-role transaction structure than random labels.

This does not invalidate K5 as a feature-space and temporal role taxonomy, but it does weaken the network-validation claim. The K5 network evidence should be reported as mixed: the role-to-role adjacency matrix reveals structured transaction flows between roles, but the sampled wallet-level modularity, assortativity, and random-label same-cluster test do not show strong within-role network alignment.

The role-level adjacency matrix shows which behavioural roles exchange transactions with each other. Strong diagonal values indicate within-role interaction, while strong off-diagonal values identify bridges between behavioural roles.

The wallet-graph modularity and assortativity metrics are sample-based network checks. Higher values indicate that wallet labels are organized in the transaction graph rather than being evenly mixed.
