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

These scripts now accept command-line input/output paths and default to predictable `data/interim` and `data/processed` locations.

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
- `src/validation/eoa_contract_contamination_check.py`

### Reporting

- older class-report generation scripts, now removed from the paper-focused repository

## Still Not Fully One-Command Reproducible

The repo now contains the main scripts, and the raw data-preparation layer has been refactored to avoid hard-coded local paths.

Some downstream analysis scripts still came from exploratory work and should be checked before claiming one-command reproducibility.

The next cleanup step would be to create a single driver script or Makefile that runs each stage from `config.example.yaml`.

## Deliberately Not Included

The following are intentionally excluded from the curated GitHub repo:

- raw `.tsv` and `.tsv.gz` transaction files
- large `.parquet` chunks
- huge intermediate CSVs
- local virtual environments
- temporary document/presentation render folders
- exploratory screenshots
- extracted PDF text from literature review
