# Analysis Pipeline

This file explains the analysis flow and where the main scripts fit.

The scripts were originally developed during exploration, so some file paths may need adjustment before fully rerunning from a clean machine.

## Stage 0: Raw TSV Extraction And Daily Wallet Tables

Purpose:

Convert raw monthly Ethereum TSV files into smaller cleaned formats and wallet-day flow tables.

This is the missing first step before feature engineering.

Main scripts:

- `src/data_preparation/extract_erc20_tsv_to_parquet.py`
- `src/data_preparation/reformat_tsv_to_wallet_direction_rows.py`
- `src/data_preparation/aggregate_wallet_daily_flows.py`
- `src/data_preparation/merge_monthly_daily_wallet_files.py`
- `src/data_preparation/add_wallet_daily_netflow.py`
- `src/data_preparation/build_early_wallet_behavior_features.py`

Typical outputs:

- Cleaned parquet chunks from raw ERC-20 TSVs.
- Wallet-direction CSVs with one row for sender/outflow and one row for recipient/inflow.
- Monthly wallet-daily flow tables.
- Merged yearly wallet-daily table.
- Wallet-daily table with net flow.
- Early wallet-level behaviour features.

Important original outputs in the working directory:

- `202211.tsv/processed/202211/part_*.parquet`
- `dataverse_files/wallet_2022*.csv`
- `dataverse_files/wallet_daily_2022*.csv`
- `dataverse_files/wallet_daily_2022.csv`
- `dataverse_files/wallet_daily_2022_netflow.csv`
- `dataverse_files/wallet_behavior_features.csv`

Notes:

Some of these scripts still contain local hard-coded paths from the original exploratory work.

Before rerunning them from a clean clone, update paths or convert them to command-line arguments.

The scripts under `src/data_preparation/legacy_event_helpers/` belong to the earlier WETH/event-analysis branch and are included for completeness, not as the main KMeans6 pipeline.

Example commands:

```powershell
python src/data_preparation/extract_erc20_tsv_to_parquet.py `
  --input-tsv data/raw/202211.tsv `
  --output-dir data/interim/erc20_parquet/202211

python src/data_preparation/reformat_tsv_to_wallet_direction_rows.py `
  --input-tsv data/raw/202211.tsv `
  --output-csv data/interim/wallet_202211.csv

python src/data_preparation/aggregate_wallet_daily_flows.py `
  --input-glob "data/interim/wallet_2022*.csv" `
  --output-dir data/processed/wallet_daily

python src/data_preparation/merge_monthly_daily_wallet_files.py `
  --input-glob "data/processed/wallet_daily/*_daily.csv" `
  --output-csv data/processed/wallet_daily_2022.csv

python src/data_preparation/add_wallet_daily_netflow.py `
  --input-csv data/processed/wallet_daily_2022.csv `
  --output-csv data/processed/wallet_daily_2022_netflow.csv

python src/data_preparation/build_early_wallet_behavior_features.py `
  --input-csv data/processed/wallet_daily_2022_netflow.csv `
  --output-csv data/processed/wallet_behavior_features.csv
```

## Stage 1: Wallet Features And Scaling

Purpose:

Convert raw/daily Ethereum transaction files into wallet-level behavioural features.

Main scripts:

- `src/data_preparation/*`
- `src/features/build_original_feature_dataset.py`
- `src/features/scale_original_features.py`
- `src/features/build_full_kmeans6_expanded_features.py`
- `src/features/robust_scale_expanded_features.py`

Typical outputs:

- Wallet feature CSV files.
- Robust-scaled feature CSV files.
- Scaling statistics.

Important original outputs in the working directory:

- `dataverse_files/wallet_kmeans6_expanded_daily_features.csv`
- `dataverse_files/wallet_kmeans6_expanded_daily_features_robust_scaled.csv`
- `dataverse_files/wallet_kmeans6_expanded_daily_features_robust_scaled_scaling_stats.csv`

Example commands:

```powershell
python src/features/build_full_kmeans6_expanded_features.py --help
python src/features/robust_scale_expanded_features.py --help
```

These feature scripts already expose command-line options in the curated repo.

## Stage 2: Clustering And Cluster Correspondence

Purpose:

Cluster wallet behaviour and compare cluster solutions across feature sets or analysis variants.

Main scripts:

- `src/clustering/compare_cluster_assignments.py`
- `src/clustering/compare_cluster_profiles_by_distance.py`

Typical outputs:

- Cluster crosstabs.
- Best-match tables.
- Distance matrices.
- Distance-based cluster correspondence summaries.

Important result files:

- `results/paper_process/formal_cluster_correspondence_definition.md`
- `results/paper_process/cross_dataset_bipartite_matching_pairs.csv`

## Stage 3: Network Validation

Purpose:

Check whether feature-based behavioural roles align with transaction-network structure.

Main scripts:

- `src/network/network_science_cluster_analysis.py`
- `src/network/broad_network_science_analysis.py`

Typical outputs:

- Role-to-role adjacency matrices.
- Network modularity/assortativity metrics.
- Cluster-level centrality summaries.
- Random-label comparison results.

Important result files:

- `results/network_validation/network_science_summary_202209.md`
- `results/network_validation/cluster_network_metrics_202209.csv`
- `results/network_validation/cluster_adjacency_values_202209.csv`

## Stage 4: Temporal Transition Analysis

Purpose:

Assign wallets to monthly behavioural states and measure persistence, transitions, and role movement.

Main script:

- `src/temporal/cluster_transition_analysis.py`

Typical outputs:

- Monthly wallet-state table.
- Transition count matrix.
- Transition probability matrix.
- State-retention summaries.
- Temporal scientific report.

Important result files:

- `results/temporal_analysis/transitional_scientific_report.md`
- `results/temporal_analysis/overall_transition_probability_matrix.csv`
- `results/temporal_analysis/state_transition_stability.csv`

Important finding:

Monthly behaviour is moderately persistent, not completely fixed and not random.

## Stage 5: Paper-Focused Validation

Purpose:

Add stronger validation for an academic paper-style presentation of the work.

Main script:

- `src/validation/run_paper_process_remaining_analyses.py`

Typical outputs:

- Cross-dataset permutation test.
- Cross-feature-set Spearman correlation.
- Formal cluster correspondence rules.
- Minimum observation experiment.
- Paper-ready temporal summaries.

Important result files:

- `results/paper_process/paper_process_status_after_run.md`
- `results/paper_process/cross_dataset_correspondence_permutation_summary.csv`
- `results/paper_process/cross_feature_set_spearman_summary.csv`
- `results/paper_process/minimum_observation_experiment_summary.csv`

## Stage 6: Within-Cluster Subcluster Analysis

Purpose:

Check whether each top-level role contains meaningful finer subgroups.

Main script:

- `src/validation/cluster_behavior_subcluster_analysis.py`

Typical outputs:

- Per-cluster subcluster diagnostics.
- Subcluster feature profiles.
- Pairwise tests.
- PCA/heatmap figures.

Important result files:

- `results/subcluster_analysis/cluster_behavior_subcluster_report.md`
- `results/subcluster_analysis/subcluster_summary.csv`

## Stage 7: Reporting

Purpose:

Generate final report artifacts from analysis outputs.

Main scripts:

- `src/reporting/build_cluster_stability_complete_report.py`
- `src/reporting/build_full_length_template_integrated_report.py`

Main final artifacts:

- `reports/final_report.docx`
- `presentations/final_project_presentation.pdf`
- `presentations/final_project_presentation.pptx`
