# K4/K5/K6 Evidence Matrix

This table combines the current internal, network, feature-holdout, and temporal validation outputs.
It is a paper-integration table, not a new experiment.

Important caveat: temporal evidence is conditional on the legacy monthly assignment/scaling procedure.
The temporal package reports a monthly window mismatch and a mixed-population scaler provenance issue, so temporal claims should be worded as conditional evidence rather than final causal proof.

|   k | cluster_size_range   |   silhouette_mean |   seed_stability_ari | network_holm_sig_months   |   network_mean_observed_minus_null |   feature_holdout_mean_agreement | feature_holdout_worst      |   persistence_holdout_agreement | self_transition_observed_vs_expected   |   temporal_kappa | two_step_return_observed_vs_null   | two_step_holm_sig_triples   | paper_interpretation                                                                                                                                                                        |
|----:|:---------------------|------------------:|---------------------:|:--------------------------|-----------------------------------:|---------------------------------:|:---------------------------|--------------------------------:|:---------------------------------------|-----------------:|:-----------------------------------|:----------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|   4 | 8.1%-39.6%           |             0.163 |                0.589 | 12/12                     |                              0.11  |                            0.73  | 0.557 (value_flow_holdout) |                           0.746 | 0.514 vs 0.347                         |            0.256 | 0.353 vs 0.283                     | 10/10                       | Conservative alternative. Strongest network evidence and strongest feature-holdout robustness, with good temporal persistence, but fewer behavioural roles.                                 |
|   5 | 6.3%-37.8%           |             0.157 |                0.713 | 1/12                      |                              0.005 |                            0.612 | 0.481 (value_flow_holdout) |                           0.644 | 0.500 vs 0.323                         |            0.261 | 0.341 vs 0.262                     | 10/10                       | Main descriptive taxonomy. Best seed stability and richer role vocabulary, but weaker network same-role evidence than K4/K6 and weaker feature-holdout recovery than K4.                    |
|   6 | 6.1%-30.5%           |             0.154 |                0.485 | 11/12                     |                              0.04  |                            0.669 | 0.590 (value_flow_holdout) |                           0.657 | 0.469 vs 0.286                         |            0.257 | 0.311 vs 0.223                     | 10/10                       | Fine-grained alternative. Network evidence is strong and activity holdout recovery is good, but seed stability is weakest and one role is fragile under a volatility/concentration holdout. |

## Paper-Facing Reading

- K4 is the strongest conservative model: it has the clearest network-null support and strongest feature-holdout robustness.
- K5 is still defensible as the main descriptive taxonomy: it has the best seed stability and a richer behavioural vocabulary.
- K6 adds finer detail, but it is less stable and more fragile in feature-holdout recovery.
- The paper should avoid saying that K5 is statistically best across all tests. A safer claim is that K5 is selected for interpretability, while K4 is the stronger conservative alternative.

## Suggested Model-Selection Wording

Across candidate resolutions, K4, K5, and K6 emphasize different trade-offs.
K4 provides the strongest conservative validation profile, with all twelve monthly network-null tests significant after Holm correction and the strongest average feature-holdout recovery.
K5 provides the most stable KMeans solution across seeds and a richer behavioural vocabulary, which makes it useful as the main descriptive taxonomy.
K6 provides finer-grained structure and strong network evidence, but its lower seed stability and fragile holdout recovery indicate that the extra resolution should be interpreted cautiously.
Therefore, this paper reports K5 as the primary descriptive taxonomy while treating K4 as a conservative robustness reference and K6 as a fine-grained sensitivity check.
