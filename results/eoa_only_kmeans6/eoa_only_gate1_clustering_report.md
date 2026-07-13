# EOA-Only Gate 1 Clustering Report

## Executive Summary

The full EOA/contract classification confirms that the original mixed-address KMeans6 result is materially contaminated by smart contracts. The strongest issue is mixed cluster C3, where 100,491 of 209,578 addresses are contracts, corresponding to a contract share of 47.95%. This exceeds the Gate 1 threshold of 15%, so the original mixed-address clustering should be treated as a pre-Gate-1 baseline rather than the final paper-facing wallet-role result.

After removing contract addresses, the EOA-only feature table contains 2,443,868 wallets. A new EOA-only KMeans6 model was fitted on the robust-scaled expanded behavioural features. The resulting six clusters are interpretable as behavioural wallet roles, but the k-sensitivity analysis shows that k=6 is not the most stable EOA-only solution. In the full-data sensitivity run, k=5 is more stable than k=6 among multi-role segmentations, while k=2 and k=3 capture coarser high-level structure.

## Gate 1 Result

| Mixed cluster | Total addresses | EOA addresses | Contract addresses | Contract share |
|---:|---:|---:|---:|---:|
| C0 | 616,169 | 569,090 | 47,079 | 7.64% |
| C1 | 281,978 | 241,608 | 40,370 | 14.32% |
| C2 | 805,252 | 738,815 | 66,437 | 8.25% |
| C3 | 209,578 | 109,087 | 100,491 | 47.95% |
| C4 | 790,194 | 753,530 | 36,664 | 4.64% |
| C5 | 35,072 | 31,738 | 3,334 | 9.51% |

Gate 1 therefore fails because C3 is far above the 15% contract-contamination threshold. C1 is also close to the threshold at 14.32%, so it should be interpreted cautiously.

## EOA-Only Dataset

| Quantity | Value |
|---|---:|
| Original mixed-address wallets | 2,738,243 |
| EOA-only wallets retained | 2,443,868 |
| Contract addresses removed | 294,375 |
| EOA share | 89.25% |
| Contract share | 10.75% |

The EOA-only branch should now be treated as the main branch for wallet-behaviour claims. The mixed-address branch remains useful as a baseline and as evidence that contract contamination materially affects the role vocabulary.

## EOA-Only KMeans6 Summary

| Metric | Value |
|---|---:|
| Wallets clustered | 2,443,868 |
| Feature count | 33 |
| k | 6 |
| Random seed | 492 |
| Inertia | 28,595,660 |
| Silhouette sample size | 50,000 |
| Silhouette | 0.1436 |

## EOA-Only KMeans6 Cluster Sizes

| EOA-only cluster | Wallets | Share |
|---:|---:|---:|
| C0 | 735,526 | 30.10% |
| C1 | 534,085 | 21.85% |
| C2 | 175,912 | 7.20% |
| C3 | 432,610 | 17.70% |
| C4 | 142,260 | 5.82% |
| C5 | 423,475 | 17.33% |

The EOA-only KMeans6 solution is not dominated by a single very large cluster, and its smallest cluster still contains 142,260 wallets. This makes all six clusters large enough for downstream profiling and validation.

## EOA-Only Behavioural Roles

| Cluster | Share | Behaviour label | Main interpretation |
|---:|---:|---|---|
| C0 | 30.10% | Small-value-flow | Low value-flow wallets with weak total inflow/outflow and low flow volatility. |
| C1 | 21.85% | Activity-intensity-leaning | Directionally imbalanced wallets with positive net-flow features but relatively low transaction intensity. |
| C2 | 7.20% | High-transaction, persistent, large-value-flow, bursty-volatile | High-activity wallets with persistent activity, large value flow, and high volatility. |
| C3 | 17.70% | Activity-intensity-leaning | Wallets with concentrated transaction/value movement, especially outflow-related activity, but lower persistence. |
| C4 | 5.82% | High-transaction, outflow-leaning | Short-lived but very dense activity wallets with strong transaction concentration and outflow leaning. |
| C5 | 17.33% | Bursty-volatile | Wallets with elevated net-flow, total-flow volatility, and persistent but irregular value movement. |

These labels are behavioural summaries, not verified real-world identities. They describe median robust-scaled feature profiles after removing contract addresses.

## Mixed vs EOA-Only Cluster Correspondence

The mixed and EOA-only clusterings were compared on the 2,443,868 wallets that remain after EOA filtering.

| Metric | Value |
|---|---:|
| Overlapping EOA wallets | 2,443,868 |
| Hungarian matched wallets | 1,439,367 |
| Hungarian matched share | 58.90% |
| Adjusted Rand Index | 0.3316 |
| Normalized Mutual Information | 0.3913 |

The EOA-only clustering is related to the mixed-address clustering, but it is not a simple relabelling. Contract removal reorganizes the role structure substantially.

The strongest mixed-to-EOA correspondences are:

| Mixed cluster | EOA-only cluster | Share of mixed-cluster EOAs matched |
|---:|---:|---:|
| C0 | C3 | 49.72% |
| C1 | C2 | 59.26% |
| C2 | C0 | 73.30% |
| C3 | C4 | 84.52% |
| C4 | C1 | 48.75% |
| C5 | C5 | 38.42% |

The contaminated mixed C3 does not disappear completely. Its EOA subset maps strongly to EOA-only C4, with 84.52% of mixed C3 EOAs assigned to EOA-only C4. This suggests that mixed C3 contained a real EOA behavioural signal, but that signal was blended with a large contract population in the pre-Gate-1 result.

## K Sensitivity And Stability

The full EOA-only k-sensitivity run tested k=2 through k=10 on all 2,443,868 EOA wallets, using seeds 492, 493, and 494. Silhouette was estimated on 50,000 wallets for computational tractability.

| k | Silhouette mean | Stability ARI mean | Stability NMI mean | Min cluster share | Max cluster share |
|---:|---:|---:|---:|---:|---:|
| 2 | 0.2372 | 0.8027 | 0.7031 | 29.23% | 70.77% |
| 3 | 0.2311 | 0.7587 | 0.7009 | 8.88% | 60.32% |
| 4 | 0.1633 | 0.5894 | 0.6206 | 7.89% | 41.39% |
| 5 | 0.1566 | 0.7126 | 0.6872 | 6.51% | 35.36% |
| 6 | 0.1536 | 0.4848 | 0.5200 | 5.23% | 33.59% |
| 7 | 0.1488 | 0.5037 | 0.5746 | 4.29% | 27.58% |
| 8 | 0.1559 | 0.5398 | 0.6004 | 3.64% | 26.18% |
| 9 | 0.1415 | 0.4507 | 0.5725 | 3.59% | 22.70% |
| 10 | 0.1423 | 0.5152 | 0.6265 | 2.55% | 21.10% |

The strongest metric-only solutions are k=2 and k=3. These are stable and have the highest silhouette values, but they provide only coarse segmentation. Among richer multi-role segmentations, k=5 is more stable than k=6:

| Comparison | k=5 | k=6 |
|---|---:|---:|
| Silhouette mean | 0.1566 | 0.1536 |
| Stability ARI mean | 0.7126 | 0.4848 |
| Stability NMI mean | 0.6872 | 0.5200 |
| Min cluster share | 6.51% | 5.23% |

This means EOA-only k=6 remains interpretable, but it should not be claimed as the most stable EOA-only resolution. A defensible paper framing is:

> The EOA-only data support a stable coarse structure at k=2 or k=3. For a richer behavioural taxonomy, k=5 appears more stable than k=6. The k=6 solution remains useful as a finer-grained role vocabulary, but it requires additional downstream validation and explicit stability caveats.

## Recommended Paper Position

The project should update its main clustering narrative as follows:

1. The original KMeans6 result is retained as a pre-Gate-1 mixed-address baseline.
2. Gate 1 failed because mixed C3 is heavily contract-contaminated.
3. Contract addresses were removed and the segmentation was rerun on 2.44 million EOA wallets.
4. The EOA-only KMeans6 result provides an interpretable six-role vocabulary.
5. However, k-sensitivity shows that k=6 is not the most stable EOA-only choice; k=5 is stronger among multi-role solutions, while k=2 and k=3 represent coarser high-level structure.
6. The next paper-ready step is to run downstream validation on the EOA-only branch, especially transaction-graph validation, temporal transition analysis, and stability/subsampling checks.

## Files Produced

| File | Purpose |
|---|---|
| `data/processed/wallet_kmeans6_expanded_daily_features_eoa_only.csv` | EOA-only expanded feature table. |
| `data/processed/wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled.csv` | EOA-only robust-scaled feature table. |
| `results/eoa_only_kmeans6/wallet_eoa_only_kmeans_clusters.csv` | EOA-only KMeans6 cluster assignments. |
| `results/eoa_only_kmeans6/cluster_sizes.csv` | EOA-only KMeans6 cluster sizes. |
| `results/eoa_only_kmeans6/cluster_feature_medians_robust_scaled.csv` | EOA-only KMeans6 median feature profiles. |
| `results/eoa_only_kmeans6/cluster_descriptions/eoa_only_cluster_behavior_labels.csv` | EOA-only role labels and profile summaries. |
| `results/eoa_only_kmeans6/mixed_comparison/mixed_to_eoa_only_comparison_summary.csv` | Mixed-vs-EOA correspondence metrics. |
| `results/eoa_only_kmeans6/k_sensitivity_full/k_sensitivity_summary.csv` | Full-data k-sensitivity and seed-stability summary. |

