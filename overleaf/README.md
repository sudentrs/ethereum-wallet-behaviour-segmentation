# Submission Paper Source

`main.tex` is the current IEEEtran journal manuscript. It is the only source to
use for the submitted paper. `supplementary.tex` is a separate supplementary
document containing extended methods and tables.

## Compile

Upload the contents of this directory to Overleaf, preserving
`figures_current/`, and select **XeLaTeX**. The bibliography is embedded in
`main.tex`; no BibTeX run is required.

Compile the final source once more with the target submission environment and
check the page count before upload. The submission package records SHA-256
hashes for its sources, figures and compiled PDFs.

## Included Assets

- `IEEEtran.cls` - class supplied with the IEEE template package, including its
  2023 title-font adjustments.
- `figures_current/ethereum_wallet_behaviour_methodology.png` - 5088 x 2478 pixel,
  3x export of the original framework layout (about 758 dpi at manuscript size).
- `figures_current/signal_cross_representation.pdf` - main cross-representation figure.
- `references.bib` - historical convenience file only; `main.tex` contains the
  authoritative embedded bibliography.

To rebuild the vector heatmaps from the frozen overlap table,
run `python scripts/render_signal_cross_representation.py` from the repository
root. The original-layout framework PNG and vector heatmap PDF are included in `main.tex`.

## Reproducibility

The current manuscript uses the controlled year-end code-free cohort and the
completed referee-extension analyses. Run `pip install -r
requirements-referee.txt` from the repository root and follow
`docs/REPRODUCE_CURRENT_VALIDATION.md`. Raw transfer data, large feature matrices
and generated caches are intentionally outside Git; their filenames, checksums
and generation steps are documented there.

Do not replace `main.tex` with historical K4/K5/K6 paper files or reuse results
under `results/` and `results_v2/` as evidence for this manuscript.

## TCSS submission

TCSS uses single-anonymous review. Keep the author block and affiliation details.
Selim S. Balcisoy is the corresponding author. The publication preference is
Traditional/Subscription; the actual portal choice must be checked at submission.

The matching source is tagged `tcss-submission-2026-11-22`. After compiling both
sources and reviewing their rendered PDFs, use `scripts/package_tcss_submission.py`
to create the main-source ZIP, separate lists, current replication archive, and
complete submission package in `output/pdf/`. The replication README maps CSVs
and manifests to manuscript and supplementary tables. The embedded bibliography
is authoritative; the historical convenience `.bib` is not needed for compilation.
