# Paper-Ready Temporal Signal Extension

## Research Question

After removing contract addresses and selecting K5 as the main EOA behavioural taxonomy, the next question is whether wallet roles are also visible in temporal activity signals.

The signal-extension question is:

> Do Ethereum EOA wallets exhibit temporal activity rhythms and time-domain behavioural states that provide evidence beyond the static K4/K5/K6 aggregate feature taxonomies?

## Method

We used an edge-aware sample of 10,000 EOA wallets. Wallets were selected from sampled transaction-edge endpoints so that the later network-science validation would have enough sample-internal edges.

For each wallet, we reconstructed daily 2022 transaction-count, total-flow, and net-flow signals from the monthly wallet-daily files.

We extracted two temporal representations:

1. Frequency-domain features from FFT spectra of daily transaction-count and value-flow signals.
2. Time-domain features describing active days, inactive gaps, active streaks, burstiness, switching, direction bias, and weekly change intensity.

We clustered each representation into five signal clusters and compared them with K4, K5, and K6 static taxonomies.

## Signal Cluster Validation

| label_type          |   k |   cluster_share_min |   cluster_share_max |   observed_silhouette |   null_mean_silhouette |   null_std_silhouette |   p_value_upper |   seed_stability_mean_ari |   seed_stability_min_ari |   seed_stability_mean_nmi |   seed_stability_min_nmi |
|:--------------------|----:|--------------------:|--------------------:|----------------------:|-----------------------:|----------------------:|----------------:|--------------------------:|-------------------------:|--------------------------:|-------------------------:|
| wavelength_cluster  |   5 |              0.0899 |              0.335  |              0.206535 |             -0.0159619 |            0.00559367 |      0.00990099 |                  0.655592 |                 0.549542 |                  0.696201 |                 0.617588 |
| time_domain_cluster |   5 |              0.0476 |              0.6327 |              0.25824  |             -0.0352159 |            0.017075   |      0.00990099 |                  0.516759 |                 0.332054 |                  0.624552 |                 0.496236 |

Both signal representations have positive observed silhouette values and shuffled-label p-values of approximately 0.0099. This supports the limited claim that the signal clusters have measurable feature-space structure in the sampled data.

Seed-stability is moderate rather than perfect. This means the signal clusters are structured, but they should be treated as exploratory temporal states rather than fixed identity classes.

## Temporal Cluster Interpretations

Wavelength cluster labels:

|   wavelength_cluster | interpretive_label                | evidence                                                                                                             |
|---------------------:|:----------------------------------|:---------------------------------------------------------------------------------------------------------------------|
|                    0 | distributed irregular rhythm      | more distributed spectrum; highest transaction spectral share: high-frequency; dominant period estimate: 365.00 days |
|                    1 | long-horizon slow-cycle rhythm    | more concentrated spectrum; highest transaction spectral share: low-frequency; dominant period estimate: 365.00 days |
|                    2 | short-cycle high-frequency rhythm | more distributed spectrum; highest transaction spectral share: high-frequency; dominant period estimate: 8.90 days   |
|                    3 | long-horizon slow-cycle rhythm    | more concentrated spectrum; highest transaction spectral share: low-frequency; dominant period estimate: 365.00 days |
|                    4 | distributed irregular rhythm      | more distributed spectrum; highest transaction spectral share: high-frequency; dominant period estimate: 365.00 days |

Time-domain cluster labels:

|   time_domain_cluster | interpretive_label           | evidence                                                                          |
|----------------------:|:-----------------------------|:----------------------------------------------------------------------------------|
|                     0 | sparse inactive-gap state    | long inactive gap with low active-day share; median active days: 10.00            |
|                     1 | near-continuous active state | active on almost the entire yearly observation window; median active days: 357.00 |
|                     2 | sustained active state       | active on more than half of observed days; median active days: 224.00             |
|                     3 | intermittent active state    | active on many days but not continuously; median active days: 104.00              |
|                     4 | sparse inactive-gap state    | long inactive gap with low active-day share; median active days: 15.50            |

These labels are profile-based interpretations. They should be used as descriptive shorthand, not as ground-truth wallet identities.

## Relationship To K4, K5, And K6

| taxonomy   | signal_cluster_type   |   sample_wallets |   taxonomy_k |   signal_k |       ari |      nmi |
|:-----------|:----------------------|-----------------:|-------------:|-----------:|----------:|---------:|
| k4_cluster | wavelength_cluster    |            10000 |            4 |          5 | 0.0814267 | 0.162774 |
| k4_cluster | time_domain_cluster   |            10000 |            4 |          5 | 0.114757  | 0.324712 |
| k5_cluster | wavelength_cluster    |            10000 |            5 |          5 | 0.102741  | 0.166247 |
| k5_cluster | time_domain_cluster   |            10000 |            5 |          5 | 0.177729  | 0.325028 |
| k6_cluster | wavelength_cluster    |            10000 |            6 |          5 | 0.0850757 | 0.164531 |
| k6_cluster | time_domain_cluster   |            10000 |            6 |          5 | 0.121978  | 0.304783 |

The temporal signal clusters do not strongly reproduce K4, K5, or K6. K5 has the highest ARI for both wavelength and time-domain comparisons, but the values remain low to moderate.

This is important academically because it suggests that temporal signal analysis is not merely duplicating the static clustering result. It adds a separate behavioural layer.

## Network-Science Validation

| label_type          |   edge_count |   observed_same_cluster_ratio |   null_mean |   null_std |   p_value_upper | note                                                                                         |
|:--------------------|-------------:|------------------------------:|------------:|-----------:|----------------:|:---------------------------------------------------------------------------------------------|
| k5_cluster          |        46771 |                      0.619657 |    0.203539 | 0.00880306 |      0.00990099 | sampled September 2022 transaction edges restricted to wallets in the signal-analysis sample |
| wavelength_cluster  |        46771 |                      0.314319 |    0.230128 | 0.0174219  |      0.00990099 | sampled September 2022 transaction edges restricted to wallets in the signal-analysis sample |
| time_domain_cluster |        46771 |                      0.393235 |    0.427587 | 0.0418751  |      0.772277   | sampled September 2022 transaction edges restricted to wallets in the signal-analysis sample |

The 10,000-wallet edge-aware sample produced 46,771 usable sampled transaction edges.

The wavelength clusters show same-cluster transaction concentration above the shuffled-label null model. This supports a sample-based network-alignment claim for frequency-domain wallet rhythms.

The time-domain clusters do not show same-cluster transaction concentration above the null model in the 10k run. This weakens any claim that burst/gap/streak states are assortative in the sampled transaction network.

K-taxonomy network comparison:

| label_type          |   edge_count |   observed_same_cluster_ratio |   null_mean |   null_std |   p_value_upper |
|:--------------------|-------------:|------------------------------:|------------:|-----------:|----------------:|
| k4_cluster          |        46771 |                      0.762695 |    0.289383 | 0.0207348  |      0.00990099 |
| k5_cluster          |        46771 |                      0.619657 |    0.203539 | 0.00880306 |      0.00990099 |
| k6_cluster          |        46771 |                      0.538731 |    0.191584 | 0.0137981  |      0.00990099 |
| wavelength_cluster  |        46771 |                      0.314319 |    0.230128 | 0.0174219  |      0.00990099 |
| time_domain_cluster |        46771 |                      0.393235 |    0.427587 | 0.0418751  |      0.772277   |

K4, K5, and K6 all show strong same-cluster transaction concentration compared with shuffled labels. This confirms that the static aggregate taxonomies remain more directly aligned with transaction-network homophily than the time-domain signal states.

## Event-Adjacent Temporal Checks

|   event_month | metric                |   observed |   non_event_mean |   event_mean |   rank_p_value |
|--------------:|:----------------------|-----------:|-----------------:|-------------:|---------------:|
|        202206 | composition_l1_change |  0.144633  |        0.0828654 |     0.112415 |       0.166667 |
|        202211 | composition_l1_change |  0.134731  |        0.0828654 |     0.112415 |       0.25     |
|        202209 | composition_l1_change |  0.123227  |        0.0828654 |     0.112415 |       0.416667 |
|        202205 | composition_l1_change |  0.0470701 |        0.0828654 |     0.112415 |       1        |
|        202211 | mean_row_entropy_bits |  1.81179   |        1.78828   |     1.77697  |       0.25     |
|        202205 | mean_row_entropy_bits |  1.77838   |        1.78828   |     1.77697  |       0.583333 |
|        202209 | mean_row_entropy_bits |  1.76115   |        1.78828   |     1.77697  |       0.833333 |
|        202206 | mean_row_entropy_bits |  1.75656   |        1.78828   |     1.77697  |       0.916667 |
|        202211 | self_transition_rate  |  0.471991  |        0.500434  |     0.498947 |       0.166667 |
|        202206 | self_transition_rate  |  0.497295  |        0.500434  |     0.498947 |       0.416667 |
|        202205 | self_transition_rate  |  0.509626  |        0.500434  |     0.498947 |       0.75     |
|        202209 | self_transition_rate  |  0.516877  |        0.500434  |     0.498947 |       1        |

The event-adjacent tests should be treated as contextual checks, not causal evidence. Some event-adjacent month pairs show larger composition changes or lower self-transition rates, but the rank tests do not by themselves prove that external market events caused wallet-state movement.

## Two-Step Return Behaviour

|   k |   month_t |   month_t1 |   month_t2 |   left_original_state_count |   observed_two_step_return_rate |   null_mean |    null_std |   p_value_upper |   observed_minus_null |
|----:|----------:|-----------:|-----------:|----------------------------:|--------------------------------:|------------:|------------:|----------------:|----------------------:|
|   5 |    202201 |     202202 |     202203 |                      224334 |                        0.340827 |    0.283737 | 0.000907963 |      0.00199601 |             0.0570899 |
|   5 |    202202 |     202203 |     202204 |                      224856 |                        0.359817 |    0.312349 | 0.000901125 |      0.00199601 |             0.0474684 |
|   5 |    202203 |     202204 |     202205 |                      232778 |                        0.340496 |    0.302276 | 0.000908685 |      0.00199601 |             0.0382205 |
|   5 |    202204 |     202205 |     202206 |                      200447 |                        0.363388 |    0.315221 | 0.000937656 |      0.00199601 |             0.0481669 |
|   5 |    202205 |     202206 |     202207 |                      210289 |                        0.342809 |    0.29305  | 0.000971196 |      0.00199601 |             0.0497589 |
|   5 |    202206 |     202207 |     202208 |                      201369 |                        0.350511 |    0.30964  | 0.000976818 |      0.00199601 |             0.0408703 |
|   5 |    202207 |     202208 |     202209 |                      265949 |                        0.299471 |    0.293056 | 0.000844323 |      0.00199601 |             0.0064154 |
|   5 |    202208 |     202209 |     202210 |                      246010 |                        0.376867 |    0.311949 | 0.000850353 |      0.00199601 |             0.064918  |
|   5 |    202209 |     202210 |     202211 |                      273867 |                        0.325932 |    0.294103 | 0.000853088 |      0.00199601 |             0.0318289 |
|   5 |    202210 |     202211 |     202212 |                      272261 |                        0.32106  |    0.298691 | 0.000831513 |      0.00199601 |             0.0223681 |

Across monthly triples, wallets that left their original K5 state often returned two months later more frequently than expected under the null model. This supports a cautious claim of behavioural mean reversion or temporary state excursions, not a claim about user intent.

## Contribution

The contribution is a layered validation framework for Ethereum EOA wallet behaviour:

1. Static aggregate roles from K4/K5/K6 clustering.
2. Frequency-domain temporal rhythms from daily wallet signals.
3. Time-domain activity states from burst, gap, and persistence features.
4. Network-science validation through shuffled-label edge null tests.
5. Temporal stability checks through transition and two-step return analyses.

The strongest paper claim is not that one K value or one signal model is universally correct. The stronger claim is that wallet behaviour can be studied as multiple related layers: aggregate role, temporal rhythm, time-domain activity state, and network position.