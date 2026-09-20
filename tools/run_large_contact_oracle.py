import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for template in (0x9b1f,0x9b4f):
 for ax,ay in ((128,96),(-1,96),(-16,-16),(0,0),(250,200)):
  for kind in (0,1,2):
   for w,h in ((4,4),(6,12)):
    for alternate in ((0,1) if kind==2 else (0,)):
     for dx in (-22,-21,-20,-19,0,19,20,21,22):
      for dy in (-18,-17,-16,-15,-4,8,9,10,23,24,55,56,57):
       cases.append(dict(template=template,ax=ax,ay=ay,kind=kind,w=w,h=h,alternate=alternate,x=ax+24+dx,y=ay+dy))
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'large-contact-oracle',args);report['cases']=cases
(ROOT/'reference/large_contact_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
