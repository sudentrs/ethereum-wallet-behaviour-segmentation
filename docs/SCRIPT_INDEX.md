# Script Index

This index explains the curated scripts copied into `src/`.

Some scripts were renamed in the curated repo to make their purpose clearer.

## Feature Engineering

### `src/features/build_original_feature_dataset.py`

Original feature-building script from the earlier clustering workflow.

Use for the first feature-set version.

Original location:

`clustering/build_feature_dataset.py`

### `src/features/scale_original_features.py`

Scales the original feature set.

Original location:

`clustering/scale.py`

### `src/features/build_full_kmeans6_expanded_features.py`

Builds expanded daily wallet features for the KMeans6 analysis.

This script aggregates daily wallet activity into richer wallet-level features such as activity persistence, value flow, directionality, volatility, and concentration.

Original location:

`dataverse_files/build_full_kmeans6_expanded_features.py`

### `src/features/robust_scale_expanded_features.py`

Applies robust scaling/transforms to the expanded feature set.

Original location:

`dataverse_files/robust_scale_expanded_features.py`

## Clustering And Correspondence

### `src/clustering/compare_cluster_assignments.py`

Compares cluster assignments across two clustering outputs.

Useful for crosstabs and best-match tables.

Original location:

`clustering/compare.py`

### `src/clustering/compare_cluster_profiles_by_distance.py`

Compares cluster profiles using multiple distance metrics.

This supports the formal cross-analysis correspondence argument.

Original location:

`clustering/distance.py`

## Network Validation

### `src/network/network_science_cluster_analysis.py`

Runs network-science validation for a specific monthly clustering output.

Outputs include role interaction matrices, network metrics, statistical tests, and summary notes.

Original location:

`clustering/network_science_cluster_analysis.py`

### `src/network/broad_network_science_analysis.py`

Broader network-science analysis for the KMeans6 expanded-feature workflow.

Original location:

`dataverse_files/broad_network_science_analysis.py`

## Temporal Analysis

### `src/temporal/cluster_transition_analysis.py`

Assigns wallets to monthly behavioural states and computes transition matrices.

This is the main script for persistence, role movement, and temporal stability.

Original location:

`dataverse_files/cluster_transition_analysis.py`

## Validation And Robustness

### `src/validation/run_paper_process_remaining_analyses.py`

Runs the paper-focused validation analyses:

- Cross-dataset correspondence permutation test.
- Formal correspondence summary.
- Paper-ready temporal summaries.
- Cross-feature-set Spearman correlation.
- Minimum observation/subsampling experiment.

Original location:

`run_paper_process_remaining_analyses.py`

### `src/validation/cluster_behavior_subcluster_analysis.py`

Checks whether each top-level behavioural role contains smaller internal subgroups.

Original location:

`dataverse_files/cluster_behavior_subcluster_analysis.py`

## Reporting

### `src/reporting/build_cluster_stability_complete_report.py`

Builds a detailed report document focused on completed findings and paper-process validation.

### `src/reporting/build_full_length_template_integrated_report.py`

Builds the full-length final report following the final-report template structure.

## Archive Scripts Not Included In `src/`

The original workspace also contains earlier exploratory scripts for:

- Insider detection.
- FTX/Luna event analysis.
- HDBSCAN experiments.
- UMAP plots.
- Early screenshots and quick checks.
- Multiple older report/presentation versions.

Those are useful as historical work, but they are not part of the final clean research pipeline.

