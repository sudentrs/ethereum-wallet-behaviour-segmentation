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

