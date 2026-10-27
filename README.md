# Ethereum Wallet Behaviour Segmentation

This repository contains the code, documentation, and selected reproducible outputs for an academic study of Ethereum externally owned account (EOA) behaviour.

The current paper asks which Ethereum wallet behaviour findings survive changes in segmentation resolution and representation. The project uses ERC-20 transfer activity from 2022 and compares K4/K5/K6 candidate partitions without selecting a preferred taxonomy. The manuscript is under methodological revision; see `docs/REVIEW_REVISION_STATUS.md` for completed tests and unresolved requirements.

## Research Question

Can Ethereum externally owned accounts be organized into behavioural states that remain meaningful across aggregate features, transaction-network evidence, and temporal activity patterns?

## Current Paper Claim

The paper does not claim that Ethereum contains one natural set of permanent wallet identities. Instead, it presents a layered validation framework:

1. Build EOA-only wallet-level behavioural features from ERC-20 transfers.
2. Compare candidate k-means resolutions K4, K5, and K6.
3. Compare seed stability, representation sensitivity, and cross-resolution overlap without declaring an overall winner.
4. Treat the K4-K6 range as exploratory unless the broader K2-K10 diagnostics establish a defensible restriction.
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

- The original present-day code filter retained 2,443,868 addresses from 2,738,243 initial addresses; this is not a verified historical 2022 EOA cohort.
- A historical probability audit found 69/400 excluded addresses code-free at all twelve 2022 month ends (weighted estimate 19.16%, conservative 95% interval 12.74%-27.02%); 67 also have verified 2022 transaction-origination evidence. A separate full-population historical rebuild is pending, not a completed correction. See `docs/HISTORICAL_COHORT_REBUILD.md`.
- No preferred annual resolution is selected.
- K4 has the strongest conservative same-role network-null evidence.
- K5 has the highest seed stability among the compared annual resolutions and provides a richer descriptive role vocabulary.
- Original K5 network validation is mixed: 1 of 12 monthly snapshots remains significant after Holm correction. Independence-calibrated Fisher significance is not used because wallets recur across months.
- Original temporal results use mismatched annual preprocessing/prototypes and monthly observations. They are provisional; the corrected count-only monthly analysis is separate and uses frozen Jan-Jun models for Jul-Dec evaluation.
- A January token-value audit found fixed-10^18 scaling in sampled prepared amounts, requiring token-aware reconstruction before value-based interpretations can be trusted.
- Full-population temporal signal analysis shows that annual K5 roles carry daily activity signatures, but these are complementary rather than fully independent evidence because some temporal-persistence features also enter annual clustering.

## Reproducing The Paper Outputs

The latest review experiments are in `results_v3/`: resolution diagnostics,
corrected monthly states, timing surrogates, token-value provenance,
activity-conditioned network tests, and participation prediction. Their
manifests describe sampling and inferential limits. Earlier `results/` and
`results_v2/` remain for traceability and are not automatically endorsed as
submission-ready evidence.

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
