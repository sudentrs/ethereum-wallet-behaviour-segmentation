# Mixed vs EOA-Only Cluster Comparison

This report compares the pre-Gate-1 mixed-address KMeans6 labels with the post-Gate-1 EOA-only KMeans6 labels on overlapping EOA wallets.

## Summary

|   mixed_wallets |   eoa_only_wallets |   overlapping_eoa_wallets |   matched_wallets_hungarian |   matched_share_hungarian |   adjusted_rand_index |   normalized_mutual_information |
|----------------:|-------------------:|--------------------------:|----------------------------:|--------------------------:|----------------------:|--------------------------------:|
|     2.73824e+06 |        2.44387e+06 |               2.44387e+06 |                 1.43937e+06 |                  0.588971 |              0.331576 |                        0.391289 |

## Mixed Cluster EOA/Contract Composition

|   mixed_cluster |   mixed_wallets |   classified_wallets |   eoa_wallets |   contract_wallets |   contract_share |   eoa_share |
|----------------:|----------------:|---------------------:|--------------:|-------------------:|-----------------:|------------:|
|               0 |          616169 |               616169 |        569090 |              47079 |        0.076406  |    0.923594 |
|               1 |          281978 |               281978 |        241608 |              40370 |        0.143167  |    0.856833 |
|               2 |          805252 |               805252 |        738815 |              66437 |        0.0825046 |    0.917495 |
|               3 |          209578 |               209578 |        109087 |             100491 |        0.479492  |    0.520508 |
|               4 |          790194 |               790194 |        753530 |              36664 |        0.0463987 |    0.953601 |
|               5 |           35072 |                35072 |         31738 |               3334 |        0.0950616 |    0.904938 |

## Hungarian Matches

|   mixed_cluster |   eoa_only_cluster |   matched_wallets |   share_of_mixed_cluster_eoas |   share_of_eoa_only_cluster |   share_of_all_overlapping_eoas |
|----------------:|-------------------:|------------------:|------------------------------:|----------------------------:|--------------------------------:|
|               0 |                  3 |            282973 |                      0.497238 |                   0.654106  |                      0.115789   |
|               1 |                  2 |            143172 |                      0.59258  |                   0.813884  |                      0.0585842  |
|               2 |                  0 |            541515 |                      0.732951 |                   0.736228  |                      0.221581   |
|               3 |                  4 |             92201 |                      0.845206 |                   0.648116  |                      0.0377275  |
|               4 |                  1 |            367313 |                      0.487456 |                   0.687743  |                      0.1503     |
|               5 |                  5 |             12193 |                      0.384177 |                   0.0287927 |                      0.00498922 |

## Top EOA-Only Destinations By Mixed Cluster

|   mixed_cluster | top_eoa_only_destinations    |
|----------------:|:-----------------------------|
|               0 | C3=0.497; C0=0.270; C5=0.099 |
|               1 | C2=0.593; C5=0.378; C3=0.021 |
|               2 | C0=0.733; C1=0.137; C3=0.072 |
|               3 | C4=0.845; C3=0.086; C2=0.062 |
|               4 | C1=0.487; C5=0.345; C3=0.108 |
|               5 | C1=0.405; C5=0.384; C2=0.116 |

## Interpretation Note

Cluster IDs are not semantic identities across reruns. Use the Hungarian matches and row-share crosstab to discuss which mixed clusters are preserved, split, or reorganized after contract addresses are removed.