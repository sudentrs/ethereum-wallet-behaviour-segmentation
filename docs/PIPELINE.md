# Analysis Pipeline

This guide explains how the current EOA-only Ethereum wallet segmentation paper is reproduced from raw ERC-20 transfer data to paper figures.

The repository contains the scripts and selected compact outputs. It does not contain raw monthly transfer files, large intermediate parquet files, large wallet-label CSVs, or API keys.

## Inputs

Required local inputs:

- ERC-20 Trading 2022 monthly transfer files from Harvard Dataverse.
- A local working data directory such as `data/raw/` or `dataverse_files/`.
- An Ethereum RPC URL if contract/EOA filtering must be regenerated.

Important dataset citation:

- `somin2025erc2022`: ERC-20 Trading 2022, Harvard Dataverse, DOI `10.7910/DVN/5P82QC`.

## Stage 0: Raw Transfer Preparation

Goal: convert monthly ERC-20 TSV files into cleaner tabular files and wallet-day records.

Main scripts:

- `src/data_preparation/extract_erc20_tsv_to_parquet.py`
- `src/data_preparation/reformat_tsv_to_wallet_direction_rows.py`
- `src/data_preparation/aggregate_wallet_daily_flows.py`
- `src/data_preparation/merge_monthly_daily_wallet_files.py`
- `src/data_preparation/add_wallet_daily_netflow.py`

Typical commands:

```powershell
python src/data_preparation/extract_erc20_tsv_to_parquet.py --input-tsv data/raw/202201.tsv --output-dir data/interim/erc20_parquet/202201
python src/data_preparation/reformat_tsv_to_wallet_direction_rows.py --input-tsv data/raw/202201.tsv --output-csv data/interim/wallet_202201.csv
python src/data_preparation/aggregate_wallet_daily_flows.py --input-glob "data/interim/wallet_2022*.csv" --output-dir data/processed/wallet_daily
python src/data_preparation/merge_monthly_daily_wallet_files.py --input-glob "data/processed/wallet_daily/*_daily.csv" --output-csv data/processed/wallet_daily_2022.csv
python src/data_preparation/add_wallet_daily_netflow.py --input-csv data/processed/wallet_daily_2022.csv --output-csv data/processed/wallet_daily_2022_netflow.csv
```

## Stage 1: EOA Filtering

Goal: remove smart-contract addresses before the main wallet-role analysis.

Main script:

- `src/validation/eoa_contract_contamination_check.py`

Method:

- Query `eth_getCode` at the latest block.
- Empty bytecode is classified as EOA.
- Non-empty bytecode is classified as contract.

Paper caveat:

- This classification reflects bytecode status at query time, not necessarily at the historical block of each 2022 transfer.
- User-controlled smart-contract wallets can be excluded by this filter.

## Stage 2: Feature Engineering And Scaling

Goal: transform wallet-day activity into wallet-level behavioural features and robust-scaled feature matrices.

Main scripts:

- `src/features/build_full_kmeans6_expanded_features.py`
- `src/features/robust_scale_expanded_features.py`
- `src/validation/filter_eoa_only_features.py`

Feature families used in the paper include:

- Activity level
- Value-flow scale
- Directionality
- Volatility and concentration
- Temporal persistence

Expected outputs include robust-scaled EOA feature tables and scaling statistics. Large feature tables are not committed.

## Stage 3: EOA-Only K4/K5/K6 Clustering

Goal: compare candidate annual role taxonomies.

Main scripts:

- `src/clustering/run_eoa_only_kmeans.py`
- `src/clustering/eoa_only_k_sensitivity.py`
- `src/clustering/describe_eoa_only_clusters.py`

Current interpretation:

- K4: conservative comparison with strongest same-role network-null evidence.
- K5: main descriptive taxonomy with the highest seed stability and richer role vocabulary.
- K6: finer-resolution sensitivity comparison with lower seed stability.

Large wallet-label CSVs are intentionally not tracked in GitHub. They should be regenerated locally or shared separately.

## Stage 4: Feature And Role Interpretation Checks

Goal: test whether the annual taxonomy is interpretable and whether K5 survives feature-family perturbations.

Main script:

- `scripts/run_feature_role_checks_v2.py`

Important outputs:

- `results_v2/feature_role_checks/internal_metrics_k4_k5_k6.csv`
- `results_v2/feature_role_checks/feature_holdout_summary_k4_k5_k6.csv`
- `results_v2/feature_role_checks/feature_holdout_summary_with_persistence.csv`
- `results_v2/feature_role_checks/feature_role_checks_summary.md`

Current K5 holdout values used in the paper:

| Holdout | ARI | NMI | Agreement |
|---|---:|---:|---:|
| Activity removed | 0.3702 | 0.4011 | 61.1% |
| Value-flow removed | 0.2391 | 0.3239 | 48.1% |
| Directionality removed | 0.4616 | 0.4916 | 67.1% |
| Volatility/concentration removed | 0.5032 | 0.5205 | 65.3% |
| Temporal-persistence removed | 0.4126 | 0.4288 | 64.4% |

## Stage 5: Monthly Network Validation

Goal: test whether wallets transact with same-role wallets more often than expected under shuffled wallet labels.

Main scripts:

- `scripts/run_k4_k5_k6_network_results_v2.py`
- `scripts/run_monthly_network_null_validation.py`

Final paper output folder:

- `results_v2/network_k4_k5_k6_B999/`

Current final B=999 summary:

| k | Holm significant months | Mean observed - null | Fisher combined p |
|---|---:|---:|---:|
| K4 | 12/12 | 0.1096 | 3.66e-23 |
| K5 | 1/12 | 0.0047 | 1.84e-04 |
| K6 | 11/12 | 0.0403 | 2.09e-21 |

Interpretation:

- K5 has mixed, time-varying same-role network evidence.
- Fisher's combined statistic rejects the global monthly null under its calibration, but only one K5 month remains significant after Holm correction.
- K4 and K6 show stronger network-null support than K5.

## Stage 6: Temporal Validation

Goal: evaluate whether monthly behavioural states persist, change, or return.

Main scripts:

- `scripts/run_temporal_validation_v2.py`
- `scripts/package_temporal_tables_v2.py`

Important outputs:

- `results_v2/temporal_k4_k5_k6/temporal_summary.csv`
- `results_v2/temporal_k4_k5_k6/table_vii_metrics.csv`
- `results_v2/temporal_k4_k5_k6/temporal_validation_v2_summary.md`

Current K5 results:

- Observed self-transition: 50.00%.
- Chance self-transition: 32.32%.
- Cohen's kappa: 0.2613.
- Two-step return: 34.06% observed versus 26.24% weighted conditional null.
- Two-step return remains significant for 10/10 monthly triples after Holm correction.

Caveat:

Monthly states are conditional on the current monthly assignment and scaling procedure. Features that accumulate over time are smaller over one month than over a full year.

## Stage 7: Full EOA Temporal Signal Analysis

Goal: represent each wallet as a daily activity signal and compare time-domain and frequency-domain activity states against annual K5 roles.

Main scripts:

- `src/validation/build_full_eoa_temporal_signal_streaming.py`
- `src/validation/select_full_eoa_temporal_signal_k.py`
- `scripts/add_temporal_signal_followup_analyses.py`

Current paper interpretation:

- Time-domain states capture sparse long-gap activity, sparse uniform-count activity, intermediate recurrent activity, and frequent intermittent-switching activity.
- Frequency-domain states describe spectral power distributions. Low-frequency concentration means activity concentrated in part of the observation year, not a proven recurring annual cycle.
- Signal states are complementary evidence, not fully independent validation, because active-day and persistence features also enter annual clustering.

## Stage 8: Paper Figure Generation

Goal: copy and regenerate paper-ready visual assets.

Main script:

- `scripts/build_paper_visuals.py`

Important output folder:

- `results_v2/paper_visuals/`

Current paper figures copied into `overleaf/figures/`:

- `ethereum_methodology.png`
- `fig_k5_profile_heatmap.pdf`
- `fig2_k5_full_year_observed_expected_mixing.pdf`
- `fig3_k5_same_role_observed_vs_null.pdf`
- `fig4_k5_network_p_values.pdf`
- `fig_k456_self_transition_vs_chance.pdf`
- `fig_k5_transition_matrix.pdf`
- `fig_k5_two_step_return_vs_null.pdf`

## Stage 9: Overleaf Paper Package

The current paper package lives in:

- `overleaf/main.tex`
- `overleaf/figures/`

Upload the contents of `overleaf/` to Overleaf. The `main.tex` file currently uses embedded `thebibliography` references rather than a separate `.bib` file.

Before submission:

1. Compile in Overleaf.
2. Confirm author/anonymity requirements.
3. Confirm the GitHub repository is visible or use an anonymous mirror for double-anonymous review.
4. Confirm the page limit and venue template.
5. Confirm the PDF has no missing figures, `??` references, or broken DOI underscores.

## Deprecated Or Exploratory Branches

Some folders and scripts remain from earlier project directions, including K6-first experiments, WETH/event-window helpers, old report-generation scripts, and sample-based temporal signal experiments. They are retained for traceability, but the current paper should be interpreted through the EOA-only K4/K5/K6 pipeline above.
