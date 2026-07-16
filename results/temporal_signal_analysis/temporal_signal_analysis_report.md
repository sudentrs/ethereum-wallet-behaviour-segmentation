# Temporal Signal Analysis Pack

## Purpose

This pack starts the next academic stage of the project: moving from static aggregate wallet roles to temporal signal-based wallet profiling.

The analysis has four parts:

1. Wavelength/spectrum-based clustering of wallet activity signals.
2. Frequency-domain analysis with frequency on the x-axis.
3. Time-domain temporal signature analysis.
4. Network-science validation of the resulting signal clusters.

## Method Summary

This run uses a `stratified` sample of `5000` EOA wallets from the K5 taxonomy.

For each sampled wallet, the script builds daily 2022 signals from transaction count, total value flow, and net flow.

Frequency-domain features are extracted using the real FFT of daily transaction-count and total-flow signals. The DC component is removed so the analysis focuses on rhythms rather than total scale.

Time-domain features measure active days, active/inactive switching, burstiness, active streaks, inactive gaps, direction bias, and weekly change intensity.

The network-science step uses sampled September 2022 transaction edges and tests whether signal-cluster labels show same-cluster transaction concentration stronger than shuffled-label null models.

## Cluster Correspondence With Existing K5 Roles

| comparison                                  |       ari |       nmi |
|:--------------------------------------------|----------:|----------:|
| K5 vs wavelength/spectral clusters          | 0.0589942 | 0.0987275 |
| K5 vs time-domain clusters                  | 0.142331  | 0.205998  |
| wavelength/spectral vs time-domain clusters | 0.0279124 | 0.0542731 |

Interpretation: ARI and NMI measure whether the new signal-derived clusters reproduce the existing K5 behavioural taxonomy. Low or moderate agreement is not necessarily a failure; it can mean the temporal-signal view captures a different axis of behaviour.

## Signal-Cluster Statistical Validation

| label_type          |   k |   cluster_share_min |   cluster_share_max |   observed_silhouette |   null_mean_silhouette |   null_std_silhouette |   p_value_upper |   seed_stability_mean_ari |   seed_stability_min_ari |   seed_stability_mean_nmi |   seed_stability_min_nmi |
|:--------------------|----:|--------------------:|--------------------:|----------------------:|-----------------------:|----------------------:|----------------:|--------------------------:|-------------------------:|--------------------------:|-------------------------:|
| wavelength_cluster  |   5 |              0.0596 |              0.3894 |              0.143933 |             -0.0192619 |            0.00810464 |        0.047619 |                  0.554589 |                 0.396576 |                  0.637778 |                 0.530939 |
| time_domain_cluster |   5 |              0.0066 |              0.4126 |              0.148166 |             -0.0507867 |            0.0363244  |        0.047619 |                  0.435969 |                 0.243609 |                  0.509776 |                 0.354572 |

Interpretation: silhouette compares within-cluster compactness against between-cluster separation. The shuffled-label p-value asks whether the observed grouping is more separated than random labels with the same wallets. Seed-stability ARI/NMI checks whether the result is sensitive to KMeans initialization.

## Network-Science Signal Validation

| label_type          |   edge_count |   observed_same_cluster_ratio |   null_mean |   null_std |   p_value_upper | note                                                                                         |
|:--------------------|-------------:|------------------------------:|------------:|-----------:|----------------:|:---------------------------------------------------------------------------------------------|
| k5_cluster          |            1 |                             1 |           1 |          0 |               1 | sampled September 2022 transaction edges restricted to wallets in the signal-analysis sample |
| wavelength_cluster  |            1 |                             1 |           1 |          0 |               1 | sampled September 2022 transaction edges restricted to wallets in the signal-analysis sample |
| time_domain_cluster |            1 |                             1 |           1 |          0 |               1 | sampled September 2022 transaction edges restricted to wallets in the signal-analysis sample |

Interpretation: this is an early network check. Because the signal clusters are built on a wallet sample, the network test is limited to sampled wallets that also appear in the sampled transaction-edge file.

The network test is underpowered if the edge count is very small. In that case, it should be treated as a pipeline proof-of-concept rather than evidence for or against network alignment.

An edge-aware sample is designed to make this check stronger by selecting wallets that are more likely to appear in the transaction-edge file.

## Run Findings

- The wavelength/spectral clusters have low agreement with the original K5 roles, which suggests that frequency-domain rhythm captures a different behavioural axis from aggregate wallet features.
- The time-domain clusters show somewhat stronger, but still limited, agreement with K5. This is expected because both include activity intensity and persistence information.
- Frequency-domain and time-domain clusters also have low agreement with each other, suggesting that rhythm-based behaviour and direct time-axis burst/gap behaviour are related but not identical.
- The network-science component has been scaffolded, but this sample is not large enough for a meaningful signal-cluster network test.

## Main Output Files

- `signal_analysis_wallet_sample.csv`
- `wallet_frequency_domain_features.csv`
- `wallet_time_domain_features.csv`
- `temporal_signal_cluster_assignments.csv`
- `wavelength_cluster_profiles.csv`
- `wavelength_cluster_interpretive_labels.csv`
- `time_domain_cluster_profiles.csv`
- `time_domain_cluster_interpretive_labels.csv`
- `signal_cluster_correspondence_summary.csv`
- `k5_signal_cluster_enrichment.csv`
- `signal_cluster_validation_summary.csv`
- `network_signal_cluster_null_tests.csv`
- `k5_cluster_edge_adjacency_counts.csv`
- `wavelength_cluster_edge_adjacency_counts.csv`
- `time_domain_cluster_edge_adjacency_counts.csv`
- `figures/frequency_power_by_k5_role.png`
- `figures/frequency_power_by_wavelength_cluster.png`
- `figures/flow_frequency_power_by_wavelength_cluster.png`

## Academic Claim Boundary

This is a first signal-analysis pipeline, not yet a final causal or intelligence-style detection system.

Safe wording:

> We extend wallet segmentation by representing wallet activity as daily temporal signals and comparing frequency-domain, time-domain, and network-structural evidence.

Avoid wording:

> These methods identify real-world entities, prove causality, or replicate classified security-agency systems.