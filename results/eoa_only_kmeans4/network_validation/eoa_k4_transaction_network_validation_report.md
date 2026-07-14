# EOA-Only K4 Transaction-Network Validation - 202209

## Purpose

This analysis checks whether the EOA-Only K4 wallet roles also appear in the real transaction network. A defensible behavioural taxonomy should not only separate wallets in feature space; wallets with the same or related roles should show non-random interaction structure.

## Main Metrics

|   month |   cluster_wallets |   raw_rows_read |   rows_with_both_cluster_labels |   coverage_ratio |   total_cluster_labeled_tx |   self_loop_tx |   self_loop_ratio_all_labeled_tx |   sample_edges |   observed_sample_same_cluster_ratio |   null_mean |   null_std |   null_max |   p_value_upper |   sample_wallet_graph_nodes |   sample_wallet_graph_edges |   sample_wallet_graph_density |   sample_wallet_label_modularity |   sample_wallet_attribute_assortativity |   sample_wallet_intra_cluster_edge_ratio |
|--------:|------------------:|----------------:|--------------------------------:|-----------------:|---------------------------:|---------------:|---------------------------------:|---------------:|-------------------------------------:|------------:|-----------:|-----------:|----------------:|----------------------------:|----------------------------:|------------------------------:|---------------------------------:|----------------------------------------:|-----------------------------------------:|
|  202209 |           2443868 |        23178780 |                         3671344 |         0.158392 |                    3671344 |        1439910 |                         0.392202 |         200000 |                              0.43044 |    0.342584 |  0.0122771 |   0.371325 |      0.00990099 |                      151251 |                      158487 |                   1.38557e-05 |                     -0.000578859 |                              -0.0685208 |                                  0.43044 |

## Role-To-Role Transaction Count Matrix

|    |                0 |      1 |      2 |     3 |
|---:|-----------------:|-------:|-------:|------:|
|  0 |      1.28966e+06 | 428192 | 513178 | 84376 |
|  1 | 148841           |  41441 |  36705 |  7753 |
|  2 | 387049           |  21163 |  87405 | 15512 |
|  3 | 246327           | 307302 |  35036 | 21399 |

## Cluster Network Centrality

|   cluster |   weighted_out_degree |   weighted_in_degree |    self_loop_tx |   external_out_tx |   external_in_tx |   net_external_in_minus_out |
|----------:|----------------------:|---------------------:|----------------:|------------------:|-----------------:|----------------------------:|
|         0 |           2.31541e+06 |          2.07188e+06 |     1.28966e+06 |       1.02575e+06 |           782217 |                     -243529 |
|         1 |      234740           |     798098           | 41441           |  193299           |           756657 |                      563358 |
|         2 |      511129           |     672324           | 87405           |  423724           |           584919 |                      161195 |
|         3 |      610064           |     129040           | 21399           |  588665           |           107641 |                     -481024 |

## Interpretation

The key proof-style check is the random-label comparison. It shuffles wallet cluster labels while preserving the same sampled transaction pairs. If the observed same-cluster transaction ratio is above the randomized ratios, then the EOA-Only K4 labels are aligned with transaction-network structure rather than behaving like arbitrary labels.

For this EOA-Only K4 run, the observed sampled same-cluster ratio was above the randomized-label null. This supports the claim that EOA-Only K4 roles have non-random within-role transaction-network alignment.

The role-level adjacency matrix shows which behavioural roles exchange transactions with each other. Strong diagonal values indicate within-role interaction, while strong off-diagonal values identify bridges between behavioural roles.

The wallet-graph modularity and assortativity metrics are sample-based network checks. Higher values indicate that wallet labels are organized in the transaction graph rather than being evenly mixed.