"""Package current TeX and compact replication artifacts without PDF compilation."""
from pathlib import Path
import json
import zipfile
from scripts.run_referee_robustness import ROOT,BASE,OUT,sha

def main():
    receipt=json.loads((OUT/('current_manuscript_delivery.json' if (OUT/'current_manuscript_delivery.json').exists() else 'revision_completion.json')).read_text())
    audit=json.loads((OUT/'revision_audit.json').read_text())
    assert receipt['complete'] and audit['checks_passed']
    assert sha(ROOT/'overleaf/main.tex')==receipt['manuscript_sha256']==audit['source_checks']['main.tex']['sha256']
    assert sha(ROOT/'overleaf/supplementary.tex')==receipt['supplementary_sha256']==audit['source_checks']['supplementary.tex']['sha256']
    output=ROOT/'output';output.mkdir(exist_ok=True)
    files=['main.tex','supplementary.tex','figures_current/ethereum_wallet_behaviour_methodology.png','figures_current/signal_cross_representation.pdf']
    paper=output/'overleaf_referee_revision.zip'
    with zipfile.ZipFile(paper,'w',zipfile.ZIP_DEFLATED) as z:
        for name in files:z.write(ROOT/'overleaf'/name,name)
        z.writestr('README.md','''# Current referee revision\n\nSelect main.tex as the main document in Overleaf; XeLaTeX is recommended.\nSelect supplementary.tex separately to prepare the standalone supplement.\nPreserve the figures_current directory. Tables and bibliography are embedded.\n\nNo manuscript PDF has been compiled or included. The PDF in figures_current\nis an existing figure asset, not a compiled manuscript. The current delivery receipt records compilation and ten-page verification.\n''')
    frozen=json.loads((ROOT/'overleaf/manuscript_inputs.json').read_text())
    paths=set()
    for directory in ['scripts','src','tests']:
        paths.update((ROOT/directory).rglob('*.py'))
    for suffix in ['*.csv','*.json']:paths.update(BASE.rglob(suffix))
    for directory in ['docs']:
        paths.update((ROOT/directory).glob('*.md'))
    paths.update(ROOT/name for name in ['requirements.txt','requirements-referee.txt','README.md','overleaf/manuscript_inputs.json',
        'data/processed/wallet_kmeans6_expanded_daily_features_build_summary.csv'])
    for name in frozen['input_sha256']:
        p=ROOT/name
        if p.suffix.lower() in {'.csv','.json','.md','.tex'}:paths.add(p)
    compact=output/'referee_replication_compact.zip'
    selected=[p for p in sorted(paths) if p.is_file() and p.stat().st_size<5_000_000]
    with zipfile.ZipFile(compact,'w',zipfile.ZIP_DEFLATED) as z:
        for p in selected:z.write(p,p.relative_to(ROOT).as_posix())
        for name in files:z.write(ROOT/'overleaf'/name,'overleaf/'+name)
        z.writestr('REPLICATION_README.md','''# Compact replication record\n\nStart with docs/REFEREE_REVISION.md. The current paper is overleaf/main.tex\nand the extended methods/tables are overleaf/supplementary.tex. Current\nreceipts and arithmetic/source audits are in\nresults_v3/year_end_2022_count_cohort/referee_extension/.\n\nRaw transfers, merged daily inputs, cohort membership, full feature matrices,\nlabel arrays, model caches and sampled edge arrays are external large artifacts.\nTheir source locations and checksums are documented in the manifests. This\narchive contains source and compact evidence, not a self-contained raw dataset.\nUse Python 3.12 and the recorded requirements-referee.txt versions in an isolated\nenvironment. Historical docs and experiments are clearly subordinate to the\ncurrent referee revision. No PDF compilation was performed.\n''')
    for path in [paper,compact]:
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert z.read('main.tex' if path==paper else 'overleaf/main.tex')==(ROOT/'overleaf/main.tex').read_bytes()
            assert z.read('supplementary.tex' if path==paper else 'overleaf/supplementary.tex')==(ROOT/'overleaf/supplementary.tex').read_bytes()
    result=dict(manuscript_sha256=receipt['manuscript_sha256'],latex_compiled=False,
        archives={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in [paper,compact]})
    (output/'referee_delivery_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
