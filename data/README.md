# Data Directory

Large raw and intermediate data files are intentionally not included in GitHub.

The original local workspace contains raw monthly Ethereum transaction files and generated wallet-level datasets.

## Expected Data Types

Raw/input data:

- Monthly `.tsv` or `.tsv.gz` Ethereum transaction files.
- Daily wallet activity files.
- Wallet cluster-label CSV files.

Intermediate/generated data:

- Wallet-level feature CSVs.
- Robust-scaled feature CSVs.
- Cluster-label CSVs.
- Monthly wallet-state CSVs.
- Large network intermediate files.

## Why These Files Are Excluded

They are too large for normal GitHub usage and may be regenerated from the original data pipeline.

Use `.gitignore` to keep these out of the repository.

## Local Paths Used In The Original Workspace

The original workspace used paths such as:

- `dataverse_files/`
- `clustering/YYYYMM/`
- `paper_process_outputs/`

If rerunning from this curated repo, either recreate those folders locally or update script arguments/paths.

