# Ethereum Wallet Behaviour Segmentation

This repository contains the code, documentation, and selected reproducible outputs for an academic study of Ethereum externally owned account (EOA) behaviour.

The current paper asks whether Ethereum EOAs can be organized into behavioural states that remain meaningful across aggregate wallet features, transaction-network evidence, and temporal activity patterns. The project uses ERC-20 transfer activity from 2022, removes smart-contract addresses, compares K4/K5/K6 k-means taxonomies, and treats K5 as the main descriptive role layer while retaining K4 and K6 as robustness and sensitivity comparisons.

## Research Question

Can Ethereum externally owned accounts be organized into behavioural states that remain meaningful across aggregate features, transaction-network evidence, and temporal activity patterns?

## Current Paper Claim

The paper does not claim that Ethereum contains one natural set of permanent wallet identities. Instead, it presents a layered validation framework:

1. Build EOA-only wallet-level behavioural features from ERC-20 transfers.
2. Compare candidate k-means resolutions K4, K5, and K6.
3. Use K5 as a descriptive behavioural taxonomy because it has the highest seed stability and richer role vocabulary.
4. Retain K4 as the stronger conservative network comparison and K6 as a finer-resolution sensitivity comparison.
5. Validate roles through feature profiles, feature-family holdouts, transaction-network null tests, monthly transitions, two-step return tests, and full-population temporal signal analysis.

## Dataset

The analysis uses the ERC-20 Trading 2022 dataset from Harvard Dataverse:

- Somin, S. ERC-20 Trading 2022. Harvard Dataverse. DOI: 10.7910/DVN/5P82QC
- Somin, S., Altshuler, Y., and Pentland, A. Crypto-asset trading on top of Ethereum Blockchain comprehensive dataset. Scientific Data, 2025.

Raw monthly transfer files are not committed to this repository. See `data/README.md` and `docs/PIPELINE.md` for expected local paths and preparation steps.

## Repository Layout

```text
src/
  data_preparation/   TSV extraction, wallet-direction rows, daily aggregation, EOA filtering helpers.
  features/           Wallet-level feature construction and robust scaling.
  clustering/         EOA-only k-means runs, K sensitivity checks, role descriptions.
  network/            Transaction-network validation and role-interaction analysis.
  temporal/           Monthly state assignment and transition analysis.
  validation/         Feature holdouts, temporal signal analysis, clustering stability checks.
  reporting/          Report and paper-support artifact builders.

scripts/
  run_feature_role_checks_v2.py       K4/K5/K6 feature and holdout checks.
  run_k4_k5_k6_network_results_v2.py  Monthly network null tests for K4/K5/K6.
  run_temporal_validation_v2.py       Self-transition and two-step return validation.
  build_paper_visuals.py              Paper-ready figures copied into results_v2/paper_visuals.
  build_k_evidence_matrix.py          K4/K5/K6 evidence summary.

docs/
  PIPELINE.md                         Reproduction guide and analysis stages.
  SCRIPT_INDEX.md                     Script-purpose index.
  FIGURE_TABLE_AUDIT.md               Figure/table provenance audit when available.

overleaf/
  main.tex                            Current paper source for Overleaf.
  figures/                            Paper figures referenced by main.tex.

results_v2/
  feature_role_checks/                Internal metrics and K5 feature-family holdouts.
  network_k4_k5_k6_B999/              Final monthly network null tests with 999 permutations.
  temporal_k4_k5_k6/                  Monthly temporal validation outputs.
  paper_visuals/                      Paper-ready visual outputs.
```

## Selected Current Results

- EOA filtering retained 2,443,868 externally owned accounts from 2,738,243 initial addresses.
- K5 is used as the main descriptive taxonomy, not as the statistically strongest resolution across every criterion.
- K4 has the strongest conservative same-role network-null evidence.
- K5 has the highest seed stability among the compared annual resolutions and provides a richer descriptive role vocabulary.
- K5 network validation is mixed and time-varying: only 1 of 12 monthly snapshots remains significant after Holm correction, although Fisher's combined statistic rejects the global monthly null under its calibration.
- K5 temporal validation shows 50.00% observed self-transition versus 32.32% chance self-transition, with Cohen's kappa = 0.2613.
- K5 two-step return behaviour is significant across 10/10 monthly triples under the stratified future-state null.
- Full-population temporal signal analysis shows that annual K5 roles carry daily activity signatures, but these are complementary rather than fully independent evidence because some temporal-persistence features also enter annual clustering.

## Reproducing The Paper Outputs

A clean rerun requires the raw ERC-20 Trading 2022 monthly files, local storage for large intermediate tables, and an Ethereum RPC endpoint for contract/EOA filtering if contract labels need to be regenerated.

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

Then follow the stage order in `docs/PIPELINE.md`:

1. Prepare raw monthly ERC-20 transfer files.
2. Build wallet-day and wallet-level features.
3. Filter to externally owned accounts.
4. Run EOA-only K4/K5/K6 clustering.
5. Run feature-role checks and holdouts.
6. Run monthly network validation with B=999 permutations.
7. Run temporal validation and two-step return tests.
8. Run full EOA temporal signal analysis.
9. Build paper-ready figures.
10. Compile the Overleaf paper from `overleaf/main.tex`.

## What Is Not Included

The repository intentionally excludes raw TSV files, large parquet intermediates, large wallet-label CSVs, API keys, and local environment files. These are ignored by `.gitignore` and should be regenerated or downloaded from the cited data source.

## Notes For Reviewers And Collaborators

The repo is organized for traceability rather than as a one-command production package. Some exploratory scripts remain for project history, but the current paper should be read through the EOA-only K4/K5/K6 path documented in `docs/PIPELINE.md` and the selected outputs in `results_v2/`.
