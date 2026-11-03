# Corrected-cohort count-signal branch

This branch reconstructs the full 2022 daily-count signal for the same 2,508,997
year-end code-free addresses used by the annual, network and monthly analyses.
It does not reuse the old EOA-only spectral assignments, pooled amount signals,
or the old 500-wallet timing test. Completion is established only by
`results_v3/year_end_2022_count_cohort/signals/manifest.json` with `complete: true`.

## Run

From the repository root, with requirements installed:

```powershell
python scripts/run_year_end_signal_validation.py
python -m unittest tests.test_year_end_signals
python scripts/publish_year_end_signal_manuscript.py
python -m scripts.audit_tcss_manuscript
```

The publisher edits the existing `overleaf/main.tex` and does not compile it.
It refuses a second automatic integration, so a later revision must inspect the
current source before changing narrative. The former extended-body builder is
blocked once signal results exist, to prevent a stale template from removing
these findings. The original pre-integration source is retained under `tmp/`.

For a rerun with changed sources, code or settings, use fresh `--cache` and
`--out` directories. Unchanged inputs can resume monthly checkpoints. The
3.66-GB uint32 count matrix and feature/model/label arrays remain under ignored
`data/interim/year_end_2022_signals/`; compact results and provenance remain in
`results_v3/year_end_2022_count_cohort/signals/`.

## Population and measurements

The candidate list is not redefined. Exact normalized membership is checked
against the completed historical cohort export, while annual feature-table row
order determines every signal and label row. All twelve monthly source hashes,
the cohort hash, annual row-source hash, label hashes, settings and producer-code
hash are recorded. Each full monthly input is checked for valid address and
month, finite nonnegative integral counts, uint32 representability and unique
wallet-day rows before its cohort join. Missing daily observations become zero.
Every reconstructed annual sum must equal its annual feature-source total.

Six time-domain variables cover active fraction, longest active/inactive run,
active/inactive switches, peak-day count share and calendar-day count CV.
Seven frequency variables cover normalized low/medium/high-frequency power,
weekly/monthly bands, peak-power share and entropy. The FFT uses mean-centred
log1p daily counts and excludes DC. Subtracting the first transformed value
before centring avoids floating-point residual power in exactly constant
signals. Independent tests cover constant signals, an exact Fourier bin,
single-impulse uniform power, run lengths, histogram preservation, agreement
invariance and the joint Holm correction.

Zero-power wallets are counted and excluded from both time and frequency fits
so their comparisons have exactly the same population. This exclusion is not a
claim that such addresses have no activity. Source-wide summary statistics and
cohort accounting still include them.

## Fits and comparisons

Time and frequency representations have separate full-eligible-population
RobustScalers; only time-domain CV receives log1p before scaling. Both use the
same seed-492 uniform 100,000-address centroid-training sample. Each fits K2--K6
and seeds 492--494 with MiniBatchKMeans (n_init 10, batch 8,192, max_iter 200),
then assigns every eligible address. A separate fixed uniform 3,000-address
sample supplies seed-492 silhouette scores. Full-population ARI, NMI and
Hungarian-matched agreement compare seed pairs and representations.

The 75 cross-representation records comprise 25 annual/time, 25 annual/frequency
and 25 time/frequency comparisons. These are descriptive comparisons, not
75 hypothesis tests. K3 overlap figures are illustrations and do not establish
that three is the optimal signal resolution. Full K2--K6 profiles and overlap
tables remain available.

## Timing null

A separate uniform 2,000-address cohort sample is selected before zero-power
exclusion. With seed 692, 999 within-wallet permutations reorder all 365 daily
counts, including zeros. The entire daily-count histogram is preserved.
Upper-tail tests evaluate sample-mean low-frequency power, peak-power share and
negative entropy. One Holm family covers these three tests; it is separate
from the existing 84 network tests and 20 held-out monthly return tests.

This is evidence about ordering conditional on wallet count histograms. It is
not a recurring-cycle test, a wallet-by-wallet significance analysis, a
prospective prediction result, an economic-value interpretation or independent
external ground truth. Full-year signal fitting is kept distinct from the
January--June-trained, July--December-evaluated monthly states.
