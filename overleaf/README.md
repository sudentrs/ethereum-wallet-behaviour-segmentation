# Submission Paper Source

`main.tex` is the current IEEEtran journal manuscript. It is the only source to
use for the submitted paper. `supplementary.tex` is a separate supplementary
document containing extended methods and tables.

## Compile

Upload the contents of this directory to Overleaf, preserving
`figures_current/`, and select **XeLaTeX**. The bibliography is embedded in
`main.tex`; no BibTeX run is required.

The manuscript is intentionally checked for ten Letter pages by the assertion
in `main.tex`. Compile the final source once more with the target submission
environment before upload. The versioned release records the source hash and
Git commit for the submitted delivery.

## Included Assets

- `figures_current/ethereum_wallet_behaviour_methodology.png` - main framework figure.
- `figures_current/signal_cross_representation.pdf` - main cross-representation figure.
- `figures_current/*.pdf` - supporting figures used by the supplementary source.
- `references.bib` - historical convenience file only; `main.tex` contains the
  authoritative embedded bibliography.

## Reproducibility

The current manuscript uses the controlled year-end code-free cohort and the
completed referee-extension analyses. Run `pip install -r
requirements-referee.txt` from the repository root and follow
`docs/REPRODUCE_CURRENT_VALIDATION.md`. Raw transfer data, large feature matrices
and generated caches are intentionally outside Git; their filenames, checksums
and generation steps are documented there.

Do not replace `main.tex` with historical K4/K5/K6 paper files or reuse results
under `results/` and `results_v2/` as evidence for this manuscript.

## Review Mode

The current author block and GitHub link identify the authors. For a venue with
double-anonymous review, use an anonymous copy of the source and code release.
