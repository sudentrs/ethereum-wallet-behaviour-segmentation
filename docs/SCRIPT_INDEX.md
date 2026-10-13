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

### `src/network/eoa_k5_transaction_network_validation.py`

Runs transaction-network validation for the EOA-only KMeans5 clustering.

It reads the K5 wallet labels and a raw monthly TSV file, then produces role-to-role transaction matrices, cluster centrality summaries, a sampled random-label null test, and a written validation report.

This is the downstream network check for the post-contract-removal K5 branch.

### `scripts/run_monthly_network_null_validation.py`

Repeats the same-role transaction-network null test across monthly ERC-20 transfer files.

It reads an EOA cluster-label file, streams each monthly TSV in chunks, counts labelled role-to-role transfer edges, samples labelled transaction edges, and compares the observed same-role transaction ratio against a shuffled wallet-label null model.

This is the full-year follow-up to the original September-only K5 network validation.

## Temporal Analysis

### `src/temporal/cluster_transition_analysis.py`

Assigns wallets to monthly behavioural states and computes transition matrices.

This is the main script for persistence, role movement, and temporal stability.

Original location:

`dataverse_files/cluster_transition_analysis.py`

### `src/temporal/eoa_k5_temporal_validation.py`

Runs temporal validation for the EOA-only KMeans5 clustering.

It assigns each wallet-month to the nearest K5 full-year prototype, computes monthly transition matrices, state persistence, and two-step return behaviour.

This is the downstream temporal check for the post-contract-removal K5 branch.

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

### `src/validation/compare_eoa_k4_k5_k6_downstream.py`

Builds the side-by-side downstream validation comparison for EOA-only `K=4`, `K=5`, and `K=6`.

It combines cluster sizes, K-sensitivity metrics, transaction-network null tests, temporal persistence, and two-step return analysis into one comparison table and written recommendation.

### `src/validation/build_academic_temporal_pack.py`

Builds paper-ready temporal validation outputs for EOA-only `K=4`, `K=5`, and `K=6`.

It generates monthly state-share event plots, self-transition event-pair plots, transition residual heatmaps, event-adjacent rank tests, top off-diagonal transition pathways, and two-step return null tests.

### `src/validation/feature_space_proofs_k4_k5_k6.py`

Reproduces the earlier six-cluster feature-space proof style for the EOA-only `K=4`, `K=5`, and `K=6` branch.

It runs sampled KNN feature-neighbourhood validation, global Kruskal-Wallis feature-separation tests, and pairwise Mann-Whitney/Cliff's-delta tests.

### `src/validation/build_k5_academic_strengthening_pack.py`

Builds the final K5 paper-strengthening pack.

It adds per-cluster stability, consensus/co-membership stability, wallet trajectory types, monthly centroid drift, and a consolidated K5 role interpretation table.

Main output:

`results/k5_academic_strengthening/k5_academic_strengthening_report.md`

Example:

`python src/validation/build_k5_academic_strengthening_pack.py`

### `src/validation/build_temporal_signal_analysis_pack.py`

Starts the temporal signal-analysis extension of the project.

It builds daily 2022 wallet signals, extracts frequency-domain features, extracts time-domain burst/gap/streak features, clusters signal signatures, compares signal clusters with K5, assigns simple interpretive labels, validates cluster separation/stability, and runs transaction-network null tests.

The default run uses a stratified EOA sample. Use `--sample-mode edge` for the stronger network-science version, which samples wallets from transaction-edge endpoints.

Main output:

`results/temporal_signal_analysis/temporal_signal_analysis_report.md`

Example:

`python src/validation/build_temporal_signal_analysis_pack.py`

Edge-aware example:

`python src/validation/build_temporal_signal_analysis_pack.py --out-dir results/temporal_signal_analysis_edge_sample --sample-mode edge --edge-wallet-limit 5000 --force-rebuild-sample --permutations 100`

Larger edge-aware example:

`python src/validation/build_temporal_signal_analysis_pack.py --out-dir results/temporal_signal_analysis_edge_sample_10k --sample-mode edge --edge-wallet-limit 10000 --force-rebuild-sample --permutations 100 --max-silhouette-sample 3000`

### `src/validation/build_temporal_signal_k_taxonomy_comparison.py`

Compares the temporal signal clusters against K4, K5, and K6 on the same 10,000-wallet edge-aware sample.

It writes correspondence metrics, enrichment tables, network null tests, adjacency matrices, and a short comparison report.

Main output:

`results/temporal_signal_k_taxonomy_comparison/temporal_signal_k_taxonomy_comparison_report.md`

## Reporting

### `src/reporting/build_temporal_signal_paper_section.py`

Builds a paper-ready markdown section from the 10k temporal signal run, the K4/K5/K6 comparison, existing event-adjacent checks, and two-step return tests.

Main output:

`results/temporal_signal_k_taxonomy_comparison/paper_ready_temporal_signal_section.md`

### `src/reporting/build_final_academic_deliverable_pack.py`

Deprecated project-deliverable helper from the class-report phase.

It can still regenerate older Word/PPT artifacts if needed locally, but those generated files are not part of the final paper-focused repository.

Main outputs:

- `results/final_academic_pack/final_deliverable_manifest.md`

### `src/reporting/build_cluster_stability_complete_report.py`

Builds a detailed report document focused on completed findings and paper-process validation.

### `src/reporting/build_final_report.py`

Deprecated helper that builds the earlier class final-report artifact.

This is included because other report-building scripts import helper content from it.

### `src/reporting/build_full_length_template_integrated_report.py`

Deprecated helper that builds the full-length class final report following the final-report template structure.

## Archive Scripts Not Included In `src/`

The original workspace also contains earlier exploratory scripts for:

- Insider detection.
- FTX/Luna event analysis.
- HDBSCAN experiments.
- UMAP plots.
- Early screenshots and quick checks.
- Multiple older report/presentation versions.

Those are useful as historical work, but they are not part of the final clean research pipeline.
