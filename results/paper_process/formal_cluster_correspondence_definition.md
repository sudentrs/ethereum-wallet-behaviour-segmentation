# Formal Cluster Correspondence Rule

Cluster correspondence is defined in two layers.

First, for each distance metric, construct a cluster-to-cluster distance matrix between the source clustering and the target clustering.

Second, solve a maximum bipartite matching problem on that matrix, using the Hungarian algorithm, so each source cluster is matched to at most one target cluster.

For label-overlap validation, correspondence is measured as the share of wallets recovered by the best bipartite alignment between the two labelings.

The paper-ready statistic is:

`Correspondence = matched wallets under optimal one-to-one cluster alignment / total overlapping wallets`.

A pair is treated as a core correspondence when it appears under at least three of the four distance metrics: cosine, weighted Euclidean, Mahalanobis, and Wasserstein.

The statistical significance of the label-overlap correspondence is tested by randomly permuting one clustering's labels while preserving cluster sizes, recomputing the optimal bipartite overlap, and comparing the observed score to this null distribution.
