# EOA-Only K5 Downstream Validation Decision Memo

## Purpose

This memo summarizes the downstream validation work completed after selecting EOA-only `K=5` as the preferred richer role-taxonomy candidate.

The goal is not to prove that five is the only true number of Ethereum wallet roles. The goal is to decide whether `K=5` is defensible enough to become the main EOA-only project result.

## What Was Run

### 1. K-selection dossier

Main output:

- `results/eoa_k_model_selection/eoa_k_model_selection_report.md`

This tested `K=2` through `K=10` using full-data internal metrics, seed stability, random-label null testing, bootstrap silhouette intervals, feature-separation tests, cluster-size gates, and parsimony.

Main finding:

- `K=2` and `K=3` are strongest for coarse separation.
- `K=4` is defensible but less expressive.
- `K=5` is the preferred richer role-taxonomy candidate.
- `K=6+` creates more detailed partitions, but the evidence becomes weaker because of lower seed stability and/or smaller clusters.

### 2. EOA-only K5 clustering and role profiles

Main outputs:

- `results/eoa_only_kmeans5/cluster_sizes.csv`
- `results/eoa_only_kmeans5/cluster_feature_medians_robust_scaled.csv`
- `results/eoa_only_kmeans5/cluster_descriptions/eoa_only_cluster_behavior_report.md`

K5 cluster sizes:

| Cluster | Wallets | Share |
|---:|---:|---:|
| C0 | 776,004 | 31.75% |
| C1 | 923,286 | 37.78% |
| C2 | 154,864 | 6.34% |
| C3 | 183,079 | 7.49% |
| C4 | 406,635 | 16.64% |

This passes the practical cluster-size requirement because no cluster is below 5 percent.

### 3. Transaction-network validation

Main outputs:

- `results/eoa_only_kmeans5/network_validation/eoa_k5_transaction_network_validation_report.md`
- `results/eoa_only_kmeans5/network_validation/network_validation_summary.csv`
- `results/eoa_only_kmeans5/network_validation/cluster_adjacency_tx_counts.csv`
- `results/eoa_only_kmeans5/network_validation/figures/cluster_adjacency_tx_counts_log_heatmap.png`

The September 2022 transaction-network validation processed:

- `23,178,780` raw transaction rows
- `3,671,344` rows where both sender and recipient had K5 EOA labels
- coverage ratio: `15.84%`

The role-to-role transaction matrix showed structured flows between K5 roles, especially involving C3 and C4.

However, the random-label same-cluster test was not supportive:

- observed sampled same-cluster ratio: `0.2955`
- randomized-label null mean: `0.2982`
- p-value: `0.5644`

Interpretation:

The K5 roles do not show stronger within-role transaction concentration than shuffled labels in this sampled network test. Therefore, the network evidence for K5 should be reported as mixed, not strong.

This is important because it means K5 is more strongly supported by feature-space stability and temporal behaviour than by same-role transaction-network modularity.

### 4. Temporal validation

Main outputs:

- `results/eoa_only_kmeans5/temporal_validation/eoa_k5_temporal_validation_report.md`
- `results/eoa_only_kmeans5/temporal_validation/overall_transition_probability_matrix.csv`
- `results/eoa_only_kmeans5/temporal_validation/state_transition_stability.csv`
- `results/eoa_only_kmeans5/temporal_validation/two_step_return_analysis.csv`
- `results/eoa_only_kmeans5/temporal_validation/figures/`

The temporal validation used all months from `202201` through `202212`.

Month-to-month self-transition rates were consistently moderate:

- lowest monthly self-transition rate: `47.20%`
- highest monthly self-transition rate: `51.69%`
- most month pairs were around `49%` to `51%`

Overall state persistence by K5 role:

| State | Self-transition probability | Main next destinations |
|---:|---:|---|
| C0 | 0.486 | C0, C2, C1 |
| C1 | 0.447 | C1, C2, C0 |
| C2 | 0.558 | C2, C0, C1 |
| C3 | 0.412 | C3, C1, C2 |
| C4 | 0.284 | C4, C1, C0 |

The strongest temporal state was C2, with a self-transition probability of `0.558`.

C4 was the least persistent state, with a self-transition probability of `0.284`, suggesting it may be a more temporary or transitional behaviour.

### 5. Two-step return analysis

This checks the pattern discussed during project review: a wallet may leave its original role for one month and return to it in the next month.

The result confirms that this pattern exists.

For wallets that left their original state, the two-step return rate ranged from:

- minimum: `29.95%`
- maximum: `37.69%`

Interpretation:

A meaningful share of wallets temporarily deviate from a behaviour state and then return. This supports treating wallet roles as behavioural states with recurring patterns, not fixed real-world identities.

## Overall Decision

`K=5` is defensible as the main EOA-only behavioural role taxonomy, but the claim must be framed carefully.

The strongest support for `K=5` comes from:

- better seed stability than `K=6`
- acceptable cluster sizes
- interpretable feature profiles
- significant separation from random labels in feature-space model-selection tests
- moderate month-to-month temporal persistence
- clear two-step return behaviour

The weakest support comes from:

- transaction-network same-cluster validation, which did not beat the shuffled-label null test

## Update After K4/K5/K6 Downstream Comparison

A later side-by-side comparison ran the same downstream validation for `K=4`, `K=5`, and `K=6`.

Main output:

- `results/eoa_k4_k5_k6_comparison/eoa_k4_k5_k6_downstream_comparison.md`

The comparison makes the decision more nuanced:

- `K=4` is the strongest conservative network-aligned taxonomy.
- `K=5` remains the preferred richer behavioural taxonomy.
- `K=6` is useful as a fine-grained exploratory comparison, but it is less stable.

This means the final paper should not present `K=5` as winning every validation category.

The better framing is:

> `K=4` provides the strongest conservative network evidence, while `K=5` provides the best richer behavioural-role vocabulary when stability, interpretability, cluster size, and temporal persistence are considered together.

## Recommended Paper Wording

Use:

> After removing contract addresses, `K=5` provides the strongest balance between statistical defensibility, interpretability, cluster size, and temporal persistence among richer EOA-only wallet-role segmentations. The roles are best interpreted as behavioural states rather than verified real-world identities. Temporal validation shows moderate persistence and meaningful two-step return behaviour, while transaction-network validation gives mixed evidence: role-to-role flows are structured, but same-role transaction concentration is not stronger than a shuffled-label null test.

Avoid:

> The Ethereum wallet network naturally contains exactly five roles.

Avoid:

> K5 is strongly validated by the transaction network.

Avoid:

> K5 roles are fixed wallet identities.

## Next Research Step

The next strengthening step is to run downstream network and temporal validation for `K=4`, `K=5`, and `K=6` side by side using the same scripts.

That would answer whether K5 is not only better by model-selection metrics, but also the best downstream-validated taxonomy among the realistic role counts.
