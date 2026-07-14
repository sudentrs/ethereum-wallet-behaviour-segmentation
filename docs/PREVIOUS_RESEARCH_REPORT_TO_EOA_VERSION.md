# Applying The Previous Research Report To The Current EOA-Only Version

## Purpose

This document maps the earlier report, `research report.docx`, to the current version of the project.

The important change is that the project is no longer trying to defend the original mixed-address `K=6` result as the final answer.

After contract-address filtering, the current paper-facing version studies Ethereum externally owned accounts (EOAs) and compares several defensible role resolutions, especially `K=4`, `K=5`, and `K=6`.

The updated framing should be:

> Can Ethereum EOAs be organized into statistically defensible behavioural roles, and do those roles show evidence of feature-space separation, network structure, and temporal state dynamics?

## Short Answer

Yes, the previous report still applies, but it should be applied to the EOA-only version rather than copied directly.

Several recommendations from the old report have already been implemented.

The remaining work is mostly about making the results more paper-ready: per-cluster stability, consensus/co-membership analysis, clearer trajectory typologies, and final figure/table traceability.

## What Changed From The Old Report

The earlier report was written when the project was still centered on a six-cluster wallet taxonomy.

The new version is stronger academically because it includes a Gate 1 correction: contract addresses were removed, so the main analysis is based on EOAs only.

This changes the claim.

Old claim:

> `K=6` gives six validated Ethereum wallet roles.

Updated claim:

> EOA wallet behaviour supports several defensible role resolutions. `K=4` is the strongest conservative network-aligned taxonomy, `K=5` is the preferred richer behavioural taxonomy, and `K=6` is a useful fine-grained sensitivity comparison but is less stable.

## Mapping Of Previous Recommendations

| Previous recommendation | Current status | Evidence in repo | What it means now |
|---|---|---|---|
| Formal cluster stability analysis | Mostly applied | `results/eoa_k_model_selection/eoa_k_model_selection_report.md` | K values from 2 to 10 were tested using seed stability, silhouette, null tests, cluster-size gates, and feature-separation checks. |
| Per-cluster stability | Partially applied | Temporal reports and transition matrices | We have role persistence over time, but not yet a direct per-cluster seed/subsample stability table. This is still worth adding. |
| K sensitivity analysis | Applied | `results/eoa_k_model_selection/eoa_k_model_selection_report.md`; `results/eoa_k4_k5_k6_comparison/eoa_k4_k5_k6_downstream_comparison.md` | The project no longer depends on only asking whether `K=6` is good. It compares alternatives and gives a calibrated decision. |
| Monthly centroid drift analysis | Not fully applied | Temporal reports exist, but centroid drift is not a complete standalone output | We have monthly role states and transitions, but should still measure whether the feature definition of each role drifts over months. |
| Clear wallet trajectory analysis | Partially applied | `results/academic_paper_pack/two_step_return_null_tests_all_k.csv`; `results/academic_paper_pack/top_off_diagonal_transition_pathways_all_k.csv` | Two-step return behaviour is now tested statistically. A more readable trajectory taxonomy should still be added. |
| External label validation | Not applied | No known-address label table currently used | This remains optional and depends on whether reliable wallet labels can be collected. It would help interpretation but is not required for the core unsupervised contribution. |
| Formal role interpretation table | Partially applied | K reports, feature-space reports, network and temporal reports | The evidence exists, but it should be consolidated into one paper-ready role table for the chosen main K. |
| Careful limitations section | Applied in principle, should be carried into paper | `results/academic_paper_pack/paper_ready_synthesis.md` | The current reports correctly say these are behavioural states, not verified real-world identities, and avoid causal event claims. |

## What Has Already Been Strengthened In The New Version

### 1. Contract filtering

This is the biggest methodological improvement.

The old project mixed EOAs and contract addresses.

The current version removes contracts and studies actual externally owned wallets.

That makes the behavioural interpretation cleaner because contracts can behave differently from human-controlled or organization-controlled wallets.

Main guide:

- `docs/GATE1_EOA_ONLY_WORKFLOW.md`

### 2. K is now tested instead of assumed

The old report said that `K=6` should not be treated as the only possible solution.

The new version follows that advice.

The repo now compares `K=2` through `K=10`, then focuses downstream analysis on `K=4`, `K=5`, and `K=6`.

Main result:

- `K=2` and `K=3` are strongest for coarse separation.
- `K=4` is conservative and network-aligned.
- `K=5` is the preferred richer role taxonomy.
- `K=6` is more granular but less stable after contract removal.

Main files:

- `results/eoa_k_model_selection/eoa_k_model_selection_report.md`
- `results/eoa_k4_k5_k6_comparison/eoa_k4_k5_k6_downstream_comparison.md`

### 3. Feature-space proof structure was recreated

The earlier six-cluster proof style was not lost.

It was rebuilt for the EOA-only `K=4`, `K=5`, and `K=6` branches.

This includes:

- KNN feature-neighbourhood quality,
- feature-space modularity,
- attribute assortativity,
- Kruskal-Wallis feature-separation tests,
- pairwise Mann-Whitney and Cliff's-delta tests.

Main file:

- `results/academic_paper_pack/feature_space_proofs/feature_space_proofs_report.md`

Important interpretation:

These tests support feature-space separation.

They do not prove real-world identity labels.

### 4. Network and temporal validation were extended

The old report asked for validation beyond clustering.

The current version includes downstream comparison across `K=4`, `K=5`, and `K=6`.

Key result:

- `K=4` has the strongest transaction-network null result.
- `K=5` has the best richer taxonomy balance because it has stronger seed stability and useful temporal structure.
- `K=6` gives more detail but has weaker seed stability.

Main file:

- `results/eoa_k4_k5_k6_comparison/eoa_k4_k5_k6_downstream_comparison.md`

### 5. Two-step return behaviour is now statistically tested

The old report suggested clearer trajectory analysis.

The new version already tests one important trajectory pattern: wallets that leave a state and return to it two months later.

The test compares observed return rates against shuffled future-state labels.

This supports the idea that some transitions are temporary behavioural deviations, not permanent role changes.

Main files:

- `results/academic_paper_pack/two_step_return_null_tests_all_k.csv`
- `results/academic_paper_pack/academic_temporal_validation_pack.md`

### 6. Event-month analysis is included carefully

The current version adds event-adjacent checks for major 2022 crypto events.

This is useful, but it must be worded carefully.

The results can support contextual interpretation.

They do not support causal claims.

Correct wording:

> Major 2022 crypto events provide plausible context for some observed monthly state changes, but the present analysis treats them as candidate explanatory windows rather than causal drivers.

Main files:

- `results/academic_paper_pack/event_month_annotations.csv`
- `results/academic_paper_pack/event_adjacent_rank_tests_all_k.csv`

## What Still Remains To Apply

### Priority 1: Per-cluster stability table

The project currently reports overall seed stability and temporal persistence.

The missing piece is a table that says which individual roles are stable and which are fragile.

Recommended output:

| K | Cluster | Size share | Matched seed stability | Subsample recovery | Temporal persistence | Interpretation |
|---|---|---:|---:|---:|---:|---|

Why it matters:

This makes the paper more honest.

Instead of saying all roles are equally stable, we can say which roles are reliable and which should be interpreted cautiously.

### Priority 2: Consensus/co-membership matrix

This was one of the strongest previous suggestions.

For each K, rerun clustering across seeds/subsamples and build a matrix showing how often pairs of wallets stay together.

Recommended outputs:

- consensus heatmap,
- consensus score per K,
- ambiguous-wallet rate,
- role-level stability summary.

Why it matters:

This is a standard unsupervised-clustering stability argument and fits the paper direction very well.

### Priority 3: Monthly centroid drift

The current temporal work tracks wallet movements between roles.

Centroid drift would track whether the meaning of a role changes over time.

Recommended output:

| K | Cluster | Mean monthly centroid drift | Max drift month | Most drifting features | Interpretation |
|---|---|---:|---|---|---|

Why it matters:

If a role keeps similar feature values over time, it is more defensible as a stable behavioural state.

If a role drifts strongly, the paper should discuss it as a mixed or context-sensitive role.

### Priority 4: Wallet trajectory taxonomy

The two-step return test is already strong, but it is still statistical.

For the paper, we also need a readable taxonomy of wallet trajectories.

Suggested trajectory types:

- persistent wallets,
- one-time switchers,
- returners,
- gradual movers,
- volatile switchers,
- inactive/reactivated wallets.

Recommended output:

| Trajectory type | Definition | Share of wallets | Dominant start states | Common paths |
|---|---|---:|---|---|

Why it matters:

This turns temporal validation into a clearer behavioural story.

### Priority 5: Final paper role table

The evidence exists, but it is spread across outputs.

For the paper, choose the main taxonomy, probably `K=5`, and build one consolidated role table.

Recommended columns:

- role ID,
- wallet share,
- dominant engineered features,
- feature-space evidence,
- network behaviour,
- temporal persistence,
- common transitions,
- interpretation,
- caution.

Why it matters:

This is the table readers will use to understand the actual contribution.

### Priority 6: Optional external label validation

This is useful only if reliable labels can be obtained.

Possible sources:

- known exchange wallets,
- Etherscan labels,
- public DeFi protocol addresses,
- ENS-linked addresses,
- known scam or mixer lists.

Use this only as interpretive evidence.

Do not turn the paper into a supervised classification paper.

## What Should Not Be Repeated As-Is

### Do not simply re-defend mixed-address K=6

That version is now historically useful, but it should not be the main paper claim.

The paper should say the original analysis motivated the proof structure, but the final empirical analysis uses EOA-only data.

### Do not claim event causality without a real event-study design

The current event analysis is useful for context.

It is not enough to say Terra, Celsius, the Merge, or FTX caused specific transitions.

### Do not claim K=5 is the universal true number of roles

The defensible claim is narrower:

> Among tested EOA-only alternatives, `K=5` provides the best richer behavioural taxonomy, while `K=4` is the strongest conservative network-aligned taxonomy.

## Recommended Next Work Order

1. Build the per-cluster stability table.
2. Add consensus/co-membership stability analysis for `K=4`, `K=5`, and `K=6`.
3. Add monthly centroid drift analysis.
4. Convert monthly sequences into wallet trajectory types.
5. Create the final paper role table for the selected main K.
6. Update the figure/table audit so every number in the paper maps to a script and output file.

## Updated Contribution Statement

This project contributes an EOA-only Ethereum wallet segmentation framework that discovers behavioural roles from engineered transaction features and evaluates them through model-selection sensitivity, feature-space separation, transaction-network validation, temporal transition analysis, two-step return testing, and calibrated event-context checks.

The main academic contribution is not a claim that one cluster count is universally correct.

The contribution is a reproducible validation framework for deciding which behavioural wallet-role taxonomy is defensible under different analytical goals.
