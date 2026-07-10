# Script Index

This index explains the curated scripts copied into `src/`.

Some scripts were renamed in the curated repo to make their purpose clearer.

## Data Preparation

### `src/data_preparation/extract_erc20_tsv_to_parquet.py`

Reads a raw monthly ERC-20 TSV file in chunks, cleans timestamps/numeric columns, normalizes token values by token decimals, and writes cleaned parquet chunks.

Example:

`python src/data_preparation/extract_erc20_tsv_to_parquet.py --input-tsv data/raw/202211.tsv --output-dir data/interim/erc20_parquet/202211`

Original location:

`202211.tsv/tsv_extract.py`

### `src/data_preparation/reformat_tsv_to_wallet_direction_rows.py`

Converts transaction rows into wallet-direction rows.

For each transfer, it creates:

- sender as `direction = out`
- recipient as `direction = in`

Original location:

`dataverse_files/reformat.py`

Example:

`python src/data_preparation/reformat_tsv_to_wallet_direction_rows.py --input-tsv data/raw/202211.tsv --output-csv data/interim/wallet_202211.csv`

### `src/data_preparation/aggregate_wallet_daily_flows.py`

Aggregates wallet-direction rows into wallet-day totals:

- `total_in`
- `total_out`
- `tx_count`

Original location:

`dataverse_files/daily.py`

Example:

`python src/data_preparation/aggregate_wallet_daily_flows.py --input-glob "data/interim/wallet_2022*.csv" --output-dir data/processed/wallet_daily`

### `src/data_preparation/merge_monthly_daily_wallet_files.py`

Merges monthly wallet-daily files into one yearly wallet-daily file.

Original location:

`dataverse_files/merge.py`

Example:

`python src/data_preparation/merge_monthly_daily_wallet_files.py --input-glob "data/processed/wallet_daily/*_daily.csv" --output-csv data/processed/wallet_daily_2022.csv`

### `src/data_preparation/add_wallet_daily_netflow.py`

Adds `net_flow = total_in - total_out` to the merged wallet-daily table.

Original location:

`dataverse_files/netflow.py`

Example:

`python src/data_preparation/add_wallet_daily_netflow.py --input-csv data/processed/wallet_daily_2022.csv --output-csv data/processed/wallet_daily_2022_netflow.csv`

### `src/data_preparation/build_early_wallet_behavior_features.py`

Builds the earlier wallet-level behaviour feature table from the merged wallet-daily data.

This was part of the initial feature-engineering branch before the expanded KMeans6 feature pipeline.

Original location:

`dataverse_files/features.py`

Example:

`python src/data_preparation/build_early_wallet_behavior_features.py --input-csv data/processed/wallet_daily_2022_netflow.csv --output-csv data/processed/wallet_behavior_features.csv`

### `src/data_preparation/legacy_event_helpers/build_event_window_wallet_features.py`

Builds event-window wallet features around a specific event date.

This belongs to the earlier event-analysis/WETH branch.

Original location:

`202211.tsv/divide_revised.py`

### `src/data_preparation/legacy_event_helpers/build_rolling_weth_window_features.py`

Builds rolling-window WETH features such as signed turnover, magnitudo, and max exposure.

This belongs to the earlier WETH/event-analysis branch.

Original location:

`202211.tsv/feature_extract.py`

### `src/data_preparation/legacy_event_helpers/build_sept_nov_features.py`

Builds September-November features for the 2022 event-analysis branch.

Original location:

`202211.tsv/sept-nov_features.py`

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

### `src/validation/eoa_contract_contamination_check.py`

Classifies sampled cluster addresses as EOAs or contracts using `eth_getCode`.

This supports the Gate 1 contamination check requested for publication work.

Example:

`python src/validation/eoa_contract_contamination_check.py --labels-csv ../dataverse_files/wallet_kmeans6_expanded_daily_features.csv --sample-per-cluster 1000`

Provide the RPC URL with `--rpc-url` or through the `ETH_RPC_URL` environment variable.

### `src/validation/cluster_behavior_subcluster_analysis.py`

Checks whether each top-level behavioural role contains smaller internal subgroups.

Original location:

`dataverse_files/cluster_behavior_subcluster_analysis.py`

## Reporting

### `src/reporting/build_cluster_stability_complete_report.py`

Builds a detailed report document focused on completed findings and paper-process validation.

### `src/reporting/build_final_report.py`

Builds the earlier final report artifact.

This is included because other report-building scripts import helper content from it.

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
