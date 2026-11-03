# Current Manuscript Status

`overleaf/main.tex` is the current manuscript.
It is based only on the year-end code-free cohort and the count/activity/direction representation documented in `results_v3/year_end_2022_count_cohort/`.

## Claims Supported by Tracked Results

- The year-end code-free cohort contains 2,508,997 addresses from an initial 2,738,243-address universe.
- Annual K3 is highly stable across the three fitted seeds, whereas annual K4--K6 are less stable.
- Matched-estimator K3 holdouts show dependence on activity level and persistence/concentration features; the labels are representation-specific, not ground truth.
- Shared-sample annual network tests cover K2--K6 seed492 and K3 seeds493/494: 84 tests, 9,999 permutations, global Holm correction. K3/K4/K5 seed492 have 12 supported months, K2 has 3, K6 has 0. All three K3 seeds have 12 supported months.
- Frozen monthly K2--K6 models use sorted wallet IDs before training sampling. K3--K6 show above-null two-step return in all four held-out triples after a 20-test temporal Holm correction. K2's within-middle-state return null is degenerate, so p=1 is uninformative.
- The original filtered features and scaled matrix were reproduced exactly. Thirteen of fifteen annual label arrays matched archived hashes; K3 seed494 and K6 seed493 are explicitly identified as reproduced fits.

Current compact evidence and provenance are recorded in `results_v3/year_end_2022_count_cohort/validation_completion.json`, `network_comparison/`, `monthly_k2_k6/`, and `annual/`. `monthly_k3/` is a K3 excerpt retaining the global temporal correction.

## Claims Deliberately Excluded

- Permanent EOA identity or ownership claims.
- Economic claims based on pooled ERC-20 token amounts.
- Causal claims about why same-state wallets interact, or claims about the full ERC-20 network beyond the retained cohort subgraph.
- A claim that K3 is Ethereum's unique or natural number of wallet types.

## Before Submission

1. Audit historical address code at transfer-time or defined monthly block boundaries if the paper needs a stronger EOA statement.
2. Rebuild a token-aware economic representation before making any value-flow interpretation.
3. Tag a commit only after reproducing the compact tables and compiling the manuscript from a clean checkout.

`docs/REVIEW_REVISION_STATUS.md` records the older K4/K5/K6 review path and is retained only as project history.

## Current source and signal extension

The editable source is `overleaf/main.tex`, using IEEEtran journal format on
Letter paper with `overleaf/figures_current/` assets. Old PDF/ZIP exports and the
`extended_body.tex` template predate the signal extension. They must not
replace the edited source. No compile or page-count certification is performed
for this revision, following the user's instruction.

The signal reconstruction, K2--K6 time/frequency fits, timing nulls and
cross-representation comparisons are documented in `YEAR_END_SIGNAL_VALIDATION.md`.
Completion is certified by `signals/manifest.json` only after the full run passes.
Previous-cohort Fourier results remain excluded; new results are calculated
from the same year-end cohort and validated daily sources.

## Completed signal extension

`results_v3/year_end_2022_count_cohort/framework_validation_completion.json`
records completion of the corrected-cohort annual, network, monthly and signal
branches. All 2,508,997 daily signals were reconstructed; 41,552,909 eligible
wallet-day rows contain 189,526,795 wallet-record count incidences. Annual sums
match the annual source exactly for every address, with no zero-power exclusions.
Thirty signal fits, 75 cross-representation comparisons and three timing-null
tests are complete. All 41 tests and the combined manuscript/provenance audit
pass. The source has not been compiled or page-count certified.

Annual K3 versus frequency K3 has ARI 0.249552 and NMI 0.115555; agreement is
partial. Frequency K3 seed ARI is 0.882--0.934, whereas time K3 is 0.197--0.639.
All three sample-mean timing summaries have Holm p=0.003 under 999 within-wallet
histogram-preserving permutations on 2,000 uniformly sampled addresses. These
findings do not establish recurring cycles or one shared taxonomy.
