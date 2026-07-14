# EOA-Only Ethereum Wallet Behaviour Segmentation: Final Progress Report

## 1. Why The Project Changed

The project originally used a mixed wallet dataset that contained both externally owned accounts (EOAs) and smart contract addresses.

That was a problem for academic interpretation.

EOAs and contracts can behave very differently. EOAs are normal wallet addresses controlled by users, institutions, bots, or services. Contracts are deployed programs, so their transaction patterns can reflect code execution rather than wallet-like behaviour.

Because our research question is about wallet behaviour, we added a Gate 1 correction:

> Remove contract addresses and rerun the main analysis on EOAs only.

This changed the project from:

> Proving that the original `K=6` clustering is the final answer.

to:

> Building a defensible EOA-only behavioural role taxonomy and testing which cluster resolutions are statistically and academically supportable.

## 2. Updated Research Question

The updated research question is:

> Can Ethereum externally owned accounts be organized into statistically defensible behavioural roles, and do those roles show evidence of feature-space separation, network structure, and temporal state dynamics?

This question has three parts.

First, we ask whether wallets can be grouped using engineered transaction-behaviour features.

Second, we ask whether those groups are reproducible and statistically defensible, rather than being only a convenient KMeans output.

Third, we ask whether the roles behave like meaningful behavioural states over time.

## 3. EOA-Only Data And Feature Pipeline

After contract filtering, the EOA-only feature table contains wallet-level behavioural features such as:

- activity intensity,
- active days,
- transaction count,
- value inflow and outflow,
- net flow,
- flow volatility,
- in/out directionality,
- concentration of transactions or value flow.

The main EOA-only robust-scaled feature table is:

`wallet_eoa_only_kmeans6_features_robust_scaled/wallet_eoa_only_kmeans6_features_robust_scaled.csv`

The K5 labels are stored in:

`results/eoa_only_kmeans5/wallet_eoa_only_kmeans_clusters.csv`

The monthly temporal validation uses the derived 2022 daily-wallet files:

`../dataverse_files/wallet_daily_clean_202201.csv`

through:

`../dataverse_files/wallet_daily_clean_202212.csv`

So the temporal analysis is full-year 2022 at the derived daily-wallet level.

However, not every raw monthly TSV is present in the repo. The raw TSV source files are still needed for full raw-data reproducibility from the very beginning of the pipeline.

## 4. K Selection: We Stopped Assuming K=6

The next step was to test whether `K=6` was still the best option after removing contracts.

We tested `K=2` through `K=10`.

The model-selection dossier uses:

- silhouette score,
- Davies-Bouldin score,
- Calinski-Harabasz score,
- inertia,
- seed stability,
- ARI and NMI,
- random-label null testing,
- feature-separation tests,
- cluster-size balance,
- role-taxonomy scoring.

Main output:

`results/eoa_k_model_selection/eoa_k_model_selection_report.md`

The key result is:

- `K=2` and `K=3` are strongest for coarse separation.
- `K=4` is a conservative multi-role taxonomy.
- `K=5` is the best richer behavioural role taxonomy.
- `K=6` is more detailed but less stable after contract removal.

The important academic point is:

> We should not claim there is one universal true K.

Instead, we should say:

> The EOA-only data supports several defensible resolutions. `K=4` is strongest as a conservative network-aligned taxonomy, while `K=5` is preferred when the goal is a richer behavioural taxonomy.

## 5. K4, K5, And K6 Downstream Comparison

After model selection, we compared `K=4`, `K=5`, and `K=6` using downstream validation.

Main output:

`results/eoa_k4_k5_k6_comparison/eoa_k4_k5_k6_downstream_comparison.md`

Summary:

| K | Seed stability ARI | Network null p-value | Mean temporal self-transition | Mean two-step return | Interpretation |
|---:|---:|---:|---:|---:|---|
| 4 | 0.5894 | 0.0099 | 0.5136 | 0.3545 | strongest conservative network-aligned taxonomy |
| 5 | 0.7126 | 0.5644 | 0.4999 | 0.3421 | best richer taxonomy balance |
| 6 | 0.4848 | 0.0495 | 0.4691 | 0.3118 | exploratory fine-grained taxonomy |

This result is nuanced.

`K=4` has the strongest same-role transaction-network null result.

`K=5` has the strongest role-taxonomy balance because it has better seed stability and useful temporal behaviour.

`K=6` is still useful as a sensitivity comparison, but it is weaker as the main EOA-only claim.

## 6. Why K5 Became The Main Taxonomy

K5 is not the best answer for every possible question.

It is the best answer for our main paper goal:

> A richer but still defensible behavioural role taxonomy.

K5 gives five interpretable roles without fragmenting the wallet population too much.

It also has stronger seed stability than K6:

- K5 seed stability ARI: `0.7126`
- K6 seed stability ARI: `0.4848`

That means K5 is less dependent on random KMeans initialization than K6.

The paper-facing claim should be:

> K5 is the preferred richer EOA behavioural taxonomy among the tested alternatives, while K4 should be reported as a conservative robustness comparison.

## 7. K5 Transaction-Network Validation

The K5 network validation checks whether the behavioural roles also appear in the actual transaction network.

Main output:

`results/eoa_only_kmeans5/network_validation/eoa_k5_transaction_network_validation_report.md`

The role-to-role transaction matrix shows that flows are structured. Some roles send to or receive from certain other roles more than others.

However, the stricter same-role null test was not supportive for K5.

The test asks:

> Do wallets transact with wallets in the same role more than expected if we randomly shuffle the role labels?

For K5:

- observed same-cluster transaction ratio: `0.2955`
- random-label null mean: `0.2982`
- p-value: `0.5644`

This means the observed same-role transaction concentration was not higher than the shuffled-label baseline.

So we cannot claim:

> K5 roles form strong same-role transaction communities.

The correct claim is:

> K5 role-to-role transaction flows are structured, but same-role transaction concentration is not stronger than a shuffled-label null test.

This does not invalidate K5.

It tells us that K5 should be interpreted as a behavioural-state taxonomy, not as a transaction-community partition.

## 8. K5 Temporal Validation

Temporal validation assigns each wallet-month in 2022 to the nearest full-year K5 prototype.

Main output:

`results/eoa_only_kmeans5/temporal_validation/eoa_k5_temporal_validation_report.md`

The main question is:

> Do wallets remain in the same behavioural state, or do they move between states over time?

The monthly self-transition rate is usually around `47%` to `52%`.

That means wallet behaviour is moderately persistent.

It is not completely fixed, but it is also not random.

The strongest K5 state-level self-transition probability is C2:

- C2 self-transition probability: `0.5580`

The weakest is C4:

- C4 self-transition probability: `0.2842`

This is important because C4 is called `persistent` based on its full-year feature profile, but it is not the most persistent monthly state.

So the correct wording is:

> C4 has a persistent full-year activity profile, but monthly state assignment shows that wallets do not always remain in C4.

## 9. Two-Step Return Behaviour

The two-step return test checks whether wallets leave a state and then return to it.

For example:

`C2 -> C0 -> C2`

This pattern means the wallet temporarily changed behaviour, then returned to its previous behavioural state.

For K5, the two-step return rates are usually around `30%` to `38%`.

The mean two-step return rate for K5 is:

`0.3421`

This supports the interpretation that many wallet transitions are temporary deviations rather than permanent changes.

This is one of the strongest temporal findings.

## 10. Academic Strengthening Pack

After the K5 decision, we added a final academic-strengthening pack.

Main output:

`results/k5_academic_strengthening/k5_academic_strengthening_report.md`

Script:

`src/validation/build_k5_academic_strengthening_pack.py`

This pack adds five things:

1. per-cluster stability,
2. consensus/co-membership stability,
3. wallet trajectory types,
4. monthly centroid drift,
5. final K5 role interpretation table.

These analyses make the project stronger because they stop us from saying only:

> K5 works overall.

Instead, we can say:

> Some K5 roles are more reliable than others, and each role has different temporal and stability behaviour.

## 11. Consensus And Co-Membership Stability

Consensus stability checks whether wallets stay grouped together when clustering is repeated with different random seeds.

Simple explanation:

> If two wallets are in the same cluster in the reference K5 result, do they tend to stay together across reruns?

Main output:

`results/k5_academic_strengthening/sampled_pair_comembership_consensus.csv`

Results:

- same-reference-cluster mean consensus: `0.6736`
- different-reference-cluster mean consensus: `0.1320`

This means wallets in the same reference cluster are much more likely to remain together than wallets from different clusters.

That supports K5 as a meaningful grouping structure.

However, the roles are not equally stable.

Within-cluster consensus by role:

- C0: `0.8999`
- C1: `0.6280`
- C2: `0.6555`
- C3: `0.6010`
- C4: `0.5803`

C0 is the strongest by co-membership consensus.

C4 is the weakest by this measure.

## 12. Per-Cluster Stability

The per-cluster stability table combines:

- wallet share,
- seed/subsample recovery,
- temporal persistence,
- centroid drift,
- trajectory behaviour,
- network position,
- reliability summary,
- interpretation caution.

Main output:

`results/k5_academic_strengthening/per_cluster_stability_table.csv`

Summary:

| Cluster | Label | Reliability | Main Caution |
|---:|---|---|---|
| C0 | small-value-flow | moderate | seed-sensitive in at least one rerun |
| C1 | value-scale-leaning | fragile | lower seed/subsample recovery |
| C2 | high-transaction, outflow-leaning | moderate | small role and higher centroid drift |
| C3 | high-transaction, large-value-flow, bursty-volatile | fragile | small role and seed-sensitive |
| C4 | persistent | fragile | low monthly persistence and higher centroid drift |

This is academically useful because it avoids overclaiming.

The correct interpretation is not:

> All five roles are equally strong.

The correct interpretation is:

> K5 is defensible overall, but individual roles vary in reliability.

## 13. Wallet Trajectory Types

Trajectory analysis converts each wallet's monthly state sequence into a readable behaviour pattern.

Main output:

`results/k5_academic_strengthening/trajectory_type_summary.csv`

Trajectory types:

- `returner`: leaves a role and later returns,
- `one_time_switcher`: changes role once,
- `persistent`: stays in the same role,
- `multi_step_mover`: changes through several states,
- `volatile_switcher`: changes often,
- `mostly_stable_with_noise`: mostly stays in one state with minor movement,
- `insufficient_observation`: observed in only one month.

Results:

| Trajectory type | Wallet share |
|---|---:|
| returner | 0.3481 |
| one-time switcher | 0.2438 |
| persistent | 0.1593 |
| multi-step mover | 0.1043 |
| insufficient observation | 0.0809 |
| volatile switcher | 0.0500 |
| mostly stable with noise | 0.0136 |

The largest group is `returner`.

This supports the two-step return finding.

Many wallets temporarily shift behaviour and then come back.

## 14. Monthly Centroid Drift

Centroid drift checks whether the meaning of a role changes across months.

Simple explanation:

> Does C0 in January still look like C0 in December?

Main output:

`results/k5_academic_strengthening/centroid_drift_summary_by_cluster.csv`

Mean L2 drift:

- C0: `2.9119`
- C1: `3.2243`
- C2: `4.8265`
- C3: `3.3041`
- C4: `3.7294`

C0 has the lowest drift, so it is the most consistent role over time.

C2 has the highest drift, so it is more context-sensitive.

This does not make C2 invalid.

It means C2 should be described carefully as a high-transaction outflow-leaning role whose monthly expression changes more than other roles.

## 15. Final K5 Role Interpretations

Main output:

`results/k5_academic_strengthening/final_k5_role_interpretation_table.csv`

### C0: Small-Value-Flow Wallets

C0 contains `776,004` wallets, about `31.8%` of the K5 EOA dataset.

These wallets have relatively low value flow and lower volatility.

C0 has strong co-membership consensus and the lowest centroid drift, but it is seed-sensitive in at least one rerun.

Best interpretation:

> C0 is a moderate-reliability low-value-flow behavioural state.

### C1: Value-Scale-Leaning Wallets

C1 contains `923,286` wallets, about `37.8%` of the K5 EOA dataset.

It is the largest role.

These wallets show stronger value-flow behaviour, especially net-flow-related features.

However, C1 has low seed/subsample recovery.

Best interpretation:

> C1 is a broad value-flow role, but it should be interpreted cautiously because it is less stable across reruns.

### C2: High-Transaction, Outflow-Leaning Wallets

C2 contains `154,864` wallets, about `6.3%` of the K5 EOA dataset.

These wallets have high transaction density and stronger outgoing behaviour.

C2 has the strongest monthly self-transition probability, but it also has high centroid drift.

Best interpretation:

> C2 is a moderate-reliability high-transaction outflow role, but its monthly expression changes more than other roles.

### C3: High-Transaction, Large-Value-Flow, Bursty-Volatile Wallets

C3 contains `183,079` wallets, about `7.5%` of the K5 EOA dataset.

These wallets combine high transaction activity, large value movement, and volatility.

C3 is small and seed-sensitive.

Best interpretation:

> C3 captures an intense bursty high-value behaviour pattern, but it is a fragile role and should not be overinterpreted.

### C4: Persistent Full-Year Activity Wallets

C4 contains `406,635` wallets, about `16.6%` of the K5 EOA dataset.

These wallets have high active-day and total-transaction features over the full-year profile.

However, C4 has low monthly self-transition probability.

Best interpretation:

> C4 has a persistent full-year activity profile, but it is not a highly persistent monthly state.

This wording is important because it avoids a contradiction between the feature label and the temporal evidence.

## 16. Main Findings After Contract Removal

The project's main findings after contract removal are:

1. EOA-only wallet behaviour supports several defensible cluster resolutions, not one universal K.

2. `K=4` is strongest as a conservative network-aligned taxonomy.

3. `K=5` is strongest as a richer behavioural role taxonomy.

4. `K=6` is useful as a fine-grained comparison, but weaker after contract removal.

5. K5 is better supported as a behavioural-state taxonomy than as a transaction-community partition.

6. Temporal behaviour is moderately persistent.

7. Two-step return behaviour is meaningful, showing that many wallets temporarily deviate and then return.

8. The K5 roles are not equally reliable, so the final paper should include role-specific cautions.

## 17. Safe Paper Claim

The safest paper claim is:

> After removing contract addresses, Ethereum EOA wallet behaviour supports several defensible role resolutions. A four-role solution provides the strongest conservative network-aligned taxonomy, while a five-role solution gives the best richer behavioural taxonomy. The K5 roles are feature-space meaningful and temporally structured, but network evidence is mixed and individual roles vary in stability. Therefore, the K5 result should be presented as a behavioural-state taxonomy, not as verified real-world identities or transaction communities.

## 18. What We Should Avoid Claiming

We should not claim:

> K5 is the true number of Ethereum wallet types.

We should not claim:

> K5 roles are verified real-world entities.

We should not claim:

> K5 roles form strong same-role transaction communities.

We should not claim:

> Event months caused specific transitions.

Instead, we should say:

> The results support a reproducible behavioural segmentation framework with calibrated evidence from feature space, temporal dynamics, network checks, and stability analysis.

## 19. Where To Look In The Repo

Start here:

- `results/k5_academic_strengthening/k5_academic_strengthening_report.md`
- `results/k5_academic_strengthening/final_k5_role_interpretation_table.csv`
- `results/eoa_k_model_selection/eoa_k_model_selection_report.md`
- `results/eoa_k4_k5_k6_comparison/eoa_k4_k5_k6_downstream_comparison.md`
- `results/eoa_only_kmeans5/temporal_validation/eoa_k5_temporal_validation_report.md`
- `results/eoa_only_kmeans5/network_validation/eoa_k5_transaction_network_validation_report.md`

For reproducibility:

- `docs/PIPELINE.md`
- `docs/SCRIPT_INDEX.md`
- `docs/OUTPUTS_CATALOG.md`
- `docs/FIGURE_TABLE_AUDIT.md`

## 20. Final One-Paragraph Summary

After removing smart contracts, the project became a cleaner EOA-only study of Ethereum wallet behaviour. We no longer defend the original mixed-address `K=6` result as the final answer. Instead, we compare several cluster resolutions and show that `K=4` is the strongest conservative network-aligned taxonomy, while `K=5` is the best richer behavioural taxonomy. The K5 roles are interpretable and temporally structured, with meaningful returner behaviour and role-specific stability patterns. However, network validation is mixed and some roles are fragile, so the final academic framing should describe K5 as a defensible behavioural-state taxonomy rather than a set of verified real-world wallet identities.
