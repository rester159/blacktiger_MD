import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for side in (0,1):
 for px in (48,112,144,240):
  for random in range(32):
   for damage,full in ((0,0),(255,0),(0,1)):
    cases.append(dict(template=0xaa0c,root=0xaaa7 if side else 0xaa7c,score=0x40,px=px,py=96,y=96,vy=0,random=random,wall=0,damage=damage,full=full,face=side,ticks=480))
t=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(t.index(0),t.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'edge-actor-oracle',args);report['cases']=cases
(ROOT/'reference/edge_actor_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
