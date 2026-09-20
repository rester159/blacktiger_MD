import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[]
for x,y in [(x,96) for x in (-51,-49,-48,-47,-46,-1,0,255,256,302,303,304,305,307)]+[(128,y) for y in (-51,-50,-49,-48,-47,-1,0,255,256,302,303,304,305,307)]+[(-49,-50),(-47,-48),(305,305)]:
 for vx in (-3,0,3):
  for vy in (-2,0,2):cases.append(dict(x=x,y=y,vx=vx,vy=vy))
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(Source(),'projectile-edge-oracle',args);report['cases']=cases
(ROOT/'reference/projectile_edge_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
