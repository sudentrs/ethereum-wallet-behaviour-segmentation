# Overleaf Paper Package

This folder contains the current paper source that can be uploaded to Overleaf.

## Files

- `main.tex` - current IEEEtran paper source.
- `review_results.tex` - generated tables and methods/results for the completed review experiments; required by main.tex.
- `figures/` - paper figures referenced by `main.tex`.
- `references.bib` - older BibTeX reference file kept for convenience. The current `main.tex` uses an embedded `thebibliography` section.

## Compile Notes

Upload the entire `overleaf/` folder contents to Overleaf while preserving the `figures/` subfolder.

Regenerate the review tables and figures with
`python scripts/package_review_revision.py` from the repository root.
The paper no longer selects a preferred annual K5 taxonomy. See
`docs/REVIEW_REVISION_STATUS.md` for the remaining methodological requirements.
The built-in single-document compiler cannot resolve this package's external
figures; full compilation and page-level layout verification must be done
in Overleaf or a compiler that supports the complete project.

Before submission, check:

1. All figures render.
2. No `??` references appear.
3. The author block matches the review mode.
4. The GitHub link is public, or replaced with an anonymous mirror for double-anonymous review.
5. The page limit and template rules of the target venue are satisfied.

## Current Caveat

The paper links to the public GitHub repository. If the target venue requires double-anonymous review, remove or anonymize the author block and use an anonymous code mirror instead of the named GitHub account.
