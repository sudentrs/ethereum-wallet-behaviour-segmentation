# Submission Record

## Release

The submission source is the Git tag `v1.2.3-submission-repo`.
It contains the final manuscript source, supplementary source, current figures,
compact numerical outputs, scripts, and tests.

## Paper Files

| Artifact | Canonical path |
| --- | --- |
| Main manuscript | `overleaf/main.tex` |
| Supplement | `overleaf/supplementary.tex` |
| Overleaf instructions | `overleaf/README.md` |
| Current figures | `overleaf/figures_current/` |
| Compact paper evidence | `results_v3/year_end_2022_count_cohort/` |

Compile `overleaf/main.tex` with XeLaTeX. The manuscript uses IEEEtran journal
format and includes its bibliography directly, so no BibTeX run is needed.

## Evidence Record

The current paper uses only the corrected year-end code-free cohort. Its compact
result/provenance record is under:

```text
results_v3/year_end_2022_full_cohort/
results_v3/year_end_2022_count_cohort/annual/
results_v3/year_end_2022_count_cohort/network_comparison/
results_v3/year_end_2022_count_cohort/monthly_k2_k6/
results_v3/year_end_2022_count_cohort/signals/
results_v3/year_end_2022_count_cohort/referee_extension/
```

`docs/CURRENT_MANUSCRIPT_STATUS.md` lists the supported claims and boundaries.
`docs/REFEREE_REVISION.md` explains the later robustness controls.

## Reproduction Boundary

The repository intentionally excludes raw monthly TSVs, large feature matrices,
model arrays, and generated caches. Reproducing the complete pipeline requires
those inputs locally. Their filenames, checksums, commands, and expected output
locations are specified in `docs/REPRODUCE_CURRENT_VALIDATION.md`.

Use the pinned environment:

```powershell
python -m pip install -r requirements-referee.txt
python -m unittest discover -s tests -v
```

## Historical Material

`results/`, `results_v2/`, and older process notes remain in the repository for
provenance only. They use earlier cohort definitions and/or pooled-value
representations and must not be cited as evidence for the submitted paper.
See `docs/ARCHIVAL_MATERIAL.md`.
