import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for x,y in ((128,96),(0,0),(255,255),(-1,96),(256,96),(128,-1),(128,256)):
 for dx in (-17,-16,-15,0,15,16):
  for dy in (-17,-16,-15,0,15,16):
   for face in (0,1):cases.append(dict(x=x,y=y,px=x+dx,py=y+dy,face=face,primary=0,ground=160,full=0))
for ground in (0,128,160,192,208,224,1024):
 for face in (0,1):
  for primary in (0,1,2,3):
   for full in (0,1):cases.append(dict(x=128,y=96,px=128,py=96,face=face,primary=primary,ground=ground,full=full))
t=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(t.index(0),t.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'edge-spawn-oracle',args);report['cases']=cases
(ROOT/'reference/edge_spawn_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
