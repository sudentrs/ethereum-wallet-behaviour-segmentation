# V2 final table inputs

This package supplements existing v2 results without overwriting them. Do not submit Table III while any internal-metric status is incomplete.

The fixed-label experiments for K4, K5 and K6 are complete. Each uses five independent samples of 20,000 wallets, seeds 42–46, population SD across the five silhouette estimates (ddof=0, matching the guide), and Davies–Bouldin on all 2,443,868 annual wallets. Input SHA256 fingerprints are retained in internal_metrics.csv. Wallet coverage, cluster sizes and all 33 scaled median profiles match the references before scoring.

The supplied original K4/K6 label files have been installed in the expected local results directories (ignored by Git). The previous mismatched K6 labels are preserved under tmp/label_backups/. Old v2 experimental outputs remain unchanged; final_table_inputs contains the corrected fixed-reference metrics and table inputs. The Methodology table now contains all three metric rows.

Reproduce with `python scripts/finalize_paper_code_v2.py --k4-labels PATH --k6-labels PATH`. The feature table can be supplied with `--features PATH`. Rebuild only tables using `--package-only`. Source files are read; new outputs stay here. Completed cached metrics require matching SHA256 input hashes before reuse.

Table V excludes the all-features baseline and contains exactly five holdouts. VII and VIII preserve the legacy monthly assignment limitations and stratified-return test. Table XI is the dominant TD subgroup, with the invalid weighted chunk-median total_tx field excluded. Selection-score components are numerically audited. Signal state profiles use the selected TD K5 and spectral K3 means; these are explicitly labelled means, not medians. Original legacy files retain their names for compatibility.

`paper_replacement_text.md` supplies manuscript text and remaining integration checks. The main manuscript and bibliography are not present; no final PDF or reference/venue verification is claimed. Professor review of claim changes remains pending.
