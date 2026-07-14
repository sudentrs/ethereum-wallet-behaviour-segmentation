# EOA-Only K5 vs K6 Comparison

This report compares the post-Gate-1 EOA-only `k=5` and `k=6` clusterings.

## Summary

|   overlapping_wallets |   hungarian_matched_wallets |   hungarian_matched_share |   adjusted_rand_index |   normalized_mutual_information |
|----------------------:|----------------------------:|--------------------------:|----------------------:|--------------------------------:|
|           2.44387e+06 |                 1.53104e+06 |                  0.626484 |              0.453592 |                        0.507152 |

## Hungarian Matches

|   k5_cluster |   k6_cluster |   matched_wallets |   share_of_k5_cluster |   share_of_k6_cluster |   share_of_all_wallets |
|-------------:|-------------:|------------------:|----------------------:|----------------------:|-----------------------:|
|            0 |            0 |            663264 |              0.854717 |              0.901755 |              0.271399  |
|            1 |            1 |            430732 |              0.466521 |              0.806486 |              0.17625   |
|            2 |            4 |            139538 |              0.901036 |              0.980866 |              0.0570972 |
|            3 |            2 |             84701 |              0.462647 |              0.481496 |              0.0346586 |
|            4 |            5 |            212809 |              0.523342 |              0.50253  |              0.0870788 |

## Interpretation

`k=5` and `k=6` are related but not identical. Use this comparison to identify whether the sixth cluster is a stable added role or a split of an existing broader role.

The final paper should not select `k=6` only because it was used before Gate 1. Selection should combine interpretability, stability, transaction-graph validation, and temporal persistence.

## Visual Outputs

- `figures/k5_to_k6_row_share_heatmap.png`
- `figures/k5_k6_cluster_size_comparison.png`
- `figures/k5_profile_heatmap.png`
- `figures/k6_profile_heatmap.png`
- `figures/k_sensitivity_k5_k6.png`