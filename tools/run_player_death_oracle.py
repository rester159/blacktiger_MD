import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(profile=p,x=x,y=y) for p in range(4) for x,y in ((112,144),(0,0),(255,255),(8,16),(248,240))]
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}'
lines,report=run_oracle(s,'player-death-oracle',args);report['cases']=cases
(ROOT/'reference/player_death_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
