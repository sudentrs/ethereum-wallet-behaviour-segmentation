# EOA-Only K5 vs K6 Decision Report

## Executive Decision

After removing contracts, `k=5` is currently more defensible than `k=6` as the main EOA-wallet behavioural segmentation.

`k=6` remains interpretable, but it should be treated as a finer-grained exploratory taxonomy rather than the primary paper-facing choice unless downstream transaction-graph and temporal validation clearly favor it.

## Why K5 Is Stronger Right Now

The full EOA-only k-sensitivity experiment showed that `k=5` is more stable than `k=6` among richer multi-role segmentations.

| Metric | EOA-only k=5 | EOA-only k=6 | Stronger |
|---|---:|---:|---|
| Silhouette mean across seeds | 0.1566 | 0.1536 | k=5 |
| Single-run silhouette used here | 0.1612 | 0.1436 | k=5 |
| Seed stability ARI mean | 0.7126 | 0.4848 | k=5 |
| Seed stability NMI mean | 0.6872 | 0.5200 | k=5 |
| Minimum cluster share | 6.51% | 5.23% | k=5 |

The key point is the seed-stability gap.

`k=6` is much more sensitive to initialization, so it is weaker as a primary model unless later validation strongly supports the sixth split.

## K5 Role Summary

| K5 cluster | Wallets | Share | Behaviour label |
|---:|---:|---:|---|
| C0 | 776,004 | 31.75% | Small-value-flow |
| C1 | 923,286 | 37.78% | Value-scale-leaning |
| C2 | 154,864 | 6.34% | High-transaction, outflow-leaning |
| C3 | 183,079 | 7.49% | High-transaction, large-value-flow, bursty-volatile |
| C4 | 406,635 | 16.64% | Persistent |

This is a cleaner structure than the current K6 role list because it avoids having two separate clusters both labelled as activity-intensity-leaning.

## K5 vs K6 Alignment

K5 and K6 are related but not simple relabelings.

| Metric | Value |
|---|---:|
| Overlapping wallets | 2,443,868 |
| Hungarian matched wallets | 1,531,044 |
| Hungarian matched share | 62.65% |
| Adjusted Rand Index | 0.4536 |
| Normalized Mutual Information | 0.5072 |

The strongest correspondences are:

| K5 cluster | Best K6 match | Share of K5 cluster matched | Interpretation |
|---:|---:|---:|---|
| C0 | K6-C0 | 85.47% | Small-value-flow role is stable. |
| C1 | K6-C1 | 46.65% | Broad value-scale group is split in K6. |
| C2 | K6-C4 | 90.10% | High-transaction outflow role is stable. |
| C3 | K6-C2 | 46.26% | Large-flow volatile role is split in K6. |
| C4 | K6-C5 | 52.33% | Persistent role is split between K6 roles. |

## What K6 Appears To Add

K6 mostly adds finer splits inside broader K5 groups rather than discovering a completely independent sixth role.

Examples:

- K5-C1 splits across K6-C1, K6-C3, and K6-C5.
- K5-C3 splits mostly between K6-C2 and K6-C5.
- K5-C4 splits across K6-C5, K6-C2, and K6-C3.

This does not mean K6 is useless.

It means K6 should be framed as a finer-grained version of the EOA-only segmentation, not as the strongest primary resolution.

## Supervisor-Aligned Recommendation

For the paper process, use this hierarchy:

1. Report that contract filtering changed the clustering problem.
2. Present K5 as the current strongest multi-role EOA-only candidate.
3. Treat K6 as a secondary/finer-grained sensitivity analysis.
4. Do not claim that Ethereum EOA wallets naturally form exactly six roles.
5. Let the next validation stage decide whether K5 or K6 is final.

The next validation stage should compare K5 and K6 on:

- real wallet-level transaction-graph assortativity,
- degree-preserving null models,
- monthly temporal persistence,
- role-to-role mixing matrices,
- external label enrichment if labels are available.

## Paper-Safe Wording

Use:

> After contract removal, the EOA-only data supported a stable coarse structure and a more interpretable multi-role structure. Among richer segmentations, K5 was more stable than K6 by seed-stability and silhouette metrics, while K6 provided a finer-grained but less stable taxonomy. We therefore evaluate both K5 and K6 in downstream validation before fixing the final role vocabulary.

Avoid:

> KMeans6 is the final validated wallet-role model.

Avoid:

> The data prove there are six EOA wallet roles.

## Visual Evidence

Generated figures:

- `figures/k_sensitivity_k5_k6.png`
- `figures/k5_k6_cluster_size_comparison.png`
- `figures/k5_to_k6_row_share_heatmap.png`
- `figures/k5_profile_heatmap.png`
- `figures/k6_profile_heatmap.png`

