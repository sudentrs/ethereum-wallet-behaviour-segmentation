# Paper Process Status After Completing Remaining Analyses

## Completed Before This Run

- Four-distance cluster comparison existed for cosine, weighted Euclidean, Mahalanobis, and Wasserstein.
- Hungarian matching existed in the clustering scripts.
- Graph validation existed with modularity, assortativity, intra-cluster edge ratio, and random-label graph testing.
- Temporal transition analysis existed with monthly wallet-state transitions.

## Completed In This Run

### 1. Cross-Dataset Correspondence Permutation Test

Output files:

- `cross_dataset_correspondence_permutation_summary.csv`
- `cross_dataset_correspondence_permutation_null.csv`
- `cross_dataset_correspondence_permutation_null.png`
- `cross_dataset_bipartite_matching_pairs.csv`
- `cross_dataset_cluster_crosstab_counts.csv`

Main result:

- Observed maximum bipartite wallet-label overlap: `0.3952`
- Random-label null mean: `0.2539`
- Empirical right-tail p-value: `0.000999`

Interpretation:

The cross-dataset label alignment is significantly stronger than chance.

However, the wallet-level overlap score is not the same as the earlier distance-metric correspondence claim, so these two results should be reported separately.

### 2. Formal Correspondence Rule

Output files:

- `formal_cluster_correspondence_definition.md`
- `distance_metric_consensus_matches.csv`

Main result:

Five cluster pairs appear as core correspondences under at least three of the four distance metrics.

Two pairs appear under all four metrics:

- `cluster_1=2` to `cluster_2=2`
- `cluster_1=4` to `cluster_2=1`

Three pairs appear under three metrics:

- `cluster_1=0` to `cluster_2=0`
- `cluster_1=1` to `cluster_2=4`
- `cluster_1=5` to `cluster_2=3`

### 3. Paper-Ready Temporal Stability Summary

Output files:

- `paper_ready_temporal_stability_summary.csv`
- `paper_ready_monthly_retention_rates.csv`
- `paper_ready_state_retention_rates.csv`
- `paper_ready_transition_probability_matrix.csv`
- `paper_ready_monthly_retention_rates.png`

Main result:

- 11 month-to-month transitions were analyzed.
- 8,130,751 consecutive wallet-month pairs were included.
- Mean monthly self-transition rate: `0.4538`
- Monthly range: `0.4324` to `0.4802`
- Most stable state: `C3`, self-transition probability `0.5237`
- Least stable state: `C5`, self-transition probability `0.2340`

### 4. Cross-Feature-Set Spearman Correlation

Output files:

- `cross_feature_set_spearman_summary.csv`
- `cross_feature_set_spearman_correlation_matrix.csv`
- `cross_feature_set_top_absolute_correlations.csv`
- `cross_feature_set_spearman_heatmap.png`

Main result:

- Sampled overlapping wallets: `137,297`
- Mean absolute Spearman correlation: `0.3216`
- Median absolute Spearman correlation: `0.2612`
- Share of feature pairs with absolute correlation at least `0.8`: `0.0808`
- Share of feature pairs with absolute correlation at least `0.6`: `0.1540`

Interpretation:

The two feature sets are related but not redundant.

This supports the argument that convergence across feature sets is meaningful.

### 5. Minimum Observation Experiment

Output files:

- `minimum_observation_experiment_summary.csv`
- `minimum_observation_experiment_runs.csv`
- `minimum_observation_correspondence_curve.png`

Main result:

The sparse interval dataset was subsampled at 10%, 25%, 50%, 75%, and 100%, with repeated KMeans runs.

Correspondence to `cluster_2` was already high at lower fractions and peaked around the middle fractions in this run.

This gives a practical observation-density result, but it should be presented carefully as a subsampling recovery experiment rather than a full new longitudinal dataset.

## What Still Remains

No major analysis item from the advisor list is completely untouched anymore.

The remaining work is mostly paper assembly and interpretation:

1. Decide how to phrase the difference between distance-metric correspondence and wallet-level label-overlap correspondence.
2. Move the new outputs into Methods and Results tables.
3. Write the cluster stability literature/background section.
4. Choose final figures from the generated outputs.
5. Avoid overclaiming the `75%` figure unless it is explicitly defined as distance-metric correspondence, not wallet-level overlap.
