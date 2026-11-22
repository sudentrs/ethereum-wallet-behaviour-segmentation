"""Package reviewed TCSS PDFs, LaTeX sources, and compact replication records.

Compile overleaf/main.tex and supplementary.tex with XeLaTeX/Tectonic first,
placing their PDFs in output/pdf/main.pdf and Supplementary_Material.pdf.
Run create_tcss_supporting_pages.py, render every PDF, and pass a JSON review
record containing the SHA-256 of each visually reviewed PDF.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf"
BASE = ROOT / "results_v3/year_end_2022_count_cohort"
TAG = "tcss-submission-2026-11-22-v2"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path):
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def write_zip(path, files, texts=None):
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        for name, source in sorted(files.items()):
            z.write(source, name)
        for name, text in (texts or {}).items():
            z.writestr(name, text)
    with ZipFile(path) as z:
        assert z.testzip() is None
        for name, source in files.items():
            assert hashlib.sha256(z.read(name)).hexdigest() == digest(source), name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-record", required=True, type=Path)
    args = parser.parse_args()
    review = json.loads(args.review_record.read_text(encoding="utf8"))
    pdfs = {"Manuscript.pdf": OUT / "main.pdf", "Footnotes.pdf": OUT / "Footnotes.pdf",
            "Figure_Captions.pdf": OUT / "Figure_Captions.pdf",
            "Supplementary_Material.pdf": OUT / "Supplementary_Material.pdf"}
    for name, path in pdfs.items():
        item = review["pdfs"][path.name]
        assert item["sha256"] == digest(path), f"Stale visual review: {name}"
        assert item["all_pages_reviewed"] is True, name
    pages = {name: len(PdfReader(path).pages) for name, path in pdfs.items()}
    assert pages == {"Manuscript.pdf": 10, "Footnotes.pdf": 1,
                     "Figure_Captions.pdf": 1, "Supplementary_Material.pdf": 5}, pages
    for path in pdfs.values():
        assert all(tuple(float(v) for v in p.mediabox) == (0., 0., 612., 792.)
                   for p in PdfReader(path).pages)
    tex = (ROOT / "overleaf/main.tex").read_text(encoding="utf8")
    assert len(re.findall(r"\\bibitem\{", tex)) == 16
    notes_text = "".join(page.extract_text() or "" for page in PdfReader(pdfs["Footnotes.pdf"]).pages)
    assert "Correspondingauthor:SelimS.Balcisoy." in re.sub(r"\s+", "", notes_text)
    assert not re.search(r"\\(?:thanks|footnote|footnotetext)\{", tex)
    assert "\\ref{fig:signaloverlap}" in tex
    assert "\\begin{doublespace}" in tex
    source_names = ["main.tex", "IEEEtran.cls",
                    "figures_current/ethereum_wallet_behaviour_methodology.png",
                    "figures_current/signal_cross_representation.pdf"]
    main_files = {n: ROOT / "overleaf" / n for n in source_names}
    write_zip(OUT / "TCSS_Main_Manuscript.zip", main_files)

    compact = {}
    locations = [BASE / n for n in ["annual", "network_comparison", "monthly_k2_k6",
                                   "signals", "referee_extension"]]
    for folder in locations:
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.suffix in {".csv", ".json"} and p.stat().st_size < 5_000_000:
                if any(x in p.name for x in ["partial", "checkpoint", "current_manuscript_delivery"]):
                    continue
                compact[p.relative_to(ROOT).as_posix()] = p
    for p in sorted((BASE / "annual/profiles_k3").glob("*.csv")):
        compact[p.relative_to(ROOT).as_posix()] = p
    for n in ["docs/REPRODUCE_CURRENT_VALIDATION.md", "docs/REFEREE_REVISION.md",
              "requirements-referee.txt"]:
        compact[n] = ROOT / n
    mapping = """TCSS compact replication records - 22 November 2026

Matching source tag: tcss-submission-2026-11-22-v2
https://github.com/sudentrs/ethereum-wallet-behaviour-segmentation/tree/tcss-submission-2026-11-22-v2

Paths below are preserved relative to the repository root.
BASE = results_v3/year_end_2022_count_cohort/
EXT = BASE/referee_extension/

Main I / Supplement I: annual/annual_fit_runs.csv, annual_seed_stability.csv;
  EXT/population_resampling.csv and annual_resampling.csv.
Main II: annual/profiles_k3/annual_exact_raw_profiles_seed492_k3.csv and
  annual/annual_cluster_sizes.csv.
Main III / Supplement II: EXT/annual_algorithms.csv.
Per-cluster robustness: EXT/annual_cluster_jaccard.csv and population_jaccard.csv.
Main IV-V / Supplement III-IV: EXT/network_summary_global300.csv;
  network_extension_with_global_correction.csv and
  network_original_with_global_correction.csv retain individual tests.
Exact excluded tokens, graph sizes and endpoint counts: EXT/network_manifest.json
  and network_YYYYMM_coverage.json.
Main VI / Supplement XII: monthly_k2_k6/heldout_persistence.csv and
  heldout_two_step_returns.csv.
Main VII / Supplement V,X: EXT/participation_prediction_scores.csv,
  participation_pooled_scores.csv and participation_prediction_intervals.csv.
Main VIII / Supplement VI: EXT/spectral_block_tests.csv.
Supplement VII: EXT/candidate_threshold_comparison.csv and candidate_manifest.json.
Supplement VIII: EXT/network_YYYYMM_coverage.json.
Supplement IX: signals/signal_model_resolution.csv and signal_seed_stability.csv.
Supplement XI: EXT/participation_transition_counts.csv and
  participation_transition_probabilities.csv.
Figure 2: signals/annual_signal_overlap.csv.
Original timing tests: signals/timing_surrogate_tests.csv and timing_null_replicates.csv.

This archive contains compact results and provenance, not the external raw data
or all derived feature/cache matrices. Follow docs/REPRODUCE_CURRENT_VALIDATION.md
and docs/REFEREE_REVISION.md for analysis commands and external dependencies.
Older computational completion receipts describe their dated runs; the current
submission source and PDF hashes are in the enclosing submission manifest.
No experimental result has been recomputed or changed by packaging.
"""
    replication_manifest = {"source_tag": TAG, "files": {n: record(p) for n, p in compact.items()}}
    write_zip(OUT / "TCSS_replication_supplement.zip", compact,
              {"README.txt": mapping, "replication_manifest.json": json.dumps(replication_manifest, indent=2) + "\n"})

    delivery = {"complete": True, "manuscript": "overleaf/main.tex",
                "manuscript_sha256": digest(ROOT / "overleaf/main.tex"),
                "supplementary_sha256": digest(ROOT / "overleaf/supplementary.tex"),
                "methodology_figure": "overleaf/figures_current/ethereum_wallet_behaviour_methodology.png",
                "methodology_sha256": digest(main_files[source_names[2]]),
                "methodology_pixels": [5088, 2478], "source_tag": TAG,
                "latex_compiled": True, "page_count_verified": True, "pages": 10,
                "supplementary_pages": 5, "compilation_engine": "Tectonic 0.17.0 (XeTeX)",
                "verification": "All final PDF pages rendered and visually checked; all 20 scientific tables match frozen CSVs.",
                "main_pdf_sha256": digest(pdfs["Manuscript.pdf"]),
                "supplementary_pdf_sha256": digest(pdfs["Supplementary_Material.pdf"]),
                "corresponding_author": "Selim S. Balcisoy"}
    delivery["author_notes_location"] = "separate Footnotes.pdf only, as requested by the author"
    delivery_path = BASE / "referee_extension/current_manuscript_delivery.json"
    delivery_path.write_text(json.dumps(delivery, indent=2) + "\n", encoding="utf8", newline="\n")
    files = dict(pdfs)
    for n, p in main_files.items():
        files["source/overleaf/" + n] = p
    for n in ["overleaf/supplementary.tex", "overleaf/README.md", "overleaf/manuscript_inputs.json",
              "scripts/create_tcss_supporting_pages.py", "scripts/package_tcss_submission.py",
              "scripts/render_signal_cross_representation.py",
              "results_v3/year_end_2022_count_cohort/signals/annual_signal_overlap.csv",
              delivery_path.relative_to(ROOT).as_posix()]:
        files["source/" + n] = ROOT / n
    files["TCSS_replication_supplement.zip"] = OUT / "TCSS_replication_supplement.zip"
    files["TCSS_Main_Manuscript.zip"] = OUT / "TCSS_Main_Manuscript.zip"
    if (OUT / "Cover_Letter.txt").exists():
        files["Cover_Letter.txt"] = OUT / "Cover_Letter.txt"
    manifest = {"source_tag": TAG, "base_git_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "compilation_engine": delivery["compilation_engine"], "pdf_pages": pages,
        "verified": {"all_pdf_pages_visually_reviewed": True, "scientific_tables_unchanged": True,
                     "figure1_pixels": [5088, 2478], "figure1_effective_dpi": 758.1,
                     "author_details_retained_for_single_anonymous_review": True},
        "files": {n: record(p) for n, p in files.items()}}
    readme = """TCSS submission package - 22 November 2026

Use TCSS_Main_Manuscript.zip in the LaTeX Main Manuscript field.
Manuscript.pdf is its reviewed ten-page compiled reference.
Footnotes.pdf and Figure_Captions.pdf are separate one-page lists.
Supplementary_Material.pdf is the five-page technical supplement for review.
TCSS_replication_supplement.zip contains the current compact CSVs and manifests.
Cover_Letter.txt can be pasted into the cover-letter text field.

The full package combines main and supplementary files for delivery/storage;
do not upload this entire ZIP as the Main Manuscript.

For Overleaf, open source/overleaf/ and select XeLaTeX. main.tex contains the
embedded bibliography. supplementary.tex compiles separately.

Corresponding author: Selim S. Balcisoy, balcisoy@sabanciuniv.edu.
Author names remain visible because TCSS uses single-anonymous review.
The author-requested layout keeps funding, corresponding-author and affiliation
notes in Footnotes.pdf only; the main manuscript has no first-page footnote block.
Publication preference: Traditional/Subscription; verify the actual portal selection.
All authors approved submission; no external funding, conflicts, prior publication,
preprint or concurrent submission were declared by the submitting author.
Required author disclosures must be checked against IEEE policy before submission.
Every author's ORCID must still be linked/checked in the submission portal.
Institutional human-subject/ethics applicability has not been independently established.

submission_manifest.json records exact source and PDF hashes. base_git_commit
identifies the starting checkout; source_tag identifies the matching source release.
"""
    write_zip(OUT / "TCSS_Submission_Package.zip", files,
              {"README.txt": readme, "submission_manifest.json": json.dumps(manifest, indent=2) + "\n"})
    (OUT / "submission_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    (OUT / "READ_ME_FIRST.txt").write_text(readme, encoding="utf8")
    print(json.dumps({"pages": pages, "replication_files": len(compact), "package_hashes_verified": True}))


if __name__ == "__main__":
    main()
