# EOA-Only K Selection Assessment

This note evaluates whether KMeans with `k=6` remains defensible after Gate 1 contract removal.

## Short Answer

`k=6` is **usable as a fine-grained exploratory role vocabulary**, but it is **not defensible as the best or most stable EOA-only clustering resolution** based on the current k-sensitivity results.

For paper-facing claims, the safer position is:

> After removing contract addresses, the EOA-only data support a stable coarse structure at `k=2` or `k=3`. Among richer multi-role segmentations, `k=5` is currently more defensible than `k=6`. The `k=6` solution remains interpretable, but it should be treated as a finer-grained taxonomy requiring downstream validation rather than as the uniquely justified number of wallet roles.

## Update: Broader K Defensibility Dossier

The later model-selection dossier expands the question from "`k=5` or `k=6`?" to "which K values are statistically defensible among the tested alternatives?"

That output is stored in:

- `results/eoa_k_model_selection/eoa_k_model_selection_report.md`
- `results/eoa_k_model_selection/model_selection_scorecard.csv`
- `results/eoa_k_model_selection/sample_statistical_tests.csv`
- `results/eoa_k_model_selection/figures/`

The dossier tests `k=2` through `k=10` using:

- full-data internal metrics from the EOA-only k-sensitivity run,
- seed stability from repeated KMeans starts,
- random-label null testing on a 60,000-wallet sample,
- bootstrap confidence intervals for sample silhouette,
- feature-separation checks with Kruskal-Wallis tests and effect sizes,
- cluster-size and parsimony gates.

The broader result supports the same main conclusion with stronger evidence:

> `k=5` is statistically defensible as the preferred richer role-taxonomy candidate. `k=2` and `k=3` remain stronger for coarse separation. `k=4` is also defensible but less expressive. Values above `k=5` create more roles, but the EOA-only evidence shows weaker seed stability and/or smaller clusters, so they need downstream graph and temporal validation before becoming the main paper claim.

## Why This Assessment Changed

The original mixed-address KMeans6 result failed Gate 1 because one cluster was heavily contract-contaminated.

Mixed cluster `C3` contained:

- `209,578` total addresses
- `109,087` EOAs
- `100,491` contracts
- `47.95%` contracts

Therefore, the original six-role interpretation should be treated as a pre-Gate-1 baseline, not as the final wallet-role result.

The EOA-only dataset contains:

- `2,443,868` EOA wallets
- `33` robust-scaled behavioural features
- contract addresses removed before refitting KMeans

## EOA-Only KMeans6 Result

The EOA-only `k=6` result is interpretable and the clusters are large enough to profile.

| EOA-only cluster | Wallets | Share | Current behavioural summary |
|---:|---:|---:|---|
| C0 | 735,526 | 30.10% | Small-value-flow |
| C1 | 534,085 | 21.85% | Activity-intensity-leaning |
| C2 | 175,912 | 7.20% | High-transaction, persistent, large-value-flow, bursty-volatile |
| C3 | 432,610 | 17.70% | Activity-intensity-leaning |
| C4 | 142,260 | 5.82% | High-transaction, outflow-leaning |
| C5 | 423,475 | 17.33% | Bursty-volatile |

This means `k=6` can still be discussed as a detailed behavioural taxonomy.

However, interpretability alone is not enough for a publication claim.

## K Sensitivity Evidence

The full EOA-only k-sensitivity experiment tested `k=2` through `k=10` on all `2,443,868` EOA wallets using seeds `492`, `493`, and `494`.

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

## What The Metrics Say

### Best metric-only choices

The strongest metric-only options are:

- `k=2`: best silhouette and best seed stability
- `k=3`: second-best silhouette and strong seed stability

These are good if the paper wants a coarse division of wallet behaviour.

But they are probably too coarse for the original goal of producing interpretable wallet roles.

### Best richer multi-role choice

Among richer segmentations, `k=5` is currently stronger than `k=6`.

| Metric | k=5 | k=6 | Better option |
|---|---:|---:|---|
| Silhouette mean | 0.1566 | 0.1536 | k=5 |
| Stability ARI mean | 0.7126 | 0.4848 | k=5 |
| Stability NMI mean | 0.6872 | 0.5200 | k=5 |
| Min cluster share | 6.51% | 5.23% | k=5 |

The stability gap is the important part.

`k=6` is much less seed-stable than `k=5`, which means the six-way split is more sensitive to initialization.

## Is KMeans6 Defensible?

### Defensible claim

Yes, but only with careful wording:

> We use `k=6` as a fine-grained behavioural vocabulary because it produces interpretable EOA wallet profiles and avoids tiny clusters, but k-sensitivity shows that it is not the most stable resolution. Therefore, the six-role taxonomy should be validated through downstream graph, temporal, and robustness analyses before being treated as the main paper claim.

### Not defensible claim

Do not say:

> The EOA-only data prove that there are six wallet roles.

Do not say:

> K=6 is the optimal number of clusters.

Do not say:

> Stability supports K=6.

The current stability evidence does not support that.

## Paper-Focused Recommendation

After Gate 1, all downstream numbers should be regenerated on the EOA-only dataset and weak claims should not be carried forward.

Based on that expectation, the recommended path is:

1. Treat the old mixed-address KMeans6 result as a baseline only.
2. Treat the EOA-only analysis as the new paper-facing branch.
3. Do not lock the paper to KMeans6 yet.
4. Run and describe an EOA-only `k=5` clustering.
5. Compare EOA-only `k=5` and `k=6` on:
   - interpretability,
   - cluster sizes,
   - seed/subsample stability,
   - real transaction-graph validation,
   - temporal persistence.
6. Choose the final paper taxonomy after downstream validation, not from silhouette alone.

## Practical Decision

The next analysis should be:

> Fit and profile EOA-only KMeans with `k=5`, then compare it directly with the existing EOA-only KMeans6 result.

If `k=5` produces clean behavioural roles and survives downstream validation better than `k=6`, the paper should use `k=5`.

If `k=6` has a role that is substantively important and also survives transaction-graph/temporal validation, it can still be used, but with an explicit caveat that it is a finer-grained role resolution rather than the most stable one.

## Suggested Paper Wording

> Gate 1 contract filtering changed the structure of the wallet population. In the EOA-only dataset, coarse solutions at `k=2` and `k=3` were most stable by internal metrics. For richer behavioural segmentation, `k=5` showed stronger seed stability than `k=6`, while `k=6` provided a more fine-grained but less stable role vocabulary. We therefore treat the final number of roles as a model-selection question to be resolved jointly by interpretability, stability, transaction-graph validation, and temporal persistence.
