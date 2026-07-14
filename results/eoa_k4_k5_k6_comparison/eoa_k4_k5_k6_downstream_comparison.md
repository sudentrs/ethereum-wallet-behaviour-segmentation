# EOA-Only K4/K5/K6 Downstream Validation Comparison

## Purpose

This report compares the realistic post-contract-removal role counts: `K=4`, `K=5`, and `K=6`.

The goal is to decide whether `K=5` remains defensible after running the same downstream network and temporal checks for the neighbouring alternatives.

## Summary Table

|   k |   min_cluster_share |   max_cluster_share |   full_sensitivity_silhouette |   seed_stability_ari |   network_observed_same_cluster_sample |   network_random_null_mean |   network_random_null_p |   temporal_self_transition_mean |   two_step_return_mean | verdict                                                                                                         |
|----:|--------------------:|--------------------:|------------------------------:|---------------------:|---------------------------------------:|---------------------------:|------------------------:|--------------------------------:|-----------------------:|:----------------------------------------------------------------------------------------------------------------|
|   4 |           0.0812699 |            0.395621 |                      0.163333 |             0.58936  |                               0.43044  |                   0.342584 |              0.00990099 |                        0.513618 |               0.354465 | Strong conservative baseline: best network-null result, acceptable stability, but less expressive.              |
|   5 |           0.0633684 |            0.377797 |                      0.156608 |             0.712603 |                               0.29554  |                   0.298159 |              0.564356   |                        0.499893 |               0.342118 | Best richer taxonomy balance: strong seed stability and temporal behaviour, but network-null evidence is mixed. |
|   6 |           0.0614063 |            0.304972 |                      0.153641 |             0.484808 |                               0.273865 |                   0.24521  |              0.049505   |                        0.469122 |               0.311776 | Exploratory fine-grained taxonomy: more roles and borderline network-null support, but weaker seed stability.   |

## What Changed After Downstream Validation

Before downstream validation, `K=5` looked like the best richer taxonomy because it balanced interpretability, cluster size, and seed stability better than `K=6`.

After downstream validation, the result is more nuanced.

`K=4` has the strongest transaction-network null result. Its observed same-cluster ratio is `0.4304` compared with a null mean of `0.3426`, with p-value `0.0099`.

`K=5` remains strong on seed stability and temporal behaviour, but its network-null test is not supportive. Its observed same-cluster ratio is `0.2955` compared with a null mean of `0.2982`, with p-value `0.5644`.

`K=6` has borderline network-null support with p-value `0.0495`, but its seed stability is much weaker than `K=5` in the full K-sensitivity table.

## Interpretation By Candidate

### K=4

K4 is the strongest conservative option. It passes the downstream network-null test clearly and has no tiny clusters. The tradeoff is that it merges behaviours that K5 separates, so it is less useful if the research goal is a richer behavioural role vocabulary.

### K=5

K5 is still defensible as the preferred richer role taxonomy. It has better seed stability than K6 and preserves five interpretable roles without creating very small clusters. Its temporal validation is also meaningful: wallets show moderate month-to-month persistence and a clear two-step return pattern.

The weakness is network validation. K5 role-to-role flows are structured, but the sampled same-cluster null test does not show stronger within-role concentration than randomized labels. Therefore, K5 should not be described as strongly network-validated.

### K=6

K6 gives the most fine-grained role vocabulary among these three options. Its network-null result is borderline supportive, but its seed stability is weaker and its role taxonomy is more sensitive to initialization. This makes K6 useful as an exploratory or appendix comparison, not the safest main taxonomy.

## Recommended Claim

The most academically honest conclusion is:

> EOA-only wallet behaviour supports a stable coarse structure and several defensible role resolutions. `K=4` is the strongest conservative network-aligned taxonomy. `K=5` is the preferred richer behavioural taxonomy because it balances stability, interpretability, cluster size, and temporal persistence. `K=6` provides additional granularity but is less stable and should be treated as exploratory unless further validation is added.

## Paper-Facing Decision

Use `K=5` if the paper's main goal is an interpretable behavioural role taxonomy.

Use `K=4` as a conservative robustness comparison, especially when discussing transaction-network evidence.

Use `K=6` only as a fine-grained sensitivity comparison.

Do not claim that one K is the universal true number of Ethereum wallet roles.