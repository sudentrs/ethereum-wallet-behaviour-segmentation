# GitHub Notes

## Recommended GitHub Strategy

Use this `github_ready` folder as the repository root.

Do not commit the whole original workspace because it contains:

- Multi-GB raw transaction files.
- Local virtual environments.
- Temporary render folders.
- Intermediate CSV/parquet files.
- Old duplicate reports and presentations.
- Extracted paper text.

## Recommended Commit Contents

Commit:

- `README.md`
- `docs/`
- `src/`
- `results/` selected compact summaries
- `reports/final_report.docx`, if your instructor allows report files in the repo
- `presentations/final_project_presentation.pdf`, if useful
- `.gitignore`
- `requirements.txt`

Do not commit:

- Raw `.tsv`, `.tsv.gz`, `.zip`, `.parquet`, `.dat`, `.pkl`
- `venv/`
- `__pycache__/`
- temporary render directories
- huge generated CSVs unless needed as a small reproducibility sample

## Suggested First Commands

From inside `github_ready`:

```powershell
git init
git add README.md docs src results reports presentations .gitignore requirements.txt
git commit -m "Initial curated project repository"
```

If GitHub rejects large files, remove `.pptx` or `.docx` from the commit and keep only the PDF/report reference.

## Reproducibility Warning

The scripts were developed during research exploration and may still contain local-path assumptions.

Before claiming full reproducibility, check each script's input arguments and replace hard-coded paths with documented command-line arguments where needed.

This curated repo is currently best described as:

> Research code and selected outputs for Ethereum wallet behaviour segmentation.

not:

> Fully automated one-command reproduction package.

