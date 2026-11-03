# Ethereum Wallet Segmentation

This repository supports a reproducible study of Ethereum wallet behaviour from 2022 ERC-20 transfer activity.
The current manuscript uses a year-end code-free address cohort and a count/activity/direction feature representation that excludes pooled token amounts.

## Research Question

Can a large Ethereum wallet population be organized into behavioural states that remain interpretable under explicit cohort, initialization, feature-family, and temporal checks?

The study does not infer wallet ownership or real-world identity.
It does not claim that a k-means partition is a natural or permanent taxonomy.

## Current Main Result

The current paper uses 2,508,997 addresses with empty code at Ethereum block 16,308,189, the final block of 2022.
This is a year-end code-free cohort, not a claim that every retained address was an EOA for all of 2022.

The annual representation contains 16 count/activity/direction features and no pooled token-value features.
Across $k=2$--$6$, K3 is the selected working resolution because it is the most stable non-coarse alternative across three full-population seeds.
Matched-MiniBatchKMeans feature-family holdouts qualify the result: K3 depends especially on activity level and persistence/concentration features.

Shared monthly network samples compare annual K2--K6 at seed 492 and K3 at two additional seeds, with 9,999 common permutations and one 84-test Holm family. K3, K4 and K5 have corrected support in all twelve months; K2 has three supported months and K6 has none under the upper-tail test. K3 is not selected by maximizing network alignment.
Separately trained frozen monthly K2--K6 models use deterministically ordered January--June training samples and July--December evaluation. Twenty return tests form one temporal Holm family: K3--K6 each have four supported triples; the binary K2 conditional return null is structurally constant and uninformative.
Monthly state identifiers are deliberately distinct from annual K3 labels.

See `docs/VALIDATION_COMPLETION.md` and `docs/REPRODUCE_CURRENT_VALIDATION.md` for current results and reproduction commands. The previous unsorted monthly run and unmatched-estimator holdouts are retained as historical artifacts, not current evidence.

## Reproducible Outputs

Compact, tracked outputs for the current paper are in:

```text
results_v3/year_end_2022_full_cohort/       Cohort membership and block-scoped definition
results_v3/year_end_2022_count_cohort/      Manifests, annual tables, temporal tables, and figures
overleaf/main.tex                           Compilable manuscript source
```

The raw data and large derived matrices are intentionally excluded from Git.
They are required to rerun the pipeline locally.

## Main Scripts

```text
scripts/filter_year_end_count_features.py       Filter the feature table to the corrected cohort and safe feature set
scripts/scale_year_end_count_features.py        Robust-scale the 16 annual features
scripts/fit_year_end_annual_models.py           Fit K2--K6 annual k-means models across seeds
scripts/summarize_year_end_annual_models.py     Produce cluster sizes, profiles, and seed stability tables
scripts/run_year_end_k3_feature_holdouts.py     Test K3 sensitivity to prespecified feature-family removals
scripts/run_monthly_count_validation.py         Fit frozen count-only monthly states and held-out temporal tests
scripts/generate_year_end_count_figures.py      Generate manuscript figures from compact annual outputs
scripts/run_monthly_network_null_validation.py  Network null validator that accepts aligned NPY labels
scripts/run_year_end_network_comparison.py     Shared-sample annual K2--K6 and K3-seed network comparisons
scripts/finalize_year_end_validation.py         Validate completed families and publish compact artifacts
scripts/synchronize_manuscript_validation.py    Synchronize manuscript numbers with verified results
```

## Dataset

The study uses the ERC-20 Trading 2022 release from Harvard Dataverse.
See `overleaf/main.tex` for the formal citations and `docs/PIPELINE.md` for earlier extraction stages.

## Important Limits

- The cohort is code-free at one historical block, not verified as EOA at every historical transfer.
- ERC-20 amounts are excluded from the current main representation because pooled token units are not economically comparable.
- K3 is a reproducible working segmentation, not ground truth.
- Monthly states are conditional on active wallet-months; absence is not modelled as a state.
- The network result covers only transfers with two cohort endpoints (13.7%--19.3% of raw monthly transfers) and is evidence of label--network alignment, not causality or community identity.

Older `results/` and `results_v2/` outputs are retained for provenance only.
They use earlier cohort and/or value-feature choices and are not evidence for the current manuscript.
