# Full EOA Temporal Signal Streaming Pack

This pack applies the same daily-signal feature logic as the 10k temporal signal analysis to the full EOA-only wallet dataset.

## RAM Safety

- The script reads `wallet_daily_2022.csv` in chunks.
- It does not assume the daily file is sorted by wallet.
- It first hash-partitions daily rows by wallet into `512` disk buckets.
- Each wallet is guaranteed to stay in one bucket, so full-year signals are complete inside a bucket.
- It computes wallet-level 365-day transaction, total-flow, and net-flow signals bucket by bucket.
- Clustering uses `StandardScaler.partial_fit` and `MiniBatchKMeans.partial_fit`.

## Outputs

- `full_eoa_time_domain_features_raw.csv`
- `full_eoa_wavelength_features_raw.csv`
- `full_eoa_time_domain_assignments.csv`
- `full_eoa_wavelength_assignments.csv`
- `full_eoa_temporal_signal_assignments.csv`
- `time_domain_cluster_profiles.csv`
- `wavelength_cluster_profiles.csv`
- `time_domain_cluster_interpretive_labels.csv`
- `wavelength_cluster_interpretive_labels.csv`

## Parameters

- k signal clusters: `5`
- kmeans epochs: `3`
- chunk size: `750000`
