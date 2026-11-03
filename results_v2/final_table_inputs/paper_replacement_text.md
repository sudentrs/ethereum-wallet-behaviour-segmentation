# Manuscript integration text

These paragraphs are replacements prepared from v2 results, not edits to the absent manuscript. Confirm claim changes with the professor before submission. Do not interpret the checklist below as a completed manuscript review.

## Abstract: validation sentence

We evaluate the role taxonomy using additional evidence beyond the clustering objective: feature profiles, transaction-network structure, monthly state transitions, two-step return behaviour, and full-population temporal signal analysis. For K5, same-role concentration is significant in one of twelve monthly networks after Holm correction. Temporal results remain conditional on the monthly assignment procedure.

## IV-C and V-B: model selection

We select k = 5 as the main descriptive taxonomy because it has the highest seed stability (ARI = 0.713) and provides more detailed roles than k = 4. K4 has stronger same-role network evidence (12/12 significant months after Holm correction, compared with 1/12 for K5) and higher average feature-holdout recovery. Chance-corrected persistence is similar, with Cohen's κ = 0.256 for K4 and 0.261 for K5. We therefore retain K4 as a conservative comparison and do not describe K5 as the statistically strongest taxonomy.

Internal silhouette and Davies–Bouldin results must come from internal_metrics.csv. A missing-original-label status means the requested experiment is incomplete, not zero. Do not substitute seed-to-seed score dispersion for sampling dispersion. Profile heatmaps show robust-scaled median feature values and use the existing v2 PDFs.

## IV-E and V-D: network

We analyse all labelled transfers between distinct sender and recipient addresses in each of the twelve monthly ERC-20 transfer networks of 2022. For each month and k, B = 999 permutations shuffle wallet labels while retaining the edges. We calculate upper-tail Monte Carlo p-values as (1 + the number of null ratios at least as large as the observed ratio)/(B + 1), apply Holm correction across twelve months per k, and report Fisher combined p-values. The figures use results_v2/network_k4_k5_k6_B999/ exclusively.

The Holm-significant month counts are 12/12, 1/12 and 11/12 for K4, K5 and K6 respectively. The corresponding mean observed-minus-null ratios are 0.109621, 0.004704 and 0.040289. The full-year K5 mixing figure shows log2(observed/expected), where expected counts preserve role-level outgoing and incoming margins. Full-year K5 assortativity is −0.0243. The mixing-margin expectation and shuffled-wallet-label null answer different questions and should be described separately.

## IV-F, V-E: monthly assignment and transitions

Monthly states are assigned with full-year prototypes and scaling. Features that accumulate over the observation window are smaller in a month, which may bias monthly assignments. The reconstructed legacy method also combines scaling estimated on the mixed annual address population with EOA-only prototypes. Temporal results remain conditional on this method; the diagnostic and chance correction do not remove these assignment concerns. Absence in a month is missing data, not a behavioural state.

Among wallets present in each adjacent pair, K5 observed self-transition is 50.00%, compared with 32.32% expected from independent states with the pair-specific marginals (Cohen's κ = 0.2613). Annual observed and expected rates are weighted by pair size before computing κ. Monthly composition differences also reflect selection of active wallet-months and do not alone establish causal scaling bias.

## IV-G, V-F: two-step returns

We retain wallets present in three consecutive months and restrict the cohort to those changing state on the first transition. We then permute the final state only within the same middle-state group among these switchers, using B = 999 permutations. This preserves the selected cohort's middle-to-final margins. The initial state may carry additional information about the final state, but stable wallet heterogeneity and alternation cannot be separated fully from temporary excursions.

K5 observed return is 34.06%, compared with a weighted stratified-null mean of 26.24%. All ten triples are significant after Holm correction. Each raw Monte Carlo p-value reaches the attainable resolution 1/(999 + 1) = 0.001 (zero exceedances); adjusted p-values are 0.010. This resolution does not identify the true tail probability. Counts pooled over windows are observations, not distinct wallets.

## IV-D, V-C and V-I: persistence holdout

The persistence holdout removes active days, activity span, activity density, the incoming/outgoing/both active-day counts, and their three active-day ratios: nine features in total. All holdouts use the same MiniBatchKMeans settings. K5 persistence-holdout ARI is 0.4126, NMI is 0.4288, and agreement after Hungarian matching is 64.36%. Because active days and activity span also enter annual clustering, part of the association between K5 and time-domain states is expected by construction. Table V should contain the five holdout rows; the all-features baseline is a separate reference.

## Table IV and role descriptions

C2: concentrated transaction activity over few days (median 3 active days, 15 total transactions and 5 transactions per active day). Do not describe this as persistent dense activity throughout the year.

C4: recurrent activity with the highest median active-day count among the five roles (29 days, 65 transactions and 2.29 transactions per active day). Do not describe it as continuous full-year activity.

Flow medians are source transfer-value aggregates. The checked daily conversion sums the source value without token-price conversion; unit provenance for these exact annual inputs has not been established. Do not report these as USD, ETH or economically comparable values across tokens. Even decimal-normalised quantities are not comparable across unlike tokens. Directional names need direction-specific evidence; differences between inflow/outflow medians are not the median net flow.

## IV-H and V-G: coefficient of variation

The transaction-count coefficient of variation is σ/μ, calculated from daily transaction counts on active days only. The implementation uses population standard deviation (ddof = 0); wallets with zero mean receive zero. It is not the bounded burstiness coefficient (σ − μ)/(σ + μ). Values such as TD4 = 1.016 can therefore exceed one. The feature values and clustering are retained.

## IV-I: signal selection score

Selection score = silhouette + 0.25 × mean seed ARI − max(0, largest cluster share − 0.75) − max(0, 0.01 − smallest cluster share). Missing silhouette is replaced by −1; missing stability is replaced by zero. Cluster entropy is descriptive and is not included in this score. selection_score_audit.csv verifies all twelve recorded candidates. This score selects temporal signal models and is not the annual K5 selection criterion.

## V-H: spectral terminology

Use spectral instead of wavelength, F0–F2 instead of W0–W2, and concentrated activity instead of slow-cycle rhythm. Use the selected K3 spectral profile, not the legacy K5 spectral profile. For a 365-day signal, concentration in low-frequency components indicates activity concentrated within the observation year; a period near the observation window does not demonstrate a recurring annual cycle. Do not infer a periodic cycle from the mean dominant period across wallets.

## Table XI caption

Dominant time-domain state within each Behaviour K5 role. Active days and Switches are arithmetic means among wallets in that dominant TD subgroup, not among all wallets of the K5 role. The subgroup count and within-role share are reported. The legacy total_tx_median is a weighted average of chunk medians and is excluded from the new export.

## EOA limitation

Contract filtering excludes smart-contract wallets, so the taxonomy describes externally owned accounts. Bytecode-based classification applies at the queried block rather than necessarily at each historical transfer. Addresses whose code is empty at query time may not have been EOAs throughout the observation period.

## Discussion and Conclusion

K5 offers a stable descriptive vocabulary, while K4 provides stronger conservative network and feature-holdout evidence. Chance-corrected persistence and stratified returns support conditional temporal structure, subject to observation-window scaling, scaler-population mismatch and wallet heterogeneity. These analyses do not establish independent validation or causality.

## Remaining manuscript checks

The main LaTeX and bibliography are absent. Once supplied, integrate these inputs and cite every figure/table, add verified dataset DOI and references, check the venue's anonymity/template/page rules, remove stale numbers and event-adjacent promises, and compile with no undefined references. Review vector figure readability and embedded fonts in the final PDF. No professor message has been sent.
