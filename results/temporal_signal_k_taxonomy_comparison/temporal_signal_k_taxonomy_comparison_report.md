# Temporal Signal K-Taxonomy Comparison

## Purpose

This pack compares whether the temporal signal results align more strongly with K4, K5, or K6 EOA taxonomies.

It does not ask which K is globally best by itself. Instead, it asks whether the same wallets' wavelength and time-domain signal clusters reproduce any of the candidate static taxonomies.

## Input

Signal-analysis source folder: `results\temporal_signal_analysis_edge_sample_10k`
Sample size: `10000` wallets

## Correspondence Results

| taxonomy   | signal_cluster_type   |   sample_wallets |   taxonomy_k |   signal_k |       ari |      nmi |
|:-----------|:----------------------|-----------------:|-------------:|-----------:|----------:|---------:|
| k4_cluster | wavelength_cluster    |            10000 |            4 |          5 | 0.0814267 | 0.162774 |
| k4_cluster | time_domain_cluster   |            10000 |            4 |          5 | 0.114757  | 0.324712 |
| k5_cluster | wavelength_cluster    |            10000 |            5 |          5 | 0.102741  | 0.166247 |
| k5_cluster | time_domain_cluster   |            10000 |            5 |          5 | 0.177729  | 0.325028 |
| k6_cluster | wavelength_cluster    |            10000 |            6 |          5 | 0.0850757 | 0.164531 |
| k6_cluster | time_domain_cluster   |            10000 |            6 |          5 | 0.121978  | 0.304783 |

Interpretation: ARI and NMI are low when the temporal signal clusters do not reproduce the static taxonomy. This is useful because it tells us that frequency and time-domain behaviour add a separate axis rather than merely repeating aggregate KMeans labels.

## Network Null Tests

| label_type          |   edge_count |   observed_same_cluster_ratio |   null_mean |   null_std |   p_value_upper |
|:--------------------|-------------:|------------------------------:|------------:|-----------:|----------------:|
| k4_cluster          |        46771 |                      0.762695 |    0.289383 | 0.0207348  |      0.00990099 |
| k5_cluster          |        46771 |                      0.619657 |    0.203539 | 0.00880306 |      0.00990099 |
| k6_cluster          |        46771 |                      0.538731 |    0.191584 | 0.0137981  |      0.00990099 |
| wavelength_cluster  |        46771 |                      0.314319 |    0.230128 | 0.0174219  |      0.00990099 |
| time_domain_cluster |        46771 |                      0.393235 |    0.427587 | 0.0418751  |      0.772277   |

Interpretation: the network null test asks whether wallets with the same label transact with each other more often than expected after shuffling labels across the same sampled wallets.

## Paper-Framing Comment

The strongest conservative framing is that K4/K5/K6 describe static aggregate behavioural roles, while wavelength and time-domain clusters describe temporal behavioural states. A good paper contribution is the comparison between these layers, not a claim that one layer fully replaces the other.