"""Test empirical candidate-universe equivalence against full merged daily source.

An exact set match establishes a reproducible operational rule, not evidence of
the historical intent of an unavailable upstream producer.
"""
import json
from pathlib import Path
import duckdb
import pandas as pd
from scripts.run_referee_robustness import ROOT,OUT,sha

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'data/processed/wallet_daily_2022.csv'
    candidates=ROOT/'data/processed/wallet_kmeans_clusters.csv'
    df=pd.read_csv(candidates,usecols=['wallet'],dtype=str)
    df.wallet=df.wallet.str.strip().str.lower().str.removeprefix('0x')
    if df.wallet.duplicated().any() or not df.wallet.str.fullmatch('[0-9a-f]{40}').all():raise ValueError('invalid candidates')
    con=duckdb.connect();con.execute('SET threads=4');con.execute("SET memory_limit='1GB'")
    temp=ROOT/'data/interim/candidate_universe_audit';temp.mkdir(parents=True,exist_ok=True)
    con.execute("SET temp_directory='"+(temp/'duckdb_tmp').as_posix()+"'")
    con.register('candidates',df)
    con.execute('''CREATE TEMP TABLE totals AS
       SELECT regexp_replace(lower(trim(wallet)),'^0x','') AS wallet,
              sum(tx_count) AS annual_count,count(*) AS observed_days,
              count(*) FILTER (WHERE NOT isfinite(tx_count) OR tx_count<0 OR tx_count<>floor(tx_count) OR tx_count IS NULL) AS invalid_rows
       FROM read_csv(?,header=true,columns={'wallet':'VARCHAR','date':'VARCHAR','total_in':'VARCHAR','total_out':'VARCHAR','tx_count':'DOUBLE'})
       GROUP BY 1''',[str(source)])
    print('Full daily-source address aggregation complete',flush=True)
    universe=con.execute('SELECT count(*),sum(observed_days),sum(invalid_rows),min(annual_count),max(annual_count) FROM totals').fetchall()[0]
    assert universe[2]==0
    invalid_wallets=con.execute("SELECT count(*) FROM totals WHERE wallet IS NULL OR NOT regexp_full_match(wallet,'[0-9a-f]{40}')").fetchall()[0][0]
    assert invalid_wallets==0
    rows=[]
    for threshold in [1,2,5,10,20]:
        r=con.execute('''SELECT count(*) FILTER (WHERE t.annual_count>=?) AS threshold_addresses,
           count(*) FILTER (WHERE c.wallet IS NOT NULL AND (t.wallet IS NULL OR t.annual_count<?)) AS candidate_only,
           count(*) FILTER (WHERE t.annual_count>=? AND c.wallet IS NULL) AS threshold_only,
           count(*) FILTER (WHERE t.annual_count>=? AND c.wallet IS NOT NULL) AS overlap
           FROM totals t FULL OUTER JOIN candidates c USING(wallet)''',[threshold]*4).fetchall()[0]
        rows.append(dict(threshold=threshold,threshold_addresses=r[0],candidate_only=r[1],threshold_only=r[2],overlap=r[3]))
    pd.DataFrame(rows).to_csv(OUT/'candidate_threshold_comparison.csv',index=False)
    selected=next(r for r in rows if r['threshold']==10)
    exact=selected['candidate_only']==selected['threshold_only']==0
    chosen=con.execute('''SELECT count(*),min(t.annual_count),max(t.annual_count),sum(t.annual_count),sum(t.observed_days)
        FROM candidates c LEFT JOIN totals t USING(wallet)''').fetchall()[0]
    con.close()
    result=dict(complete=True,exact_threshold_10_set_match=exact,candidate_addresses=len(df),daily_unique_addresses=int(universe[0]),
        daily_rows=int(universe[1]),invalid_count_rows=int(universe[2]),candidate_min_count=float(chosen[1]),
        candidate_max_count=float(chosen[2]),candidate_total_incidence=float(chosen[3]),candidate_daily_rows=int(chosen[4]),
        comparisons=rows,source_sha256=sha(source),candidate_source_sha256=sha(candidates),script_sha256=sha(__file__),
        interpretation='Empirical set equivalence against the supplied merged daily source; does not reconstruct raw-transfer cleaning or prove historical producer intent.',
        outputs={'candidate_threshold_comparison.csv':sha(OUT/'candidate_threshold_comparison.csv')})
    (OUT/'candidate_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
