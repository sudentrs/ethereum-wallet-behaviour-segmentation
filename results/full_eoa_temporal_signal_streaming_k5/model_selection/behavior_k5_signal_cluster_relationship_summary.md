# Behavior K5 x Temporal Signal Cluster Summary

This summarizes the selected signal model-selection outputs: time-domain K=5 and wavelength K=3.

## Time-domain K5: top signal states per behavior cluster

| Behavior K5 | Signal cluster | Label | Wallets | Within behavior share | Enrichment vs global |
|---:|---:|---|---:|---:|---:|
| 0 | 2 | sparse long-gap state | 513,716 | 66.2% | 1.81x |
| 0 | 1 | sparse long-gap state | 123,655 | 15.9% | 0.73x |
| 1 | 2 | sparse long-gap state | 306,073 | 33.2% | 0.91x |
| 1 | 3 | low-activity mixed state | 258,723 | 28.0% | 1.26x |
| 2 | 1 | sparse long-gap state | 118,537 | 76.5% | 3.49x |
| 2 | 2 | sparse long-gap state | 32,125 | 20.7% | 0.57x |
| 3 | 0 | sparse long-gap state | 61,261 | 33.5% | 2.16x |
| 3 | 4 | intermittent switching state | 37,102 | 20.3% | 5.32x |
| 4 | 3 | low-activity mixed state | 182,354 | 44.8% | 2.02x |
| 4 | 0 | sparse long-gap state | 141,253 | 34.7% | 2.24x |


## Wavelength K3: top rhythm states per behavior cluster

| Behavior K5 | Signal cluster | Label | Wallets | Within behavior share | Enrichment vs global |
|---:|---:|---|---:|---:|---:|
| 0 | 0 | distributed high-frequency rhythm | 389,755 | 50.2% | 0.95x |
| 0 | 1 | distributed high-frequency rhythm | 356,575 | 46.0% | 1.12x |
| 1 | 0 | distributed high-frequency rhythm | 645,542 | 69.9% | 1.33x |
| 1 | 1 | distributed high-frequency rhythm | 273,553 | 29.6% | 0.72x |
| 2 | 1 | distributed high-frequency rhythm | 89,868 | 58.0% | 1.42x |
| 2 | 0 | distributed high-frequency rhythm | 43,741 | 28.2% | 0.54x |
| 3 | 1 | distributed high-frequency rhythm | 89,269 | 48.8% | 1.19x |
| 3 | 2 | distributed high-frequency rhythm | 53,419 | 29.2% | 4.55x |
| 4 | 1 | distributed high-frequency rhythm | 190,908 | 46.9% | 1.15x |
| 4 | 0 | distributed high-frequency rhythm | 167,541 | 41.2% | 0.78x |

## Main reading

- Behavior K5 cluster 0 is dominated by time-domain cluster 2, a sparse long-gap state with very low burstiness.
- Behavior K5 cluster 1 is temporally mixed, split across sparse long-gap and low-activity mixed states.
- Behavior K5 cluster 2 is strongly concentrated in time-domain cluster 1, the sparsest/longest-gap state.
- Behavior K5 cluster 3 is the clearest high-activity/intermittent behavior group, with strong enrichment in time-domain cluster 4.
- Behavior K5 cluster 4 is mostly low-activity mixed plus sparse long-gap, but also shows notable intermittent-switching enrichment.
- Wavelength K3 separates the population into two large high-frequency/distributed rhythm groups and one smaller slow-cycle/concentrated group.
- The slow-cycle/concentrated wavelength cluster is especially enriched in behavior K5 clusters 3 and 4, not in clusters 0 or 1.