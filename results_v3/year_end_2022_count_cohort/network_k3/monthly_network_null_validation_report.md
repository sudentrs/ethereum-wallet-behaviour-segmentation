# Monthly Network Null Validation (K3 SEED492)

## Purpose

This report repeats the same-role transaction concentration test across monthly ERC-20 transfer snapshots.
The null model keeps sampled transaction edges fixed and randomly permutes cluster labels across the unique wallets appearing in those sampled edges.

## Summary

- Months processed: `12`.
- Months with upper-tail p-value below 0.05: `12`.
- Mean observed same-cluster ratio: `0.5593`.
- Mean null same-cluster ratio: `0.4677`.
- Mean observed-minus-null difference: `0.0916`.

## Monthly Results

|   month |   raw_rows_read |   rows_with_both_cluster_labels |   coverage_ratio |   exact_same_cluster_edges |   exact_same_cluster_ratio |   sample_edges |   observed_sample_same_cluster_ratio |   null_mean |   null_std |   p_value_upper |
|--------:|----------------:|--------------------------------:|-----------------:|---------------------------:|---------------------------:|---------------:|-------------------------------------:|------------:|-----------:|----------------:|
|  202201 |        18914888 |                         2757891 |         0.145805 |                    1517371 |                   0.550193 |         200000 |                             0.549725 |    0.475123 | 0.0121647  |           0.001 |
|  202202 |        17002499 |                         2452882 |         0.144266 |                    1392016 |                   0.567502 |         200000 |                             0.569745 |    0.482411 | 0.0092215  |           0.001 |
|  202203 |        21944715 |                         2996699 |         0.136557 |                    1699350 |                   0.567074 |         200000 |                             0.568055 |    0.479723 | 0.00945693 |           0.001 |
|  202204 |        19189598 |                         2850701 |         0.148554 |                    1659827 |                   0.582252 |         200000 |                             0.581905 |    0.475417 | 0.0100234  |           0.001 |
|  202205 |        18497423 |                         3083225 |         0.166684 |                    1764938 |                   0.572432 |         200000 |                             0.572805 |    0.473853 | 0.00958492 |           0.001 |
|  202206 |        14595953 |                         2814210 |         0.192808 |                    1661418 |                   0.590367 |         200000 |                             0.590535 |    0.476896 | 0.00867039 |           0.001 |
|  202207 |        18827784 |                         3324462 |         0.176572 |                    2000295 |                   0.60169  |         200000 |                             0.60303  |    0.467751 | 0.0110573  |           0.001 |
|  202208 |        20304712 |                         3558981 |         0.175279 |                    2015142 |                   0.566213 |         200000 |                             0.5674   |    0.472089 | 0.0116594  |           0.001 |
|  202209 |        23178780 |                         3974290 |         0.171462 |                    1995531 |                   0.50211  |         200000 |                             0.5017   |    0.474423 | 0.00963483 |           0.001 |
|  202210 |        23497364 |                         3398495 |         0.144633 |                    1852645 |                   0.545137 |         200000 |                             0.545375 |    0.466337 | 0.00955386 |           0.001 |
|  202211 |        25630339 |                         3923930 |         0.153097 |                    2168387 |                   0.552606 |         200000 |                             0.553315 |    0.453517 | 0.0125608  |           0.001 |
|  202212 |        24327004 |                         3597751 |         0.147891 |                    1820933 |                   0.506131 |         200000 |                             0.50841  |    0.415417 | 0.0124374  |           0.001 |

## Interpretation

A low upper-tail p-value means the observed same-cluster transaction ratio is higher than expected under shuffled labels.
A non-significant p-value means same-labelled wallets do not transact with one another more often than the shuffled-label baseline for that month.
This test evaluates network homophily only; it does not test whether feature-space roles are interpretable or temporally persistent.