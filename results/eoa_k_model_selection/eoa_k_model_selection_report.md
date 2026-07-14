# EOA-Only K Model Selection Dossier

## Question

Which K values are statistically defensible for EOA-only Ethereum wallet behaviour segmentation?

This dossier does not try to prove a single true K. It separates a coarse metric answer from a role-taxonomy answer.

## Evidence Used

- Full EOA-only K sensitivity table: `results\eoa_only_kmeans6\k_sensitivity_full\k_sensitivity_summary.csv`.
- Sampled proof tests from `wallet_eoa_only_kmeans6_features_robust_scaled\wallet_eoa_only_kmeans6_features_robust_scaled.csv`.
- Sample size for proof tests: `60,000` wallets.
- Evaluation size for silhouette/null tests: `2,000` wallets.
- Random-label permutations per K: `50`.
- Tested K values: `2, 3, 4, 5, 6, 7, 8, 9, 10`.

## Main Conclusion

- Best metric-only/coarse K: `K=2`.
- Best overall statistical score in this dossier: `K=3`.
- Best role-taxonomy candidate after defensibility gates: `K=5`.

For this project, the strongest academically defensible wording is:

> K=5 is statistically defensible as the preferred richer role-taxonomy candidate among the tested alternatives. K=2 and K=3 are stronger if the goal is only coarse separation. K=4 is also defensible but less expressive. K>=6 creates more roles, but the EOA-only evidence shows weaker seed stability and/or smaller clusters, so those values need downstream justification before becoming the primary claim.

## Full-Data Screening Metrics

|   k |   silhouette_mean |   silhouette_std |   davies_bouldin_mean |   calinski_harabasz_mean |   inertia_mean |   min_cluster_share_mean |   max_cluster_share_mean |   stability_ari_mean |   stability_ari_std |   stability_nmi_mean |   stability_nmi_std |   rank_stability_ari |   rank_silhouette |
|----:|------------------:|-----------------:|----------------------:|-------------------------:|---------------:|-------------------------:|-------------------------:|---------------------:|--------------------:|---------------------:|--------------------:|---------------------:|------------------:|
|   2 |          0.237164 |       0.00571798 |               1.84753 |                   534307 |    4.23854e+07 |                0.292336  |                 0.707664 |             0.802705 |           0.0731751 |             0.703103 |           0.1011    |                    1 |                 1 |
|   3 |          0.231146 |       0.0107336  |               1.58464 |                   521893 |    3.61957e+07 |                0.088842  |                 0.60318  |             0.758663 |           0.0888622 |             0.70095  |           0.0842401 |                    2 |                 2 |
|   4 |          0.163333 |       0.00534107 |               1.68596 |                   479396 |    3.25489e+07 |                0.0789001 |                 0.413901 |             0.58936  |           0.148174  |             0.620588 |           0.108522  |                    4 |                 3 |
|   5 |          0.156608 |       0.00628956 |               1.73913 |                   426621 |    3.04064e+07 |                0.0650776 |                 0.35359  |             0.712603 |           0.140987  |             0.687235 |           0.126764  |                    3 |                 4 |
|   6 |          0.153641 |       0.0084625  |               1.72131 |                   388445 |    2.88147e+07 |                0.0523012 |                 0.335874 |             0.484808 |           0.0630356 |             0.520046 |           0.0618006 |                    8 |                 6 |
|   7 |          0.148793 |       0.0208517  |               1.64812 |                   373507 |    2.69657e+07 |                0.042939  |                 0.275763 |             0.503712 |           0.132591  |             0.574562 |           0.0704688 |                    7 |                 7 |
|   8 |          0.155946 |       0.0143304  |               1.5983  |                   357372 |    2.55531e+07 |                0.0363879 |                 0.261817 |             0.539846 |           0.141383  |             0.600376 |           0.0813405 |                    5 |                 5 |
|   9 |          0.141482 |       0.0128564  |               1.61267 |                   336727 |    2.45797e+07 |                0.0359118 |                 0.22701  |             0.450709 |           0.0412397 |             0.572502 |           0.0142972 |                    9 |                 9 |
|  10 |          0.142299 |       0.00507887 |               1.63176 |                   320089 |    2.37092e+07 |                0.025465  |                 0.211038 |             0.515163 |           0.0474914 |             0.626526 |           0.0542094 |                    6 |                 8 |

## Sample-Based Statistical Proof Tests

|   k |   sample_wallets |   eval_wallets |   sample_silhouette_mean |   sample_silhouette_ci_low |   sample_silhouette_ci_high |   random_label_null_mean |   random_label_null_std |   random_label_null_max |   random_label_p_value |   min_cluster_share_sample |   max_cluster_share_sample |   cluster_entropy |   significant_feature_count_bh_0_05 |   median_epsilon_squared |   max_epsilon_squared | top_feature_by_effect   |   top_feature_epsilon_squared |
|----:|-----------------:|---------------:|-------------------------:|---------------------------:|----------------------------:|-------------------------:|------------------------:|------------------------:|-----------------------:|---------------------------:|---------------------------:|------------------:|------------------------------------:|-------------------------:|----------------------:|:------------------------|------------------------------:|
|   2 |            60000 |           2000 |                 0.196102 |                   0.190835 |                    0.201137 |               0.00010392 |              0.00237936 |              0.00518533 |              0.0196078 |                  0.412183  |                   0.587817 |          0.977633 |                                  30 |                 0.277502 |              0.5283   | total_flow_sum          |                      0.5283   |
|   3 |            60000 |           2000 |                 0.150892 |                   0.145891 |                    0.155626 |              -0.00786836 |              0.00385294 |             -0.00411308 |              0.0196078 |                  0.196233  |                   0.451467 |          0.95223  |                                  32 |                 0.312235 |              0.643734 | std_daily_total_flow    |                      0.643734 |
|   4 |            60000 |           2000 |                 0.220192 |                   0.214905 |                    0.225872 |              -0.0180274  |              0.00869875 |             -0.00511574 |              0.0196078 |                  0.0647167 |                   0.6061   |          0.774504 |                                  33 |                 0.357583 |              0.447466 | total_flow_sum          |                      0.447466 |
|   5 |            60000 |           2000 |                 0.147831 |                   0.143513 |                    0.152305 |              -0.0220778  |              0.00966306 |             -0.00839677 |              0.0196078 |                  0.0572333 |                   0.5339   |          0.797837 |                                  33 |                 0.371325 |              0.536325 | total_flow_sum          |                      0.536325 |
|   6 |            60000 |           2000 |                 0.146045 |                   0.141046 |                    0.15135  |              -0.0243151  |              0.00840592 |             -0.0117902  |              0.0196078 |                  0.0506    |                   0.388083 |          0.88612  |                                  33 |                 0.474552 |              0.587546 | active_days_observed    |                      0.587546 |
|   7 |            60000 |           2000 |                 0.168373 |                   0.162787 |                    0.173683 |              -0.0374366  |              0.0168423  |             -0.0175853  |              0.0196078 |                  0.0153167 |                   0.306067 |          0.879581 |                                  33 |                 0.447838 |              0.652158 | total_flow_sum          |                      0.652158 |
|   8 |            60000 |           2000 |                 0.162036 |                   0.157154 |                    0.167234 |              -0.0469608  |              0.0175126  |             -0.0215068  |              0.0196078 |                  0.0181667 |                   0.30505  |          0.829878 |                                  33 |                 0.408955 |              0.681249 | total_flow_sum          |                      0.681249 |
|   9 |            60000 |           2000 |                 0.130531 |                   0.126008 |                    0.134959 |              -0.0400497  |              0.0107903  |             -0.0216823  |              0.0196078 |                  0.0311833 |                   0.220667 |          0.923876 |                                  33 |                 0.503695 |              0.647663 | max_daily_total_flow    |                      0.647663 |
|  10 |            60000 |           2000 |                 0.153283 |                   0.147835 |                    0.158531 |              -0.0464582  |              0.0134264  |             -0.0243135  |              0.0196078 |                  0.0213667 |                   0.217383 |          0.912641 |                                  33 |                 0.524323 |              0.719445 | total_flow_sum          |                      0.719445 |

## Model Selection Scorecard

|   k |   overall_statistical_score |   role_taxonomy_score | defensible_role_taxonomy   |   silhouette_mean |   stability_ari_mean |   min_cluster_share_mean |   cluster_entropy |   random_label_p_value |   median_epsilon_squared |
|----:|----------------------------:|----------------------:|:---------------------------|------------------:|---------------------:|-------------------------:|------------------:|-----------------------:|-------------------------:|
|   2 |                    0.666667 |             nan       | False                      |          0.237164 |             0.802705 |                0.292336  |          0.977633 |              0.0196078 |                 0.277502 |
|   3 |                    0.791667 |             nan       | False                      |          0.231146 |             0.758663 |                0.088842  |          0.95223  |              0.0196078 |                 0.312235 |
|   4 |                    0.5      |               0.595   | True                       |          0.163333 |             0.58936  |                0.0789001 |          0.774504 |              0.0196078 |                 0.357583 |
|   5 |                    0.5      |               0.61875 | True                       |          0.156608 |             0.712603 |                0.0650776 |          0.797837 |              0.0196078 |                 0.371325 |
|   6 |                    0.5      |               0.37625 | False                      |          0.153641 |             0.484808 |                0.0523012 |          0.88612  |              0.0196078 |                 0.474552 |
|   7 |                    0.5      |               0.39    | False                      |          0.148793 |             0.503712 |                0.042939  |          0.879581 |              0.0196078 |                 0.447838 |
|   8 |                    0.604167 |               0.54125 | False                      |          0.155946 |             0.539846 |                0.0363879 |          0.829878 |              0.0196078 |                 0.408955 |
|   9 |                    0.5625   |               0.2675  | False                      |          0.141482 |             0.450709 |                0.0359118 |          0.923876 |              0.0196078 |                 0.503695 |
|  10 |                    0.625    |               0.3625  | False                      |          0.142299 |             0.515163 |                0.025465  |          0.912641 |              0.0196078 |                 0.524323 |

## Plain-Language Explanation Of The Tests

### Full-data K sensitivity

This tests several possible numbers of clusters, from K=2 to K=10. The goal is to avoid choosing a cluster count only because it looks convenient. If a K value is defensible, it should look reasonable compared with nearby alternatives.

### Silhouette score

Silhouette measures whether wallets are closer to wallets in their own cluster than to wallets in other clusters. Higher values mean cleaner separation. In this analysis, K=2 and K=3 have the strongest silhouette scores, which means the broadest divisions are easiest to separate.

### Seed stability

KMeans starts from random initial positions. Seed stability checks whether the clustering result stays similar when the algorithm is rerun with different random starts. A stable K is easier to defend because it is less dependent on random initialization.

### ARI and NMI

Adjusted Rand Index and Normalized Mutual Information compare two clustering runs. In simple terms, they ask whether two runs mostly assign wallets to similar groups. Higher ARI and NMI mean the cluster structure is more repeatable.

### Davies-Bouldin score

Davies-Bouldin measures whether clusters are compact and separated from each other. Lower values are better. It is useful as a secondary check, but it should not be used alone to choose K.

### Calinski-Harabasz score

Calinski-Harabasz compares separation between clusters with variation inside clusters. Higher values usually indicate clearer separation. Like the other internal metrics, it is evidence, not a final decision rule.

### Inertia

Inertia is the objective KMeans directly minimizes. It measures how far wallets are from their assigned cluster centers. It always decreases as K increases, so it cannot choose K by itself. It is mainly useful for checking whether there is an elbow where extra clusters stop adding much improvement.

### Random-label null test

The random-label null test keeps the same number of clusters and the same cluster sizes, but shuffles the labels randomly. Then it compares the real clustering against those random assignments. If the real clustering is much stronger than the shuffled labels, the result is not just a random grouping. In this run, every tested K had a p-value of about 0.0196 against the random-label null.

### Bootstrap confidence interval

The bootstrap confidence interval estimates uncertainty around the sampled silhouette score. Instead of trusting one sample value, it resamples the evaluation wallets many times and reports a likely range. Narrow intervals mean the sampled estimate is more stable.

### Kruskal-Wallis feature-separation test

This test checks whether the clusters differ across the engineered wallet-behaviour features. It asks whether the groups are behaviourally different, not only algorithmically labelled. Because this dataset is large, statistical significance is expected for many features, so effect size is also needed.

### Epsilon-squared effect size

Epsilon squared measures how large the feature differences are. This helps separate meaningful behavioural differences from differences that are statistically significant only because the dataset is very large.

### Cluster-size gate

The cluster-size gate checks whether a K value creates very small groups. For the role-taxonomy decision, a K value should avoid clusters below 5 percent of the full EOA-only dataset. Very small clusters may still be interesting, but they are harder to defend as main wallet roles.

### Parsimony

Parsimony means preferring the simpler model when two choices explain the data similarly well. Higher K values often create more specific differences, but that does not automatically make them better. A paper-facing taxonomy should use enough roles to be informative without splitting the population unnecessarily.

### Role-taxonomy score

The role-taxonomy score is aligned with the research goal of finding interpretable wallet roles. It combines separation, stability, cluster size, random-label evidence, and parsimony. It is different from asking which K has the single best internal metric.

### Defensible role-taxonomy flag

This is a pass/fail decision rule. A K value passes only if it has at least four clusters, beats the random-label null test, avoids clusters below 5 percent, reaches acceptable seed stability, and shows broad feature separation.

## Commentary On The Results

The strongest purely statistical separation appears at K=2 and K=3. These values have the best silhouette and seed-stability results, so they are useful evidence that the EOA-only wallet population has a strong coarse structure.

However, K=2 and K=3 are too broad for the main research goal. They would tell us that wallets can be divided into a few large behavioural groups, but they do not provide a rich enough vocabulary for wallet roles.

K=4 passes the defensibility gates and is a conservative multi-role option. Its main limitation is interpretability depth: it compresses the wallet population into fewer behavioural types, so some meaningful distinctions may remain merged.

K=5 is the best balance under the current evidence. It passes the random-label test, passes the minimum-size gate, has broad feature separation, and has much stronger seed stability than K=6. This makes it the preferred EOA-only role-taxonomy candidate.

K=6 remains interpretable, but it is weaker after contract removal. Its seed-stability ARI is 0.4848, compared with 0.7126 for K=5. That means the six-cluster solution is more sensitive to random initialization, so it should not be claimed as the best-supported EOA-only resolution unless downstream graph and temporal validation clearly justify the extra role.

K=7 through K=10 produce more detailed partitions, and some of their feature-separation effect sizes are strong. This is expected because more clusters can create more specific feature differences. The problem is that these higher K values produce smaller clusters and weaker stability, so they risk over-fragmenting the wallet population.

The correct academic conclusion is therefore not that K=5 is the only true number of Ethereum wallet roles. The defensible claim is that, among tested alternatives, K=5 currently offers the strongest balance between statistical support, stability, cluster size, and role interpretability for the EOA-only dataset.

## How To Read This

- Silhouette asks whether wallets are closer to their own cluster than to other clusters.
- Seed stability asks whether the same K gives similar clusters when KMeans starts from different random initializations.
- Random-label testing asks whether the observed separation is stronger than shuffled labels with the same cluster sizes.
- Feature separability asks whether the clusters differ across the engineered wallet behaviour features, not only by algorithm labels.
- Cluster entropy asks whether the solution avoids being dominated by one giant cluster and several very small clusters.
- The defensible role-taxonomy flag requires K>=4, p<=0.05 against random labels, no cluster below 5 percent in the full run, ARI stability at least 0.55, and broad feature separation.

## Claim Boundaries

- These tests support defensibility, not a universal natural law for Ethereum wallets.
- The selected K should still be tied to interpretability and downstream network/temporal validation.
- K=5 should be presented as the preferred EOA-only role-taxonomy candidate under the current evidence, not as the only possible partition.