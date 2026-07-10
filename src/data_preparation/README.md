# Data Preparation Scripts

These scripts document the raw-data preparation layer that came before the final wallet-role analyses.

They were copied from the original working folders so the GitHub repository includes the full pipeline history instead of starting from already-prepared CSV files.

## Core Raw-Data Path

The intended raw-data flow is:

```text
raw monthly TSV
  -> cleaned parquet chunks
  -> wallet-direction rows
  -> wallet-day in/out/tx_count tables
  -> merged yearly wallet-day table
  -> net-flow table
  -> wallet-level behaviour features
```

Relevant scripts:

- `extract_erc20_tsv_to_parquet.py`
- `reformat_tsv_to_wallet_direction_rows.py`
- `aggregate_wallet_daily_flows.py`
- `merge_monthly_daily_wallet_files.py`
- `add_wallet_daily_netflow.py`
- `build_early_wallet_behavior_features.py`

## Legacy Event Helpers

The `legacy_event_helpers/` scripts came from the earlier event-analysis branch of the project.

They are included because they explain previous outputs and project history, but they are not the central KMeans6 wallet-role pipeline.

## Important Warning

Several scripts still contain hard-coded local paths from the original workspace.

Before rerunning them from a clean clone, update the paths or refactor the scripts to accept command-line arguments.

