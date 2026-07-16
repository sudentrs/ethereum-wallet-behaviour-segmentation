# Robustness And Claim Calibration Summary

## What is robust enough to claim

- K5 remains a defensible main taxonomy because it balances interpretability, static feature separation, temporal validation, and downstream comparison results.
- K5 has the strongest signal correspondence among K4/K5/K6 for wavelength clusters (ARI 0.103) and time-domain clusters (ARI 0.178), but the values are not high enough to say the signal clusters reproduce K5.
- Wavelength clusters show feature-space structure (silhouette 0.207) and network alignment above the shuffled-label null.
- Two-step return behaviour is consistently above the null model across monthly triples, with observed-minus-null ranging from 0.006 to 0.065.

## What must be worded carefully

- Time-domain clusters are useful as burst/gap/persistence states, but in the 10k edge-aware network test they do not have stronger same-cluster edge concentration than the shuffled-label null.
- Event-adjacent results are contextual checks, not causal event studies.
- Cluster labels describe behavioural states from transaction data, not verified real-world identities.

## Key tables

K-taxonomy vs signal-cluster correspondence:

| taxonomy   | signal_cluster_type   |   sample_wallets |   taxonomy_k |   signal_k |       ari |      nmi |
|:-----------|:----------------------|-----------------:|-------------:|-----------:|----------:|---------:|
| k4_cluster | wavelength_cluster    |            10000 |            4 |          5 | 0.0814267 | 0.162774 |
| k4_cluster | time_domain_cluster   |            10000 |            4 |          5 | 0.114757  | 0.324712 |
| k5_cluster | wavelength_cluster    |            10000 |            5 |          5 | 0.102741  | 0.166247 |
| k5_cluster | time_domain_cluster   |            10000 |            5 |          5 | 0.177729  | 0.325028 |
| k6_cluster | wavelength_cluster    |            10000 |            6 |          5 | 0.0850757 | 0.164531 |
| k6_cluster | time_domain_cluster   |            10000 |            6 |          5 | 0.121978  | 0.304783 |

Signal cluster validation:

| label_type          |   k |   cluster_share_min |   cluster_share_max |   observed_silhouette |   null_mean_silhouette |   null_std_silhouette |   p_value_upper |   seed_stability_mean_ari |   seed_stability_min_ari |   seed_stability_mean_nmi |   seed_stability_min_nmi |
|:--------------------|----:|--------------------:|--------------------:|----------------------:|-----------------------:|----------------------:|----------------:|--------------------------:|-------------------------:|--------------------------:|-------------------------:|
| wavelength_cluster  |   5 |              0.0899 |              0.335  |              0.206535 |             -0.0159619 |            0.00559367 |      0.00990099 |                  0.655592 |                 0.549542 |                  0.696201 |                 0.617588 |
| time_domain_cluster |   5 |              0.0476 |              0.6327 |              0.25824  |             -0.0352159 |            0.017075   |      0.00990099 |                  0.516759 |                 0.332054 |                  0.624552 |                 0.496236 |

Network null tests:

| label_type          |   edge_count |   observed_same_cluster_ratio |   null_mean |   null_std |   p_value_upper |
|:--------------------|-------------:|------------------------------:|------------:|-----------:|----------------:|
| k4_cluster          |        46771 |                      0.762695 |    0.289383 | 0.0207348  |      0.00990099 |
| k5_cluster          |        46771 |                      0.619657 |    0.203539 | 0.00880306 |      0.00990099 |
| k6_cluster          |        46771 |                      0.538731 |    0.191584 | 0.0137981  |      0.00990099 |
| wavelength_cluster  |        46771 |                      0.314319 |    0.230128 | 0.0174219  |      0.00990099 |
| time_domain_cluster |        46771 |                      0.393235 |    0.427587 | 0.0418751  |      0.772277   |