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
- `src/network/eoa_k5_transaction_network_validation.py`

Typical outputs:

- Role-to-role adjacency matrices.
- Network modularity/assortativity metrics.
- Cluster-level centrality summaries.
- Random-label comparison results.

Important result files:

- `results/network_validation/network_science_summary_202209.md`
- `results/network_validation/cluster_network_metrics_202209.csv`
- `results/network_validation/cluster_adjacency_values_202209.csv`
- `results/eoa_only_kmeans5/network_validation/eoa_k5_transaction_network_validation_report.md`

EOA-only K5 note:

The K5 transaction-network validation is a downstream check of the post-Gate-1 taxonomy. It processed September 2022 raw transactions and found mixed network evidence: role-to-role flows are structured, but the same-cluster random-label null test did not support stronger within-role concentration than shuffled labels.

## Stage 4: Temporal Transition Analysis

Purpose:

Assign wallets to monthly behavioural states and measure persistence, transitions, and role movement.

Main script:

- `src/temporal/cluster_transition_analysis.py`
- `src/temporal/eoa_k5_temporal_validation.py`

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
- `results/eoa_only_kmeans5/temporal_validation/eoa_k5_temporal_validation_report.md`
- `results/eoa_only_kmeans5/temporal_validation/two_step_return_analysis.csv`

Important finding:

Monthly behaviour is moderately persistent, not completely fixed and not random.

EOA-only K5 note:

The K5 temporal validation assigns each wallet-month to the nearest K5 prototype and measures month-to-month movement. It also includes a two-step return analysis, which checks whether wallets that leave a behavioural state return to it in the following month.

## Stage 5: Paper-Focused Validation

Purpose:

Add stronger validation for an academic paper-style presentation of the work.

Main script:

- `src/validation/run_paper_process_remaining_analyses.py`
- `src/validation/build_academic_temporal_pack.py`
- `src/validation/feature_space_proofs_k4_k5_k6.py`
- `src/validation/build_k5_academic_strengthening_pack.py`

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
- `results/academic_paper_pack/paper_ready_synthesis.md`
- `results/academic_paper_pack/academic_temporal_validation_pack.md`
- `results/academic_paper_pack/feature_space_proofs/feature_space_proofs_report.md`
- `results/k5_academic_strengthening/k5_academic_strengthening_report.md`
- `results/k5_academic_strengthening/final_k5_role_interpretation_table.csv`

EOA paper-pack note:

The academic paper pack reproduces the earlier six-cluster proof style for the EOA-only K4/K5/K6 branch. It includes feature-space KNN network quality, global and pairwise feature-separation tests, transition matrices, transition residuals, event-adjacent rank tests, and two-step return null tests. Event-month interpretation is contextual only and should not be presented as causal evidence without a separate event-study design.

K5 strengthening note:

The K5 academic-strengthening pack addresses the remaining paper-readiness questions after model selection. It adds per-cluster stability, consensus/co-membership stability, trajectory-type summaries, centroid drift, and a consolidated role interpretation table. This is the best folder to use when explaining which K5 roles are reliable, which are fragile, and how wallet behaviour changes over time.

## Stage 6: Temporal Signal Analysis

Purpose:

Extend the EOA wallet study from static aggregate clustering to temporal signal-based wallet profiling.

Main script:

- `src/validation/build_temporal_signal_analysis_pack.py`

Typical outputs:

- Wavelength/spectrum-based clusters.
- Frequency-domain feature tables and plots with frequency on the x-axis.
- Time-domain burst/gap/streak features.
- Signal-cluster correspondence tests against K5.
- Network-science null tests for signal clusters.
- Signal-cluster validation summaries and interpretive label tables.

Important result files:

- `results/temporal_signal_analysis/temporal_signal_analysis_report.md`
- `results/temporal_signal_analysis/wallet_frequency_domain_features.csv`
- `results/temporal_signal_analysis/wallet_time_domain_features.csv`
- `results/temporal_signal_analysis/signal_cluster_correspondence_summary.csv`
- `results/temporal_signal_analysis/signal_cluster_validation_summary.csv`
- `results/temporal_signal_analysis/network_signal_cluster_null_tests.csv`
- `results/temporal_signal_analysis/figures/frequency_power_by_k5_role.png`
- `results/temporal_signal_analysis/figures/frequency_power_by_wavelength_cluster.png`
- `results/temporal_signal_analysis_edge_sample/temporal_signal_analysis_report.md`
- `results/temporal_signal_analysis_edge_sample/network_signal_cluster_null_tests.csv`
- `results/temporal_signal_analysis_edge_sample/signal_cluster_validation_summary.csv`
- `results/temporal_signal_analysis_edge_sample_10k/temporal_signal_analysis_report.md`
- `results/temporal_signal_k_taxonomy_comparison/temporal_signal_k_taxonomy_comparison_report.md`
- `results/temporal_signal_k_taxonomy_comparison/paper_ready_temporal_signal_section.md`

Academic note:

This stage is exploratory and should be described as temporal signal-based profiling. The original run uses a stratified 5,000-wallet sample. The edge-aware run uses 5,000 wallets selected from sampled transaction-edge endpoints so the network-science null test has enough usable edges. The spectral and time-domain clusters do not simply reproduce K5, suggesting they capture different behavioural dimensions. The edge-aware network check gives stronger evidence than the first stratified run, but it should still be described as sample-based network validation rather than a full-population network claim.

Example commands:

- Stratified exploratory run: `python src/validation/build_temporal_signal_analysis_pack.py`
- Edge-aware network run: `python src/validation/build_temporal_signal_analysis_pack.py --out-dir results/temporal_signal_analysis_edge_sample --sample-mode edge --edge-wallet-limit 5000 --force-rebuild-sample --permutations 100`
- Larger edge-aware run: `python src/validation/build_temporal_signal_analysis_pack.py --out-dir results/temporal_signal_analysis_edge_sample_10k --sample-mode edge --edge-wallet-limit 10000 --force-rebuild-sample --permutations 100 --max-silhouette-sample 3000`
- K-taxonomy signal comparison: `python src/validation/build_temporal_signal_k_taxonomy_comparison.py`
- Paper-ready temporal signal section: `python src/reporting/build_temporal_signal_paper_section.py`

## Stage 7: Within-Cluster Subcluster Analysis

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

## Stage 8: Reporting

Purpose:

Generate final report artifacts from analysis outputs.

Main scripts:

- `src/reporting/build_cluster_stability_complete_report.py`
- `src/reporting/build_full_length_template_integrated_report.py`
- `src/reporting/build_final_academic_deliverable_pack.py`

Main final artifacts:

- `reports/final_report.docx`
- `presentations/final_project_presentation.pdf`
- `presentations/final_project_presentation.pptx`
- `reports/Final_Academic_Project_Report_Ethereum_Wallet_Behaviour.docx`
- `presentations/Final_Academic_Project_Advisor_Deck.pptx`
- `presentations/Final_Academic_Project_Advisor_Deck.pdf`
- `results/final_academic_pack/final_deliverable_manifest.md`
