from pathlib import Path
import sys,json,hashlib,time
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1]
import os
os.chdir(ROOT)
sys.path.insert(0,str(ROOT/'scripts'))
import run_feature_role_checks_v2 as m
out=Path('results_v2/feature_role_checks/table_v_audit');out.mkdir(exist_ok=True)
m.K_VALUES=[5]
if not m.SCALED_FEATURES.exists():
 m.SCALED_FEATURES=Path('results/eoa_only_kmeans6/wallet_eoa_only_kmeans6_features_robust_scaled.csv').resolve()
print('Loading',m.SCALED_FEATURES,flush=True)
with threadpool_limits(limits=4):
 f=m.load_scaled_features()
 summary,recovery=m.run_feature_holdouts(f)
summary.to_csv(out/'rerun_summary.csv',index=False)
recovery.to_csv(out/'rerun_recovery.csv',index=False)
(out/'run_settings.json').write_text(json.dumps(dict(random_state=492,batch_size=8192,n_init=10,max_iter=200,k=5,features=str(m.SCALED_FEATURES),scenarios=list(m.FEATURE_GROUPS)),indent=2))
print(summary.to_string(index=False),flush=True)
