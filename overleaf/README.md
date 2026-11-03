# Overleaf Paper Package

This folder contains the current paper source that can be uploaded to Overleaf.
The current source uses `IEEEtran` journal format for TCSS on US Letter, not the
older conference format. Select **XeLaTeX** in Overleaf. The bibliography is
embedded; no BibTeX run or external `.bib` file is required.

The current editable source is `main.tex` with assets under `figures_current/`.
Existing ZIP/PDF files under `output/pdf/` predate the signal integration and
should not be treated as current exports. The selected methodology PNG is included
in the source, with its original K5 label distinguished from the current K3 summary.
See `docs/TCSS_REFEREE_AUDIT.md` for the scientific audit and remaining limits.

## Files

- `main.tex` - current IEEEtran paper source.
- `extended_body.tex` - historical narrative template; do not use it to overwrite the signal-integrated `main.tex`.
- `manuscript_inputs.json` - frozen result-table hashes used by the extended manuscript builder.
- `review_results.tex` - historical review material; not included by the current main.tex.
- `figures_current/` - current manuscript assets, including the methodology image and rebuilt signal figures.
- `figures/` - older assets retained for provenance.
- `references.bib` - older BibTeX reference file kept for convenience. The current `main.tex` uses an embedded `thebibliography` section.

## Compile Notes

Upload the entire `overleaf/` folder contents to Overleaf while preserving the `figures_current/` subfolder.

Current tables and figures come from the controlled year-end cohort pipeline,
not the old review pack. See `docs/REPRODUCE_CURRENT_VALIDATION.md` and
`docs/VALIDATION_COMPLETION.md`. Annual and monthly K2--K6 comparisons are
included, with K3 as the main descriptive illustration.
The paper uses IEEEtran journal/Letter format. The ten-page target has not been
reverified for the signal-integrated revision because compilation was explicitly
not requested. `main.tex` is the source of truth; the old extended-body builder
is blocked after signal publication to avoid losing the new analysis.
See `docs/YEAR_END_SIGNAL_VALIDATION.md` for reproducible signal commands and
`overleaf/manuscript_inputs.json` for frozen compact result hashes.
Compile the complete project with figures available. The built-in Codex project
compiler supports this directory; a standalone Tectonic compiler can also run:

```powershell
tectonic --keep-logs --outdir ../output/pdf main.tex
```

Before submission, check:

1. All figures render.
2. No `??` references appear.
3. The author block matches the review mode.
4. The GitHub link is public, or replaced with an anonymous mirror for double-anonymous review.
5. The page limit and template rules of the target venue are satisfied.

## Current Caveat

The paper links to the public GitHub repository. If the target venue requires double-anonymous review, remove or anonymize the author block and use an anonymous code mirror instead of the named GitHub account.
