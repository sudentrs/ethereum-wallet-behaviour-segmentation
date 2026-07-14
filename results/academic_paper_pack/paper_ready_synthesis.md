# Paper-Ready Synthesis: EOA Wallet Behaviour Roles

## Research Question

Can Ethereum externally owned accounts be organized into statistically defensible behavioural roles, and do those roles show evidence of feature-space separation, network structure, and temporal state dynamics?

## Why This Version Is Different From The Earlier Six-Cluster Story

The earlier `K=6` work was valuable because it established the proof structure:

- cluster profile interpretation,
- feature-space statistical separation,
- feature-space KNN/network validation,
- transaction-network validation,
- temporal state-transition matrices,
- state persistence,
- transition pathways.

However, the later Gate 1 check showed that the mixed-address six-cluster result included contract contamination. After removing contract addresses, the paper-facing analysis must use the EOA-only branch.

The current academic framing is therefore not:

> K=6 is the validated final answer.

The stronger paper framing is:

> After contract removal, multiple role resolutions are defensible for different research purposes. `K=4` is the strongest conservative network-aligned taxonomy, while `K=5` is the preferred richer behavioural taxonomy. `K=6` is useful as a fine-grained sensitivity comparison but is less stable.

## Main Evidence Package

### 1. Model selection

Main file:

- `results/eoa_k_model_selection/eoa_k_model_selection_report.md`

Result:

- `K=2` and `K=3` are strongest for coarse separation.
- `K=4` is conservative and network-aligned.
- `K=5` is the preferred richer behavioural taxonomy.
- `K=6` is more granular but less stable.

### 2. K4/K5/K6 downstream comparison

Main file:

- `results/eoa_k4_k5_k6_comparison/eoa_k4_k5_k6_downstream_comparison.md`

Key table:

| K | Seed stability ARI | Network null p-value | Mean temporal self-transition | Mean two-step return | Interpretation |
|---:|---:|---:|---:|---:|---|
| 4 | 0.5894 | 0.0099 | 0.5136 | 0.3545 | strongest conservative network-aligned taxonomy |
| 5 | 0.7126 | 0.5644 | 0.4999 | 0.3421 | best richer role-taxonomy balance |
| 6 | 0.4848 | 0.0495 | 0.4691 | 0.3118 | exploratory fine-grained taxonomy |

### 3. Feature-space proof replication

Main file:

- `results/academic_paper_pack/feature_space_proofs/feature_space_proofs_report.md`

This reproduces the old six-cluster proof style for the EOA-only K4/K5/K6 branch.

Feature-space KNN network quality:

| K | Sample wallets | Intra-cluster KNN edge ratio | Label modularity | Attribute assortativity |
|---:|---:|---:|---:|---:|
| 4 | 20,000 | 0.8707 | 0.6201 | 0.8274 |
| 5 | 25,000 | 0.8539 | 0.6535 | 0.8173 |
| 6 | 30,000 | 0.8477 | 0.6806 | 0.8171 |

Interpretation:

The EOA-only clusters are visible in local feature-space neighbourhoods. This supports the claim that the clusters are not arbitrary labels in the engineered feature space.

### 4. Temporal transition matrices and state dynamics

Main file:

- `results/academic_paper_pack/academic_temporal_validation_pack.md`

Generated visuals:

- `results/academic_paper_pack/k4/k4_monthly_state_shares_events.png`
- `results/academic_paper_pack/k5/k5_monthly_state_shares_events.png`
- `results/academic_paper_pack/k6/k6_monthly_state_shares_events.png`
- `results/academic_paper_pack/k4/k4_self_transition_event_pairs.png`
- `results/academic_paper_pack/k5/k5_self_transition_event_pairs.png`
- `results/academic_paper_pack/k6/k6_self_transition_event_pairs.png`
- `results/academic_paper_pack/k4/k4_transition_residual_heatmap.png`
- `results/academic_paper_pack/k5/k5_transition_residual_heatmap.png`
- `results/academic_paper_pack/k6/k6_transition_residual_heatmap.png`

The transition matrices show moderate persistence, not fixed identities.

For `K=5`, the strongest off-diagonal pathways are:

| From state | To state | Probability |
|---:|---:|---:|
| C0 | C2 | 0.3686 |
| C1 | C2 | 0.3386 |
| C4 | C1 | 0.2823 |
| C3 | C1 | 0.2781 |
| C2 | C0 | 0.2362 |

Interpretation:

The roles should be described as behavioural states. Wallets often persist, but movement between states is common and structured.

### 5. Two-step return test

The two-step return test directly checks whether a wallet can leave a state and return to it two months later.

Method:

For wallets with states at months `t`, `t+1`, and `t+2`, take wallets where:

`state_t != state_t1`

Then test whether:

`state_t2 == state_t`

more often than expected after shuffling `state_t2` labels among wallets that left.

Result:

For almost all K/month triplets, the observed two-step return rate is significantly above the shuffled null.

For `K=5`, the observed return rates are usually around `0.30` to `0.38`, while null expectations are lower. This supports the temporary-deviation interpretation:

> Some wallets do not permanently change behavioural type. They temporarily deviate and then return to a previous behavioural state.

### 6. Event-month contextual analysis

Event months used:

| Month | Candidate context | Interpretation boundary |
|---|---|---|
| 202205 | Terra/UST-LUNA collapse | market-wide stress candidate |
| 202206 | Celsius/liquidity stress | centralized-lending stress candidate |
| 202209 | Ethereum Merge | Ethereum protocol event |
| 202211 | FTX collapse | market-wide exchange crisis |

Important caution:

The tests do not prove causality.

They only ask whether event-adjacent months are unusual compared with other month pairs in 2022.

Result:

Event-adjacent rank tests do not show a strong enough pattern to claim direct causal effects. Some event months, especially `202206`, `202209`, and `202211`, show visible state-share or persistence deviations in some K settings, but the sample of monthly pairs is small.

Paper wording should be:

> Major 2022 crypto events provide plausible context for some observed monthly state changes, but the present analysis treats them as candidate explanatory windows rather than causal drivers.

Do not write:

> Terra, the Merge, or FTX caused these transitions.

## Recommended Paper Argument

The paper should make three claims.

### Claim 1: EOA wallet roles are feature-space meaningful

Supported by:

- KMeans model-selection checks,
- feature-profile interpretation,
- Kruskal-Wallis tests,
- pairwise Mann-Whitney and Cliff's-delta tests,
- KNN feature-neighbourhood modularity.

### Claim 2: There is no single universal K

Supported by:

- K4/K5/K6 comparison,
- K4 stronger network-null result,
- K5 stronger richer-taxonomy balance,
- K6 finer but less stable.

### Claim 3: Wallet roles behave as dynamic behavioural states

Supported by:

- monthly transition matrices,
- moderate self-transition rates,
- strongest off-diagonal pathways,
- two-step return null tests.

## Suggested Abstract-Level Result Sentence

After filtering contract addresses, Ethereum EOA behaviour supports several defensible role resolutions rather than a single universal cluster count. A four-role solution provides the strongest conservative network-aligned taxonomy, while a five-role solution offers the best balance between interpretability, seed stability, cluster size, and temporal persistence. Monthly transition analysis shows that wallet roles behave as dynamic behavioural states: many wallets persist, many move through structured transition pathways, and two-step return tests indicate that temporary deviations followed by return are more common than expected under shuffled future states.

## What Still Needs To Be Done Before Submission

1. Convert this synthesis into a formal paper structure: introduction, related work, methods, results, discussion, limitations.
2. Decide whether the main paper uses `K=5` with `K=4` as robustness, or presents both as complementary resolutions.
3. Add a proper event-study design only if making causal claims about Terra, Celsius, the Merge, or FTX.
4. Create a final figure/table map so every reported number points to a script and output file.
