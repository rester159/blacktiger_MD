import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for left in (0,1):
 for low in (0,1):
  for wall in (0,1):
   for drift in (0,1):
    for hit in (0,8):cases.append(dict(left=left,low=low,wall=wall,drift=drift,hit=hit,ticks=100))
t=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(t.index(0),t.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}'
lines,report=run_oracle(s,'player-dagger-oracle',args);report['cases']=cases
(ROOT/'reference/player_dagger_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
