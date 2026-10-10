# Temporal validation V2: professor Items 8, 10, 9

## Scope and decision

All K4/K5/K6 tests use the original monthly assignment method. Old results are untouched. Monthly states were reconstructed from complete wallet-hash daily partitions because the large legacy assignment CSVs are absent locally. Reconstruction must match all 36 monthly compositions (tolerance 1e-6), active-wallet counts and all 33 pair transition count matrices exactly before outputs are accepted.

Decision: retain original assignments and add the Item 8 limitation. Annualisation is not applied. The annual/monthly window mismatch exists in the code; composition differences are diagnostic, not causal proof of bias. Annual shares use all annual EOAs; monthly shares use active wallet-months, so activity selection also changes composition. A future annualisation decision requires professor review and recomputation of every temporal quantity.

Monthly states are assigned with prototypes and scaling fitted on full-year features. Features that sum over the observation window (counts, totals and active days) are smaller in a single month, which may bias monthly assignments toward lower-activity roles. Transition results should be read with this caveat.

## Annual versus pooled monthly shares

|   k |   state |   annual_share |   monthly_share |   share_difference |
|----:|--------:|---------------:|----------------:|-------------------:|
|   4 |       0 |      0.148531  |      0.0230212  |         -0.12551   |
|   4 |       1 |      0.395621  |      0.19145    |         -0.204171  |
|   4 |       2 |      0.374578  |      0.251944   |         -0.122633  |
|   4 |       3 |      0.0812699 |      0.533585   |          0.452315  |
|   5 |       0 |      0.317531  |      0.252146   |         -0.0653846 |
|   5 |       1 |      0.377797  |      0.21407    |         -0.163727  |
|   5 |       2 |      0.0633684 |      0.496274   |          0.432906  |
|   5 |       3 |      0.0749136 |      0.0230511  |         -0.0518625 |
|   5 |       4 |      0.16639   |      0.0144588  |         -0.151931  |
|   6 |       0 |      0.222839  |      0.123557   |         -0.0992824 |
|   6 |       1 |      0.304972  |      0.228659   |         -0.0763132 |
|   6 |       2 |      0.0614063 |      0.488749   |          0.427342  |
|   6 |       3 |      0.0699449 |      0.0203204  |         -0.0496244 |
|   6 |       4 |      0.130485  |      0.00945684 |         -0.121029  |
|   6 |       5 |      0.210352  |      0.129259   |         -0.0810936 |

## Chance-corrected persistence and return summary

|   k |   transition_observations |   observed_self_transition |   expected_self_transition |   cohen_kappa |   two_step_switcher_observations |   observed_return |   weighted_null_return |   two_step_significant_triples_raw |   two_step_significant_triples_holm |   total_triples |   permutations |
|----:|--------------------------:|---------------------------:|---------------------------:|--------------:|---------------------------------:|------------------:|-----------------------:|-----------------------------------:|------------------------------------:|----------------:|---------------:|
|   4 |               7.35155e+06 |                   0.51357  |                   0.346613 |      0.255524 |                      2.30333e+06 |          0.352879 |               0.282954 |                                 10 |                                  10 |              10 |            999 |
|   5 |               7.35155e+06 |                   0.500035 |                   0.323174 |      0.26131  |                      2.35216e+06 |          0.340609 |               0.262364 |                                 10 |                                  10 |              10 |            999 |
|   6 |               7.35155e+06 |                   0.46905  |                   0.285821 |      0.256559 |                      2.51453e+06 |          0.310505 |               0.223136 |                                 10 |                                  10 |              10 |            999 |

## Methods

Pairs include only wallets present in both adjacent calendar months; absence is missing, not a state. Expected agreement is the dot product of the pair-specific state marginals. Annual observed and expected rates are weighted by pair sample size, then kappa=(observed-expected)/(1-expected). This is not the mean of monthly kappas.

Triples include only wallets present in all three consecutive months, then restrict to s0 != s1 before any shuffling. Shuffle s2 only within the same s1 group among those switchers. This preserves the selected cohort's middle-to-final margins. Compute upper-tail p=(1+exceedances)/(B+1). Holm adjusts the ten triple tests separately for each k; raw results are also retained. Wallets recur across windows; no independence or unique-wallet interpretation of the pooled observation counts is claimed. Pooled return is descriptive; there is no invented pooled permutation p-value.

B=999; root seed=42; reproducible independent streams use SeedSequence([seed,k,triple_index]). Zero exceedances give the minimum attainable Monte Carlo p=1/(B+1); this does not identify the true tail probability. The analytical conditional-null expectation is also saved as an implementation check.

## Paper replacements and table handoff

Append to Section IV-F: Monthly states are assigned with prototypes and scaling fitted on full-year features. Features that sum over the observation window (counts, totals and active days) are smaller in a single month, which may bias monthly assignments toward lower-activity roles. Transition results should be read with this caveat.

Sections IV-F / V-E: The overall K5 self-transition rate is 50.00%, compared with 32.32% expected under independent consecutive states with the observed pair-specific marginals (Cohen's kappa=0.2613). Rates are weighted by the number of wallets observed in each pair and are subject to the monthly-scaling limitation.

Section IV-G: To test whether the initial state carries information about the final state beyond the middle state, we restrict to wallets observed in three consecutive months that changed state in the first transition. We permute final states within middle-state strata using B=999 permutations and report upper-tail Monte Carlo p-values and Holm correction across ten triples per k. This test cannot fully separate temporary excursions from stable differences between wallets, including regular alternation.

Section V-F: K5 returns to its initial state in 34.06% of eligible switcher observations, versus a weighted conditional-null mean of 26.24%. 10/10 triples are significant before correction and 10/10 after Holm correction. Report these as conditional return evidence, with the scaling caveat and wallet-heterogeneity limitation; do not claim proven temporary excursions.

Table III: merge temporal inputs with Person 2's final internal metrics; show observed (chance), kappa and raw/Holm significant triples. Table VII: use the weighted summary plus the existing state-level matrix; add chance agreement and kappa. Table VIII: use table_viii_k5_inputs.csv, with B, null mean, effect, raw and adjusted p-values.

No LaTeX manuscript exists in this checkout; these are replacement text and table inputs, not edits to a final manuscript. Table V and final model-selection wording remain with Person 2 / joint integration. Send claim-changing results to the professor before finalising claims; no message has been sent automatically.

## Reproduction

```powershell
python scripts/run_temporal_validation_v2.py --permutations 99 --out-dir results_v2/temporal_k4_k5_k6_smoke
python scripts/run_temporal_validation_v2.py --permutations 999
```

Local reconstruction cache is ignored by Git; compact CSVs and provenance manifest are retained. Source daily rows=39,853,742; annual wallets=2,443,868; buckets=512.

## Additional scaler provenance finding

The local EOA-only annual scaler does not reproduce legacy monthly state compositions
(K4 January maximum share difference 0.0464, with the same active-wallet count).
The legacy temporal / strengthening code references a mixed-population annual scaler.
That missing scaler was recovered from data/processed/wallet_kmeans6_expanded_daily_features.csv
using the original robust_scale_expanded_features.transform_series function and exact
full-population quartiles. This is not a refit on monthly data.
Only the recovered legacy scaler is accepted for these outputs after reconstruction checks.
The EOA-only feature-space scaler remains untouched. Both scaler populations are compared
in scaler_population_comparison.csv; replacing one silently would change the experiment.

This adds a population-scaling concern to the observation-window concern: the reproduced
monthly assignments use mixed-population scaling with EOA-only median prototypes.
Annual raw/scaled sample values identify the separate EOA scaler: annual_scaler_sample_check.csv
verifies all 33 features on the shared wallets in the first 500 annual raw/scaled rows.
The results are a transparent revalidation of the legacy assignment, not a correction of
these assignment biases. Professor review should consider consistent EOA scaling and
annualisation together before finalising temporal claims. If either changes, rerun all
transition, entropy, and return outputs and revise every affected paper number.

Additional Section IV-F wording: The legacy monthly assignment also uses scaling statistics
estimated on the mixed annual address population with EOA-only prototypes. This population
mismatch may further affect monthly assignments; temporal conclusions remain conditional
on this assignment procedure.
