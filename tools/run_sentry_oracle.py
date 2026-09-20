import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[{'x':x,'y':y,'random':r} for x,y in ((32,96),(128,16),(224,96),(128,200)) for r in (32,63)]
lines,report=run_oracle(Source(),'sentry-oracle','return {'+','.join('{x=%d,y=%d,random=%d}'%(c['x'],c['y'],c['random']) for c in cases)+'}\n')
report['cases']=cases
(ROOT/'reports/sentry-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print('observations',len(lines)-1)
