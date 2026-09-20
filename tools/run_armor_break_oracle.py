import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(profile=p,x=x,y=y) for p in range(4) for x,y in ((120,152),(8,8),(248,240),(-8,-8),(260,260))]
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}'
lines,report=run_oracle(s,'armor-break-oracle',args);report['cases']=cases
(ROOT/'reference/armor_break_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
