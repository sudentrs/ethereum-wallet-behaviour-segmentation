# Collaborator Data Setup

The Git repository contains code, compact results, manuscript figures, and provenance manifests.
It does **not** contain raw Ethereum data or large generated matrices.
This is intentional: the twelve raw 2022 transfer TSV files total tens of gigabytes and are unsuitable for ordinary GitHub storage.

## Choose the Needed Setup

### Paper and Results Only

For reading or editing the manuscript, no large data are required.

```powershell
git clone https://github.com/sudentrs/ethereum-wallet-behaviour-segmentation.git
cd ethereum-wallet-behaviour-segmentation
```

The current paper is `overleaf/main.tex`.
The compact numerical tables and figures used by the paper are in `results_v3/year_end_2022_count_cohort/`.

### Run the Corrected Monthly Temporal Analysis

Create a local directory named `dataverse_files/` beside the repository and place these twelve files inside it:

```text
wallet_daily_clean_202201.csv
wallet_daily_clean_202202.csv
...
wallet_daily_clean_202212.csv
```

Then run:

```powershell
python scripts/run_monthly_count_validation.py `
  --data-dir ../dataverse_files `
  --cohort results_v3/year_end_2022_full_cohort/cohort_members.csv.gz `
  --out-dir data/interim/year_end_2022_monthly_count_k3 `
  --k-values 3 --permutations 999 --seed 492
```

The daily files are derived from the raw transfer files and are also large.
They should be obtained from the project data holder by external drive, shared cloud storage, or regenerated from the source release.

### Run the Corrected Annual K2--K6 Analysis

In addition to the source code, obtain these local artifacts:

```text
data/processed/wallet_kmeans6_expanded_daily_features.csv
data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv
data/interim/year_end_2022_count_cohort/wallet_count_activity_scaled.npy
```

The first item can be used to reproduce the filtered feature table with `scripts/filter_year_end_count_features.py`.
The latter two are large, derived intermediates and are deliberately ignored by Git.

### Run Transaction-Network Validation

Obtain the raw ERC-20 transfer files from the Harvard Dataverse source or from the project data holder.
The validator accepts either layout:

```text
dataverse_files/202201.tsv/202201.tsv
dataverse_files/202202.tsv/202202.tsv
...
```

or:

```text
dataverse_files/202201.tsv
dataverse_files/202202.tsv
...
```

The corrected K3 network command is:

```powershell
python scripts/run_monthly_network_null_validation.py `
  --labels-npy data/interim/year_end_2022_count_cohort/annual_fits_final2/k3_seed492_labels.npy `
  --wallet-source data/interim/year_end_2022_count_cohort/wallet_count_activity_features.csv `
  --raw-root ../dataverse_files `
  --out-dir results_v3/year_end_2022_count_cohort/network_k3 `
  --permutations 999 --sample-edges 200000
```

## Recommended Data Transfer

Do not add these files to GitHub or remove the matching `.gitignore` rules.
Use an external SSD, university shared storage, Google Drive, OneDrive, or the original Harvard Dataverse download.
The recipient should verify file names and sizes after transfer.

The original raw source is Somin's ERC-20 Trading 2022 Harvard Dataverse release, DOI `10.7910/DVN/5P82QC`.
