## Paper replacements and table handoff

Append to Section IV-F: Monthly states are assigned with prototypes and scaling fitted on full-year features. Features that sum over the observation window (counts, totals and active days) are smaller in a single month, which may bias monthly assignments toward lower-activity roles. Transition results should be read with this caveat.

Sections IV-F / V-E: The overall K5 self-transition rate is 50.00%, compared with 32.32% expected under independent consecutive states with the observed pair-specific marginals (Cohen's kappa=0.2613). Rates are weighted by the number of wallets observed in each pair and are subject to the monthly-scaling limitation.

Section IV-G: To test whether the initial state carries information about the final state beyond the middle state, we restrict to wallets observed in three consecutive months that changed state in the first transition. We permute final states within middle-state strata using B=999 permutations and report upper-tail Monte Carlo p-values and Holm correction across ten triples per k. This test cannot fully separate temporary excursions from stable differences between wallets, including regular alternation.

Section V-F: K5 returns to its initial state in 34.06% of eligible switcher observations, versus a weighted conditional-null mean of 26.24%. 10/10 triples are significant before correction and 10/10 after Holm correction. Report these as conditional return evidence, with the scaling caveat and wallet-heterogeneity limitation; do not claim proven temporary excursions.

Table III: merge temporal inputs with Person 2's final internal metrics; show observed (chance), kappa and raw/Holm significant triples. Table VII: use the weighted summary plus the existing state-level matrix; add chance agreement and kappa. Table VIII: use table_viii_k5_inputs.csv, with B, null mean, effect, raw and adjusted p-values.

No LaTeX manuscript exists in this checkout; these are replacement text and table inputs, not edits to a final manuscript. Table V and final model-selection wording remain with Person 2 / joint integration. Send claim-changing results to the professor before finalising claims; no message has been sent automatically.
Additional Section IV-F wording: The legacy monthly assignment also uses scaling statistics
estimated on the mixed annual address population with EOA-only prototypes. This population
mismatch may further affect monthly assignments; temporal conclusions remain conditional
on this assignment procedure.
