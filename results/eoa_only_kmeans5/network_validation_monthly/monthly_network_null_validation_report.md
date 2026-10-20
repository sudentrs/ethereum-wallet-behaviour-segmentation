# Monthly Network Null Validation (eoa_only_kmeans5)

## Purpose

This report repeats the same-role transaction concentration test across monthly ERC-20 transfer snapshots.
The null model keeps sampled transaction edges fixed and randomly permutes cluster labels across the unique wallets appearing in those sampled edges.

## Summary

- Months processed: `12`.
- Months with upper-tail p-value below 0.05: `5`.
- Mean observed same-cluster ratio: `0.2877`.
- Mean null same-cluster ratio: `0.2757`.
- Mean observed-minus-null difference: `0.0120`.

## Monthly Results

|   month |   raw_rows_read |   rows_with_both_cluster_labels |   coverage_ratio |   exact_same_cluster_edges |   exact_same_cluster_ratio |   sample_edges |   observed_sample_same_cluster_ratio |   null_mean |   null_std |   p_value_upper |
|--------:|----------------:|--------------------------------:|-----------------:|---------------------------:|---------------------------:|---------------:|-------------------------------------:|------------:|-----------:|----------------:|
|  202201 |        18914888 |                         2670575 |         0.141189 |                     747502 |                   0.279903 |         200000 |                             0.280305 |    0.273164 | 0.00979004 |      0.267327   |
|  202202 |        17002499 |                         2370355 |         0.139412 |                     683820 |                   0.288488 |         200000 |                             0.287115 |    0.278755 | 0.00930639 |      0.168317   |
|  202203 |        21944715 |                         2896102 |         0.131973 |                     856839 |                   0.295859 |         200000 |                             0.294975 |    0.275155 | 0.01053    |      0.019802   |
|  202204 |        19189598 |                         2751795 |         0.1434   |                     804326 |                   0.292291 |         200000 |                             0.29178  |    0.279062 | 0.0106481  |      0.118812   |
|  202205 |        18497423 |                         2987219 |         0.161494 |                     850324 |                   0.284654 |         200000 |                             0.28524  |    0.278401 | 0.011675   |      0.326733   |
|  202206 |        14595953 |                         2728945 |         0.186966 |                     822415 |                   0.301367 |         200000 |                             0.30149  |    0.282669 | 0.011775   |      0.0594059  |
|  202207 |        18827784 |                         3205572 |         0.170258 |                     961111 |                   0.299825 |         200000 |                             0.29927  |    0.279774 | 0.0112874  |      0.039604   |
|  202208 |        20304712 |                         3429727 |         0.168913 |                     982178 |                   0.286372 |         200000 |                             0.28597  |    0.284161 | 0.0137687  |      0.445545   |
|  202209 |        23178780 |                         3671344 |         0.158392 |                     936419 |                   0.255062 |         200000 |                             0.256605 |    0.279176 | 0.0127505  |      0.970297   |
|  202210 |        23497364 |                         3265634 |         0.138979 |                     969156 |                   0.296774 |         200000 |                             0.296255 |    0.276118 | 0.00993215 |      0.019802   |
|  202211 |        25630339 |                         3785054 |         0.147679 |                    1112301 |                   0.293867 |         200000 |                             0.294515 |    0.267072 | 0.0112798  |      0.00990099 |
|  202212 |        24327004 |                         3430908 |         0.141033 |                     958044 |                   0.279239 |         200000 |                             0.278735 |    0.254834 | 0.0132584  |      0.019802   |

## Figures

- `figures/monthly_observed_vs_null_same_cluster_ratio.png`
- `figures/monthly_network_null_p_values.png`

## Interpretation

A low upper-tail p-value means the observed same-cluster transaction ratio is higher than expected under shuffled labels.
A non-significant p-value means same-labelled wallets do not transact with one another more often than the shuffled-label baseline for that month.
This test evaluates network homophily only; it does not test whether feature-space roles are interpretable or temporally persistent.
