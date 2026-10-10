# Temporal V2 handoff

Guide Items 8, 10 and 9 are implemented using the limitation path for monthly scaling.
The existing monthly assignment method is retained; final claims require professor review.
Read temporal_validation_v2_summary.md and paper_replacement_paragraphs.md before copying numbers.

Reproduce from the repository root:

```powershell
python scripts/test_temporal_validation_v2.py
python scripts/recover_legacy_temporal_scaler.py
python scripts/run_temporal_validation_v2.py --permutations 99 --out-dir results_v2/temporal_k4_k5_k6_smoke
python scripts/package_temporal_tables_v2.py --out-dir results_v2/temporal_k4_k5_k6_smoke
python scripts/run_temporal_validation_v2.py --permutations 999
python scripts/package_temporal_tables_v2.py
```

Required local inputs: complete 512 daily_wallet_partitions, recovered legacy annual scaling statistics,
K4/K5/K6 median prototypes, annual cluster sizes and legacy compact temporal outputs.
Large state CSVs and K4/K6 wallet-label CSVs are not required: states are reconstructed,
then verified against monthly compositions and every pair and triple count.
The ignored NPZ cache stores aligned wallet rows with -1 for absence, across twelve months
and three resolutions. It never treats inactivity as a behavioural state.

Table III temporal inputs are partial: Person 2 must supply the final internal metrics,
including sampled silhouette mean plus standard deviation, before joint integration.
Table VII uses table_vii_metrics.csv and table_vii_state_profiles.csv.
Table VIII uses table_viii_k5_inputs.csv (all K comparisons are in two_step_stratified.csv).
No manuscript was edited, and no results were sent or pushed automatically.
The legacy mixed-population scaler differs from the EOA-only feature-space scaler.
See scaler_population_comparison.csv and the additional provenance finding in the summary.
Old results remain unchanged. Percentages in CSVs are fractions; multiply by 100 for display.
Pooled counts are wallet-window observations, not unique-wallet counts.
