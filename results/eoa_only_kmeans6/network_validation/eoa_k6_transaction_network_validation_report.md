# EOA-Only K6 Transaction-Network Validation - 202209

## Purpose

This analysis checks whether the EOA-Only K6 wallet roles also appear in the real transaction network. A defensible behavioural taxonomy should not only separate wallets in feature space; wallets with the same or related roles should show non-random interaction structure.

## Main Metrics

|   month |   cluster_wallets |   raw_rows_read |   rows_with_both_cluster_labels |   coverage_ratio |   total_cluster_labeled_tx |   self_loop_tx |   self_loop_ratio_all_labeled_tx |   sample_edges |   observed_sample_same_cluster_ratio |   null_mean |   null_std |   null_max |   p_value_upper |   sample_wallet_graph_nodes |   sample_wallet_graph_edges |   sample_wallet_graph_density |   sample_wallet_label_modularity |   sample_wallet_attribute_assortativity |   sample_wallet_intra_cluster_edge_ratio |
|--------:|------------------:|----------------:|--------------------------------:|-----------------:|---------------------------:|---------------:|---------------------------------:|---------------:|-------------------------------------:|------------:|-----------:|-----------:|----------------:|----------------------------:|----------------------------:|------------------------------:|---------------------------------:|----------------------------------------:|-----------------------------------------:|
|  202209 |           2443868 |        23178780 |                         3671344 |         0.158392 |                    3671344 |         900467 |                         0.245269 |         200000 |                             0.273865 |     0.24521 |  0.0147878 |    0.28378 |        0.049505 |                      151251 |                      158487 |                   1.38557e-05 |                       0.00783771 |                              -0.0485514 |                                 0.273865 |

## Role-To-Role Transaction Count Matrix

|    |      0 |      1 |     2 |      3 |      4 |     5 |
|---:|-------:|-------:|------:|-------:|-------:|------:|
|  0 |  10710 |  16385 |  2085 |  41273 |  23629 |  6788 |
|  1 |   9978 |  52756 |  8184 | 198923 | 112570 |  4807 |
|  2 | 168711 |  18536 | 14902 |  56435 | 152071 | 26174 |
|  3 | 338991 | 237352 | 32642 | 418695 | 545344 | 90805 |
|  4 |  55955 | 174038 | 36903 | 253081 | 387268 | 35292 |
|  5 |   9521 |   6897 |  4520 |  70157 |  32830 | 16136 |

## Cluster Network Centrality

|   cluster |   weighted_out_degree |   weighted_in_degree |   self_loop_tx |   external_out_tx |   external_in_tx |   net_external_in_minus_out |
|----------:|----------------------:|---------------------:|---------------:|------------------:|-----------------:|----------------------------:|
|         0 |      100870           |     593866           |          10710 |   90160           |           583156 |                      492996 |
|         1 |      387218           |     505964           |          52756 |  334462           |           453208 |                      118746 |
|         2 |      436829           |      99236           |          14902 |  421927           |            84334 |                     -337593 |
|         3 |           1.66383e+06 |          1.03856e+06 |         418695 |       1.24513e+06 |           619869 |                     -625265 |
|         4 |      942537           |          1.25371e+06 |         387268 |  555269           |           866444 |                      311175 |
|         5 |      140061           |     180002           |          16136 |  123925           |           163866 |                       39941 |

## Interpretation

The key proof-style check is the random-label comparison. It shuffles wallet cluster labels while preserving the same sampled transaction pairs. If the observed same-cluster transaction ratio is above the randomized ratios, then the EOA-Only K6 labels are aligned with transaction-network structure rather than behaving like arbitrary labels.

For this EOA-Only K6 run, the observed sampled same-cluster ratio was above the randomized-label null. This supports the claim that EOA-Only K6 roles have non-random within-role transaction-network alignment.

The role-level adjacency matrix shows which behavioural roles exchange transactions with each other. Strong diagonal values indicate within-role interaction, while strong off-diagonal values identify bridges between behavioural roles.

The wallet-graph modularity and assortativity metrics are sample-based network checks. Higher values indicate that wallet labels are organized in the transaction graph rather than being evenly mixed.