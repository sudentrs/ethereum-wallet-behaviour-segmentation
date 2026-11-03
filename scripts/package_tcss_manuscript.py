"""Package only the current standalone LaTeX source and referenced vector assets."""
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source=ROOT/'overleaf/main.tex'
    tex=source.read_text(encoding='utf-8')
    assets=re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',tex)
    audit=json.loads((ROOT/'results_v3/year_end_2022_count_cohort/tcss_manuscript_audit.json').read_text())
    assert audit['checks_passed'] and audit['manuscript_sha256']==sha(source)
    kit=OUT/'TCSS_LaTeX_package'
    (kit/'figures').mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,kit/'main.tex')
    for name in assets:shutil.copyfile(ROOT/'overleaf'/name,kit/name)
    readme='''TCSS LaTeX source — corrected year-end cohort

Upload main.tex and the figures/ folder, preserving paths. In Overleaf select
XeLaTeX and set main.tex as the main document. No external .bib file or BibTeX
run is needed: references and all ten tables are embedded in main.tex.

The checked Tectonic 0.17.0 (XeTeX) build has 10 US Letter journal pages,
including references. Another compiler/font installation can change pagination.
Use the supplied PDF to compare the layout.

There are nine figures. Figure 1 (pipeline) is drawn directly in main.tex.
External vector PDFs, in citation order:
'''
    readme+='\n'.join(f'Figure {i+2}: {name}' for i,name in enumerate(assets))
    readme+='''

Scientific scope: 2,508,997 year-end code-free addresses; annual K2–K6;
84 network tests; 20 monthly return tests. Annual roles and monthly states
are separate. See the accompanying TCSS referee audit for remaining limits.
The separate replication supplement contains compact results and analysis code;
raw data, large feature matrices, model arrays and API secrets are excluded.
'''
    (kit/'README.txt').write_text(readme,encoding='utf-8')
    with zipfile.ZipFile(OUT/'TCSS_LaTeX_package.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in [kit/'main.tex',kit/'README.txt',*[kit/a for a in assets]]:
            z.write(p,p.relative_to(kit).as_posix())
    with zipfile.ZipFile(OUT/'TCSS_figures_only.zip','w',zipfile.ZIP_DEFLATED) as z:
        for a in assets:z.write(kit/a,a)
    # Replace the former delivery archive so it cannot accidentally deliver stale source.
    shutil.copyfile(OUT/'TCSS_LaTeX_package.zip',OUT/'overleaf_source.zip')
    base=ROOT/'results_v3/year_end_2022_count_cohort'
    supplemental=[]
    for folder in ['annual','annual/profiles_k3','network_comparison','monthly_k2_k6']:
        supplemental.extend(p for p in (base/folder).iterdir() if p.suffix in {'.csv','.json'} and p.stat().st_size<5_000_000)
    supplemental.extend(base/n for n in ['validation_completion.json','tcss_manuscript_audit.json'])
    supplemental.extend(ROOT/'overleaf'/n for n in ['extended_body.tex','manuscript_inputs.json'])
    scripts=['filter_year_end_count_features','scale_year_end_count_features','fit_year_end_annual_models',
             'summarize_year_end_annual_models','run_year_end_k3_feature_holdouts','run_monthly_count_validation',
             'run_year_end_network_comparison','apply_network_holm_correction','finalize_year_end_validation',
             'generate_year_end_count_figures','build_extended_manuscript','audit_tcss_manuscript','package_tcss_manuscript']
    supplemental.extend(ROOT/'scripts'/f'{n}.py' for n in scripts)
    supplemental.extend((ROOT/'tests').glob('test_*.py'))
    supplemental.extend(ROOT/'docs'/n for n in ['REPRODUCE_CURRENT_VALIDATION.md','VALIDATION_COMPLETION.md','TCSS_REFEREE_AUDIT.md'])
    supplemental.extend([ROOT/'requirements.txt',ROOT/'src/features/build_full_kmeans6_expanded_features.py',
                         ROOT/'src/data_preparation/reformat_tsv_to_wallet_direction_rows.py',
                         ROOT/'src/data_preparation/aggregate_wallet_daily_flows.py'])
    with zipfile.ZipFile(OUT/'TCSS_replication_supplement.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(supplemental)):z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('SUPPLEMENT_README.txt','Compact local replication record. Start with docs/TCSS_REFEREE_AUDIT.md and docs/REPRODUCE_CURRENT_VALIDATION.md. Raw files, cohort CSV, annual source feature table, matrices and labels are required external inputs; this archive is not an independently reconstructed raw-to-annual dataset. No RPC scan needs to be repeated. No secrets or raw transfers are included.\n')
    receipt=json.loads((base/'publication_receipt.json').read_text())
    receipt.update(manuscript_version='TCSS journal-format audited controlled-cohort manuscript',
                   paper_source_sha256=sha(source),pdf_sha256=sha(OUT/'main.pdf'),
                   source_package_sha256=sha(OUT/'TCSS_LaTeX_package.zip'),
                   figure_sha256=audit['figure_sha256'],tcss_audit_sha256=sha(base/'tcss_manuscript_audit.json'),
                   abstract_words=audit['abstract_words'],format='IEEEtran journal, US Letter',
                   replication_supplement_sha256=sha(OUT/'TCSS_replication_supplement.zip'))
    (base/'publication_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    with zipfile.ZipFile(OUT/'TCSS_LaTeX_package.zip') as z:
        assert set(z.namelist())=={'main.tex','README.txt',*assets}
        assert hashlib.sha256(z.read('main.tex')).hexdigest()==sha(source)
        for a in assets:assert hashlib.sha256(z.read(a)).hexdigest()==audit['figure_sha256'][a]
    print('Verified standalone source package, 8 vector figures and compact replication supplement.')


if __name__=='__main__':main()
