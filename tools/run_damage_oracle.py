import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[dict(hp=h,armor=a,damage=d,invincible=i) for h in (1,4,8) for a in (0,1,2,4) for d in (0,1,2,4,8) for i in (0,1,60)]
lines,report=run_oracle(Source(),'damage-oracle','return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n')
report['cases']=cases
(ROOT/'reports/damage-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print('observations',len(lines)-1)
