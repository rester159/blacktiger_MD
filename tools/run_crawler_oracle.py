import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
from extract_crawler import PROFILES
for profile,(bank,base,roots,callbacks,score) in enumerate(PROFILES):
 for part in range(3):
  for px in (47,48,128,207,208):
   for wall in (0,96):
    for damage in (0,1,(2,8,16)[profile]):
     cases.append(dict(profile=profile,part=part,bank=bank,template=base+32*part,root=roots[0 if part==0 else 9+part],score=score,px=px,py=120,y=40 if part==0 else 144,vy=0,wall=wall,random=0,face=0,ticks=240,hit_tick=160,damage=damage,hit2_tick=200,damage2=damage))
  cases.append(dict(profile=profile,part=part,bank=bank,template=base+32*part,root=roots[0 if part==0 else 9+part],score=score,px=240,py=120,y=40,vy=0,wall=0,random=0,face=0,ticks=80,hit_tick=0,damage=0,hit2_tick=0,damage2=0,pow_tick=10))
c=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(c.index(0),c.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in case.items())+'}' for case in cases)+'}}\n'
lines,report=run_oracle(s,'crawler-oracle',args);report['cases']=cases;(ROOT/'reference/crawler_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
