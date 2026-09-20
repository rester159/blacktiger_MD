import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for template,root in ((0xacbe,0xad1e),(0xacde,0xadb7),(0xacfe,0xadec)):
 for px in (47,48,128,207,208):
  for wall in (0,96):
   for damage in (0,1,2):
    cases.append(dict(template=template,root=root,px=px,py=120,y=40 if template==0xacbe else 144,vy=0,wall=wall,random=0,face=0,ticks=240,hit_tick=160,damage=damage,hit2_tick=200,damage2=damage))
for template,root in ((0xacbe,0xad1e),(0xacde,0xadb7),(0xacfe,0xadec)):
 cases.append(dict(template=template,root=root,px=240,py=120,y=40,vy=0,wall=0,random=0,face=0,ticks=80,hit_tick=0,damage=0,hit2_tick=0,damage2=0,pow_tick=10))
c=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(c.index(0),c.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in case.items())+'}' for case in cases)+'}}\n'
lines,report=run_oracle(s,'crawler-oracle',args);report['cases']=cases;(ROOT/'reference/crawler_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
