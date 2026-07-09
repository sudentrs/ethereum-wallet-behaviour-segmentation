# Future Work Checklist

This checklist collects the improvements discussed for making the project stronger academically.

## Highest Priority

### Formal cluster stability protocol

Run KMeans6 repeatedly with different seeds and subsampled wallet sets.

Align clusters using Hungarian/bipartite matching.

Report ARI, NMI, and Jaccard similarity.

### Per-cluster stability

Report stability separately for each role.

This avoids implying that all clusters are equally reliable.

### K sensitivity analysis

Compare K values such as 2 through 10.

Use clustering metrics, interpretability, network validation, and temporal persistence.

Do not use stability alone to justify K=6.

### Monthly centroid drift

Compute each role centroid by month.

Measure whether role definitions move over time.

This strengthens the temporal analysis because it checks whether a role keeps the same meaning across months.

### Two-step transition analysis

Report common A -> B -> A return paths.

Important finding from the working analysis:

Among wallets that changed behavioural state, about 29.4% returned to their previous monthly state in the following month.

Examples:

- C3 -> C2 -> C3
- C2 -> C3 -> C2
- C3 -> C4 -> C3

## Strong Additions If Data Is Available

### External label validation

Use known labelled addresses such as exchanges, DeFi protocols, token contracts, ENS names, or Etherscan labels.

Check how labelled addresses distribute across the six behavioural roles.

This helps interpret the roles without changing the project into supervised classification.

### EOA vs contract separation

Separate externally owned accounts and smart contracts if possible.

This can make role interpretation cleaner.

### Graph embedding comparison

Run Node2Vec, DeepWalk, Role2Vec, or Struc2Vec on the transaction graph.

Compare graph-embedding clusters with behaviour-feature clusters.

## Presentation And Paper Improvements

### Formal role table

For each cluster, report:

- Cluster size.
- Dominant features.
- Network position.
- Temporal persistence.
- Common transitions.
- Interpretation.
- Cautions.

### Limitations section

State clearly:

- Roles are behavioural states, not verified identities.
- K=6 is an interpretable validated solution, not the only possible truth.
- Stability supports reproducibility under tested conditions, not absolute correctness.
- Results should be replicated across more time windows and external datasets.

### Literature positioning

Position the work against:

- Supervised Ethereum address classification.
- Address/entity clustering.
- Static graph analysis.
- Clustering stability literature.
- Temporal clustering literature.

