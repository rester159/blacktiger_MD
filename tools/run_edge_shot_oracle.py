import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for profile,table in enumerate((0xaeee,0xb0da)):
 for direction in range(17):
  for wall,hit in ((0,0),(1,0),(0,1)):
   cases.append(dict(profile=profile,template=0xaa3c+profile*32,direction=direction,root=s.word(4,table+direction*2)+5,wall=wall,hit=hit))
t=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(t.index(0),t.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'edge-shot-oracle',args);report['cases']=cases
(ROOT/'reference/edge_shot_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
