# Ethereum Wallet Behaviour Segmentation

This repository contains the curated research code and selected outputs for an Ethereum wallet behaviour segmentation project.

The project studies whether Ethereum wallets can be grouped into interpretable behavioural roles using transaction-derived features, and whether those roles are supported by network structure and temporal behaviour.

## Research Question

Can Ethereum wallets be organized into interpretable behavioural roles that are reproducible across feature sets, aligned with transaction-network structure, and persistent enough over time to support meaningful analysis of wallet behaviour?

## Main Contribution

The project contributes an unsupervised wallet-role discovery workflow:

1. Build wallet-level behavioural features from Ethereum transaction activity.
2. Cluster wallets into six behavioural roles.
3. Interpret the roles using feature profiles.
4. Validate the roles using transaction-network structure.
5. Test whether cross-analysis alignment is stronger than random labels.
6. Analyze monthly role transitions, persistence, and return patterns.
7. Check robustness through feature-set correspondence, subsampling, and subcluster analysis.

## Repository Layout

```text
src/
  data_preparation/ Raw TSV extraction, reformatting, daily aggregation, and legacy event helpers.
  features/        Feature engineering and scaling scripts.
  clustering/      Cluster comparison and distance-based correspondence scripts.
  network/         Transaction-network validation scripts.
  temporal/        Monthly wallet-state transition analysis.
  validation/      Paper-focused validation, stability, and subcluster scripts.
  reporting/       Scripts used to build project reports.

results/
  paper_process/       Compact outputs from paper-focused validation.
  network_validation/  Network evidence and role-interaction summaries.
  temporal_analysis/   Monthly transition and stability outputs.
  subcluster_analysis/ Within-role subcluster outputs.

reports/
  final_report.docx

presentations/
  final_project_presentation.pdf
  final_project_presentation.pptx

docs/
  PROJECT_GUIDE.md
  PIPELINE.md
  OUTPUTS_CATALOG.md
  GITHUB_NOTES.md

data/
  README.md
```

## What Is Not Included

Large raw files, local virtual environments, temporary renders, and full intermediate datasets should not be committed to GitHub.

Use `data/README.md` to document where raw data came from and which local files are required to reproduce the analysis.

## Key Results

- Approximately 2.74 million wallets were processed.
- Six behavioural wallet roles were identified.
- Network validation showed strong role structure.
- Temporal analysis found moderate monthly persistence.
- Cross-feature-set and permutation tests showed non-random correspondence.
- Two-step transition analysis suggested that some role changes are temporary, with many wallets returning to a prior state after one intermediate month.

## How To Read This Repo

Start with:

1. `docs/PROJECT_GUIDE.md`
2. `docs/PIPELINE.md`
3. `docs/SCRIPT_INDEX.md`
4. `docs/MAIN_PIPELINE_AUDIT.md`
5. `docs/FIGURE_TABLE_AUDIT.md`
6. `docs/OUTPUTS_CATALOG.md`

Then inspect the scripts in `src/` according to the pipeline stage you need.
