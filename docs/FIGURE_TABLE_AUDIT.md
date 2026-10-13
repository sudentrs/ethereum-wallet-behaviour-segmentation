# Figure And Table Reproducibility Audit

This audit tracks which scripts regenerate each figure/table used in the paper draft and reproducible analysis package.

Status values:

- `Regenerable`: script and input path are known.
- `Partially regenerable`: script exists, but paths/config need cleanup.
- `Static artifact`: final document/slide artifact copied into repo.
- `Needs audit`: included in a document but not yet mapped to a script.

| Figure/Table | File In Repo Or Original Workspace | Script That Generates It | Input Data | Status |
|---|---|---|---|---|
| Cross-dataset permutation summary | `results/paper_process/cross_dataset_correspondence_permutation_summary.csv` | `src/validation/run_paper_process_remaining_analyses.py` | `clustering/202209/merged_cluster_labels_202209.csv` | Regenerable |
| Bipartite cluster matching pairs | `results/paper_process/cross_dataset_bipartite_matching_pairs.csv` | `src/validation/run_paper_process_remaining_analyses.py` | `clustering/202209/merged_cluster_labels_202209.csv` | Regenerable |
| Cross-feature Spearman summary | `results/paper_process/cross_feature_set_spearman_summary.csv` | `src/validation/run_paper_process_remaining_analyses.py` | Original and expanded feature tables | Partially regenerable |
| Minimum observation experiment summary | `results/paper_process/minimum_observation_experiment_summary.csv` | `src/validation/run_paper_process_remaining_analyses.py` | Sparse interval feature/label data | Partially regenerable |
| Paper-ready temporal stability summary | `results/paper_process/paper_ready_temporal_stability_summary.csv` | `src/validation/run_paper_process_remaining_analyses.py` | Monthly wallet-state transition outputs | Regenerable |
| Network-science summary | `results/network_validation/network_science_summary_202209.md` | `src/network/network_science_cluster_analysis.py` | September 2022 cluster labels and transaction data | Partially regenerable |
| Cluster network metrics | `results/network_validation/cluster_network_metrics_202209.csv` | `src/network/network_science_cluster_analysis.py` | September 2022 cluster labels and transaction data | Partially regenerable |
| Cluster adjacency values | `results/network_validation/cluster_adjacency_values_202209.csv` | `src/network/network_science_cluster_analysis.py` | September 2022 cluster labels and transaction data | Partially regenerable |
| Temporal transition probability matrix | `results/temporal_analysis/overall_transition_probability_matrix.csv` | `src/temporal/cluster_transition_analysis.py` | Monthly daily wallet data, scaling stats, KMeans6 centroids | Partially regenerable |
| State transition stability | `results/temporal_analysis/state_transition_stability.csv` | `src/temporal/cluster_transition_analysis.py` | Monthly wallet-state assignments | Regenerable |
| Temporal scientific report | `results/temporal_analysis/transitional_scientific_report.md` | `src/temporal/cluster_transition_analysis.py` | Monthly transition outputs | Regenerable |
| K5 academic strengthening report | `results/k5_academic_strengthening/k5_academic_strengthening_report.md` | `src/validation/build_k5_academic_strengthening_pack.py` | EOA K5 labels, robust-scaled features, monthly wallet states, daily wallet files, K5 network/temporal outputs | Regenerable |
| K5 per-cluster stability table | `results/k5_academic_strengthening/per_cluster_stability_table.csv` | `src/validation/build_k5_academic_strengthening_pack.py` | K5 role labels, consensus recovery, temporal stability, centroid drift, network centrality | Regenerable |
| K5 final role interpretation table | `results/k5_academic_strengthening/final_k5_role_interpretation_table.csv` | `src/validation/build_k5_academic_strengthening_pack.py` | K5 role labels, temporal stability, network centrality, consensus recovery, centroid drift, trajectory summaries | Regenerable |
| K5 co-membership consensus table | `results/k5_academic_strengthening/sampled_pair_comembership_consensus.csv` | `src/validation/build_k5_academic_strengthening_pack.py` | Stratified sample from robust-scaled EOA feature table and K5 labels | Regenerable |
| K5 co-membership consensus figure | `results/k5_academic_strengthening/consensus_comembership_by_cluster.png` | `src/validation/build_k5_academic_strengthening_pack.py` | `results/k5_academic_strengthening/sampled_pair_comembership_consensus.csv` | Regenerable |
| K5 trajectory type summary | `results/k5_academic_strengthening/trajectory_type_summary.csv` | `src/validation/build_k5_academic_strengthening_pack.py` | `results/eoa_only_kmeans5/temporal_validation/wallet_monthly_behavior_states.csv` | Regenerable |
| K5 trajectory type figure | `results/k5_academic_strengthening/trajectory_type_shares.png` | `src/validation/build_k5_academic_strengthening_pack.py` | `results/k5_academic_strengthening/trajectory_type_summary.csv` | Regenerable |
| K5 centroid drift summary | `results/k5_academic_strengthening/centroid_drift_summary_by_cluster.csv` | `src/validation/build_k5_academic_strengthening_pack.py` | Full-year K5 centroids, scaling stats, monthly daily wallet files, monthly state assignments | Regenerable |
| K5 centroid drift figure | `results/k5_academic_strengthening/monthly_centroid_drift.png` | `src/validation/build_k5_academic_strengthening_pack.py` | `results/k5_academic_strengthening/monthly_centroid_drift.csv` | Regenerable |
| Temporal signal analysis report | `results/temporal_signal_analysis/temporal_signal_analysis_report.md` | `src/validation/build_temporal_signal_analysis_pack.py` | K5 labels, 2022 wallet-daily files, sampled September transaction edges | Regenerable |
| Frequency-domain wallet features | `results/temporal_signal_analysis/wallet_frequency_domain_features.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | Daily transaction-count and total-flow signals for sampled wallets | Regenerable |
| Time-domain wallet features | `results/temporal_signal_analysis/wallet_time_domain_features.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | Daily transaction-count, total-flow, and net-flow signals for sampled wallets | Regenerable |
| Signal-cluster correspondence summary | `results/temporal_signal_analysis/signal_cluster_correspondence_summary.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | K5 labels, wavelength/spectral clusters, time-domain clusters | Regenerable |
| Signal-cluster validation summary | `results/temporal_signal_analysis/signal_cluster_validation_summary.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | Frequency-domain features, time-domain features, signal-cluster labels | Regenerable |
| Signal-cluster interpretive labels | `results/temporal_signal_analysis/wavelength_cluster_interpretive_labels.csv` and `results/temporal_signal_analysis/time_domain_cluster_interpretive_labels.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | Signal-cluster profiles | Regenerable |
| Signal-cluster network null tests | `results/temporal_signal_analysis/network_signal_cluster_null_tests.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | Sampled September transaction edges and signal-cluster assignments | Regenerable / underpowered in first sample |
| Edge-aware temporal signal report | `results/temporal_signal_analysis_edge_sample/temporal_signal_analysis_report.md` | `src/validation/build_temporal_signal_analysis_pack.py` | K5 labels, 2022 wallet-daily files, sampled September transaction edges | Regenerable |
| Edge-aware signal validation summary | `results/temporal_signal_analysis_edge_sample/signal_cluster_validation_summary.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | Edge-aware wallet sample, frequency-domain features, time-domain features, signal-cluster labels | Regenerable |
| Edge-aware signal network null tests | `results/temporal_signal_analysis_edge_sample/network_signal_cluster_null_tests.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | Edge-aware wallet sample and sampled September transaction edges | Regenerable |
| Edge-aware signal adjacency matrices | `results/temporal_signal_analysis_edge_sample/k5_cluster_edge_adjacency_counts.csv`, `results/temporal_signal_analysis_edge_sample/wavelength_cluster_edge_adjacency_counts.csv`, and `results/temporal_signal_analysis_edge_sample/time_domain_cluster_edge_adjacency_counts.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | Edge-aware wallet sample and sampled September transaction edges | Regenerable |
| Larger edge-aware temporal signal report | `results/temporal_signal_analysis_edge_sample_10k/temporal_signal_analysis_report.md` | `src/validation/build_temporal_signal_analysis_pack.py` | K5 labels, 2022 wallet-daily files, sampled September transaction edges | Regenerable |
| Larger edge-aware signal validation summary | `results/temporal_signal_analysis_edge_sample_10k/signal_cluster_validation_summary.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | 10,000-wallet edge-aware sample, frequency-domain features, time-domain features, signal-cluster labels | Regenerable |
| Larger edge-aware signal network null tests | `results/temporal_signal_analysis_edge_sample_10k/network_signal_cluster_null_tests.csv` | `src/validation/build_temporal_signal_analysis_pack.py` | 10,000-wallet edge-aware sample and sampled September transaction edges | Regenerable |
| K-taxonomy signal correspondence | `results/temporal_signal_k_taxonomy_comparison/k_taxonomy_signal_correspondence.csv` | `src/validation/build_temporal_signal_k_taxonomy_comparison.py` | 10,000-wallet signal assignments and K4/K5/K6 label files | Regenerable |
| K-taxonomy signal network null tests | `results/temporal_signal_k_taxonomy_comparison/k_taxonomy_signal_network_null_tests.csv` | `src/validation/build_temporal_signal_k_taxonomy_comparison.py` | 10,000-wallet signal assignments, K4/K5/K6 labels, sampled September transaction edges | Regenerable |
| Paper-ready temporal signal section | `results/temporal_signal_k_taxonomy_comparison/paper_ready_temporal_signal_section.md` | `src/reporting/build_temporal_signal_paper_section.py` | 10,000-wallet signal outputs, K-taxonomy comparison, event-adjacent tests, two-step return tests | Regenerable |
| Overleaf paper source | `overleaf/main.tex` | Manual paper assembly from audited result tables and copied figures | Current K4/K5/K6 EOA-only outputs | Static source / figure paths checked |
| Frequency plot by K5 role | `results/temporal_signal_analysis/figures/frequency_power_by_k5_role.png` | `src/validation/build_temporal_signal_analysis_pack.py` | Normalized FFT power from daily transaction-count signals | Regenerable |
| Frequency plot by wavelength cluster | `results/temporal_signal_analysis/figures/frequency_power_by_wavelength_cluster.png` | `src/validation/build_temporal_signal_analysis_pack.py` | Normalized FFT power and wavelength/spectral cluster labels | Regenerable |
| Flow-frequency plot by wavelength cluster | `results/temporal_signal_analysis/figures/flow_frequency_power_by_wavelength_cluster.png` | `src/validation/build_temporal_signal_analysis_pack.py` | Normalized FFT power from daily total-flow signals | Regenerable |
| Subcluster summary | `results/subcluster_analysis/subcluster_summary.csv` | `src/validation/cluster_behavior_subcluster_analysis.py` | Expanded KMeans6 feature table and labels | Partially regenerable |
| Subcluster report | `results/subcluster_analysis/cluster_behavior_subcluster_report.md` | `src/validation/cluster_behavior_subcluster_analysis.py` | Subcluster outputs | Regenerable |

## Open Audit Items

The following should be checked before any publication submission:

- Every figure embedded in `overleaf/main.tex`.
- Any manually copied value in paper text.
- Any value that came from an older run before the post-Gate-1 pipeline.

## Rule For Future Submissions

No figure, table, or numerical claim should be used in a submission unless it is tied to:

1. a script,
2. an input dataset,
3. an output file,
4. and a tagged Git commit.
