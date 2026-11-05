# Ethereum Wallet Segmentation Through Layered Behavioural Validation

This repository is the submission record for a study of Ethereum ERC-20 address
behaviour in 2022. The current tagged submission revision is
[`v1.2.3-submission-repo`](https://github.com/sudentrs/ethereum-wallet-behaviour-segmentation/tree/v1.2.3-submission-repo).

## Research Question

To what extent can unsupervised Ethereum address segments provide an interpretable
and reproducible account of participation across aggregate features,
transaction-network structure, and temporal activity?

The analysis concerns address-level participation, not wallet ownership,
real-world identity, or a permanent natural taxonomy of Ethereum users.

## Paper At A Glance

- **Population:** 2,508,997 addresses with empty code at Ethereum block
  16,308,189, the final block of 2022, from a supplied 2,738,243-address
  activity-selected universe.
- **Annual representation:** sixteen count, activity, persistence, and
  direction features. Pooled token amounts are excluded.
- **Model comparison:** annual K2--K6 models; K3 is an interpretable working
  description, not a universal optimum.
- **Validation:** initialization, training-subset, feature-family, estimator,
  network-null, monthly-state, participation-baseline, and temporal-signal
  checks.
- **Main conclusion:** the segmentation is a bounded descriptive summary.
  Its interpretation changes under representation and graph controls, which is
  reported as evidence rather than hidden as an inconvenience.

## Start Here

| Need | Location |
| --- | --- |
| Final manuscript | [`overleaf/main.tex`](overleaf/main.tex) |
| Supplementary methods and tables | [`overleaf/supplementary.tex`](overleaf/supplementary.tex) |
| Submission and artifact map | [`SUBMISSION.md`](SUBMISSION.md) |
| Reproduction instructions | [`docs/REPRODUCE_CURRENT_VALIDATION.md`](docs/REPRODUCE_CURRENT_VALIDATION.md) |
| Paper claims, caveats, and evidence | [`docs/CURRENT_MANUSCRIPT_STATUS.md`](docs/CURRENT_MANUSCRIPT_STATUS.md) |
| Current compact outputs | [`results_v3/year_end_2022_count_cohort/`](results_v3/year_end_2022_count_cohort/) |
| Historical material policy | [`docs/ARCHIVAL_MATERIAL.md`](docs/ARCHIVAL_MATERIAL.md) |

## Repository Layout

```text
overleaf/       Submission manuscript, supplement, and current figure assets
results_v3/     Compact results and provenance for the corrected-cohort paper
scripts/        Reproduction and validation programs
tests/          Deterministic unit and regression tests
docs/           Current instructions, audit records, and historical index
results/        Historical experiments; not evidence for the submission
results_v2/     Historical experiments; not evidence for the submission
```

Raw source data, large feature matrices, model arrays, and local caches are not
in Git. Their expected names, checksums, and generation commands are in the
reproduction guide. Install the tested environment with:

```powershell
python -m pip install -r requirements-referee.txt
python -m unittest discover -s tests -v
```

## Scope Limits

- The cohort is **year-end code-free**, not verified as an EOA at every 2022
  transfer.
- Counts are wallet-record incidences, not necessarily distinct blockchain
  transactions.
- Network tests cover retained-cohort endpoint interactions and do not establish
  causality, community identity, or economic meaning.
- Monthly states, annual roles, and daily signal partitions are distinct
  descriptions and should not be equated by their numeric labels.

The ERC-20 Trading 2022 data are available from Harvard Dataverse. Formal data
and method citations are embedded in the manuscript.
