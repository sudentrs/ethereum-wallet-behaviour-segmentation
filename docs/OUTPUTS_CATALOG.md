# Outputs Catalog

This catalog explains the selected outputs included in this curated repo.

## `results/paper_process/`

### `paper_process_status_after_run.md`

High-level summary of the paper-focused validation work.

Use this first when trying to remember what was completed and what each test means.

### `formal_cluster_correspondence_definition.md`

Defines how cross-analysis cluster correspondences were formalized.

This is useful for explaining that cluster IDs do not automatically mean the same thing across runs.

### `cross_dataset_correspondence_permutation_summary.csv`

Permutation-test summary for wallet-label overlap across two clustering analyses.

Key result:

- Observed maximum bipartite wallet-label overlap: about 0.3952.
- Random-label null mean: about 0.2539.
- Empirical p-value: about 0.000999.

Interpretation:

The observed alignment was stronger than random-label expectation.

### `cross_dataset_bipartite_matching_pairs.csv`

Cluster-pair matching table from bipartite/Hungarian matching.

Use this to explain which cluster in one analysis best corresponds to which cluster in another.

### `cross_feature_set_spearman_summary.csv`

Summary of Spearman correlations between original and expanded feature sets.

Interpretation:

The feature sets are related but not redundant.

### `minimum_observation_experiment_summary.csv`

Subsampling experiment summary.

Interpret carefully as a practical recovery experiment in this dataset, not a universal minimum-data threshold.

### `paper_ready_temporal_stability_summary.csv`

Compact temporal stability summary prepared for paper-style reporting.

## `results/network_validation/`

### `network_science_summary_202209.md`

Narrative summary of the network-validation analysis for the 202209 snapshot.

### `cluster_network_metrics_202209.csv`

Cluster-level network metrics.

Use this to support claims about hub-like, bridge-like, receiver-oriented, and baseline roles.

### `cluster_adjacency_values_202209.csv`

Role-to-role interaction values.

Use this to show that role interactions are structured rather than evenly/randomly distributed.

## `results/temporal_analysis/`

### `transitional_scientific_report.md`

Main temporal-analysis narrative.

Use this when explaining monthly behavioural states, transition probabilities, and persistence.

### `overall_transition_probability_matrix.csv`

Matrix showing probabilities of moving from one role to another.

Rows are current states and columns are next states.

### `state_transition_stability.csv`

State-level persistence summary.

Use this to identify which roles are most or least persistent over time.

## `results/k5_academic_strengthening/`

### `k5_academic_strengthening_report.md`

Main report for the final K5 strengthening pass.

It combines per-cluster stability, consensus/co-membership stability, wallet trajectory types, centroid drift, and the final K5 role interpretation table.

### `per_cluster_stability_table.csv`

Role-level table combining wallet share, seed/subsample recovery, temporal persistence, centroid drift, dominant trajectory type, network position, reliability summary, and cautions.

Use this table when explaining which K5 roles are more reliable and which need careful wording.

### `sampled_pair_comembership_consensus.csv`

Consensus/co-membership result from rerunning KMeans on a stratified wallet sample.

Use this to show whether wallets assigned to the same reference role tend to remain grouped together across reruns.

### `trajectory_type_summary.csv`

Summary of wallet-level monthly trajectory types, such as persistent wallets, returners, one-time switchers, and volatile switchers.

Use this to explain the temporal contribution in plain language.

### `centroid_drift_summary_by_cluster.csv`

Cluster-level summary of monthly centroid drift.

Use this to show whether each monthly role keeps the same feature meaning as its full-year prototype.

### `final_k5_role_interpretation_table.csv`

Paper-ready role table for the K5 taxonomy.

Use this as the main table for describing the five EOA behavioural roles.

## `results/temporal_signal_analysis/`

### `temporal_signal_analysis_report.md`

Main report for the next-stage temporal signal analysis.

It explains the four-part extension: wavelength/spectrum clustering, frequency-domain analysis, time-domain temporal signatures, and network-science validation.

### `wallet_frequency_domain_features.csv`

Wallet-level spectral features extracted from daily transaction-count and total-flow signals.

Use this for the wavelength/spectrum-based clustering argument.

### `wallet_time_domain_features.csv`

Wallet-level time-domain features such as active days, burstiness, active/inactive switching, longest active streak, longest inactive gap, and weekly change intensity.

Use this for the temporal signature analysis.

### `temporal_signal_cluster_assignments.csv`

Sample wallet assignments for K5, wavelength/spectral clusters, and time-domain clusters.

Use this to compare the static K5 taxonomy against signal-derived taxonomies.

### `signal_cluster_correspondence_summary.csv`

ARI/NMI comparison between K5, wavelength/spectral clusters, and time-domain clusters.

The first result shows low agreement between signal clusters and K5, suggesting temporal signals capture a different behavioural dimension.

### `network_signal_cluster_null_tests.csv`

First-pass network-science null tests for signal clusters.

In the current 5,000-wallet sample, this test is underpowered because too few sampled transaction edges connect two signal-sampled wallets. Treat it as a pipeline proof-of-concept, not a final network result.

### `signal_cluster_validation_summary.csv`

Silhouette, shuffled-label null, and seed-stability diagnostics for wavelength/spectral clusters and time-domain clusters.

Use this for the academic argument that the signal clusters have measurable structure beyond random labels.

### `wavelength_cluster_interpretive_labels.csv`

Simple labels for wavelength/spectral clusters based on dominant frequency-band evidence.

### `time_domain_cluster_interpretive_labels.csv`

Simple labels for time-domain clusters based on active days, burstiness, streaks, inactive gaps, and switching.

## `results/temporal_signal_analysis_edge_sample/`

Edge-aware version of the temporal signal analysis.

This uses 5,000 EOA wallets sampled from transaction-edge endpoints, balanced across K5 where possible. This folder is the stronger version for network-science discussion because the September edge test has many usable sample-internal edges.

The key files mirror `results/temporal_signal_analysis/`, with the same report, feature, validation, network-null, adjacency, and figure outputs.

### `figures/frequency_power_by_k5_role.png`

Frequency-domain plot with frequency on the x-axis and mean spectral power on the y-axis, grouped by K5 role.

### `figures/frequency_power_by_wavelength_cluster.png`

Frequency-domain plot grouped by wavelength/spectral cluster.

### `figures/flow_frequency_power_by_wavelength_cluster.png`

Frequency-domain plot based on total-flow signal spectra, grouped by wavelength/spectral cluster.

## `results/subcluster_analysis/`

### `cluster_behavior_subcluster_report.md`

Narrative summary of within-role subcluster analysis.

### `subcluster_summary.csv`

Compact subcluster diagnostics.

Use this to explain that KMeans6 gives the broad role layer, while subclusters show finer internal structure.

## `reports/`

### `final_report.docx`

Latest full-length final report produced from the project materials.

## `presentations/`

### `final_project_presentation.pdf`

Final presentation PDF.

### `final_project_presentation.pptx`

Editable PowerPoint version of the final presentation.
