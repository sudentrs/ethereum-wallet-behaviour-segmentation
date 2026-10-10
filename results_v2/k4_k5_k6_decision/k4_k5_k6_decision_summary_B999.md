# K4/K5/K6 Decision Summary After B=999 Network Validation

## What Was Recomputed

The network validation was rerun for K4, K5, and K6 using all labelled ERC-20 transfer edges in each 2022 monthly file.
For each month and k, wallet labels were shuffled B = 999 times while keeping the observed transaction edges fixed.
Monthly p-values were Holm-adjusted across the twelve months, and Fisher combined p-values were computed for each k.

## Decision Table

|   k |   min_share |   max_share |   seed_ari |   silhouette |   davies_bouldin |   network_sig_months_holm |   network_mean_observed_minus_null |   network_fisher_p |   network_mean_observed_same_role |   network_mean_null | interpretation                                                                                        |
|----:|------------:|------------:|-----------:|-------------:|-----------------:|--------------------------:|-----------------------------------:|-------------------:|----------------------------------:|--------------------:|:------------------------------------------------------------------------------------------------------|
|   4 |   0.0812699 |    0.395621 |   0.58936  |     0.163333 |          1.68596 |                        12 |                          0.109621  |        3.65999e-23 |                          0.442    |            0.332379 | Strongest conservative network-supported taxonomy; less detailed role vocabulary.                     |
|   5 |   0.0633684 |    0.377797 |   0.712603 |     0.156608 |          1.73913 |                         1 |                          0.004704  |        0.000184365 |                          0.286043 |            0.281339 | Most descriptive main taxonomy with strongest seed stability, but weaker network evidence than K4/K6. |
|   6 |   0.0614063 |    0.304972 |   0.484808 |     0.153641 |          1.72131 |                        11 |                          0.0402885 |        2.08707e-21 |                          0.266705 |            0.226416 | Network-supported fine-grained taxonomy, but weaker seed stability and more fragmented roles.         |

## Main Interpretation

- K4 is the strongest conservative network-supported solution: all 12 months remain significant after Holm correction.
- K5 remains useful as the richer behavioural taxonomy because it has the highest seed stability and interpretable five-role structure, but its network evidence is weaker: 3 raw significant months and 1 Holm-significant month.
- K6 has strong network evidence, with 11 Holm-significant months, but its seed stability is lower than K5 and the role vocabulary is more fragmented.

## Recommended Paper Claim

Use K5 as the main descriptive behavioural taxonomy only with careful wording.
Do not claim that K5 is the statistically strongest resolution across all validation layers.
Say that K4 is the conservative network-supported comparison, K5 is the richer seed-stable taxonomy, and K6 is a fine-grained network-supported but less stable alternative.