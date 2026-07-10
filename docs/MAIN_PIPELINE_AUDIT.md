# Main Pipeline Audit

This file lists the main pipeline pieces now included in the curated repository.

## Included

### Raw TSV preparation

- `src/data_preparation/extract_erc20_tsv_to_parquet.py`
- `src/data_preparation/reformat_tsv_to_wallet_direction_rows.py`
- `src/data_preparation/aggregate_wallet_daily_flows.py`
- `src/data_preparation/merge_monthly_daily_wallet_files.py`
- `src/data_preparation/add_wallet_daily_netflow.py`
- `src/data_preparation/build_early_wallet_behavior_features.py`

### Legacy event/WETH branch

- `src/data_preparation/legacy_event_helpers/build_event_window_wallet_features.py`
- `src/data_preparation/legacy_event_helpers/build_rolling_weth_window_features.py`
- `src/data_preparation/legacy_event_helpers/build_sept_nov_features.py`

These are included for project history and reproducibility of older exploratory outputs.

### Feature engineering and scaling

- `src/features/build_original_feature_dataset.py`
- `src/features/scale_original_features.py`
- `src/features/build_full_kmeans6_expanded_features.py`
- `src/features/robust_scale_expanded_features.py`

### Cluster comparison and correspondence

- `src/clustering/compare_cluster_assignments.py`
- `src/clustering/compare_cluster_profiles_by_distance.py`

### Network validation

- `src/network/network_science_cluster_analysis.py`
- `src/network/broad_network_science_analysis.py`

### Temporal analysis

- `src/temporal/cluster_transition_analysis.py`

### Paper-focused validation

- `src/validation/run_paper_process_remaining_analyses.py`
- `src/validation/cluster_behavior_subcluster_analysis.py`

### Reporting

- `src/reporting/build_final_report.py`
- `src/reporting/build_cluster_stability_complete_report.py`
- `src/reporting/build_full_length_template_integrated_report.py`

## Still Not Fully One-Command Reproducible

The repo now contains the main scripts, but several scripts still have local hard-coded paths from the original workspace.

To make the repo fully reproducible, the next cleanup step would be to refactor these scripts so every input and output path is passed through command-line arguments.

## Deliberately Not Included

The following are intentionally excluded from the curated GitHub repo:

- raw `.tsv` and `.tsv.gz` transaction files
- large `.parquet` chunks
- huge intermediate CSVs
- local virtual environments
- temporary document/presentation render folders
- exploratory screenshots
- extracted PDF text from literature review

