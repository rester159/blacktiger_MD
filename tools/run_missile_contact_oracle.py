import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[]
for kind in (0,1):
 w,h=(11,12) if kind==0 else (12,6)
 for parity in (0,1):
  for dx in (-w-1,-w,-w+1,0,w-1,w,w+1):
   for dy in (-h-1,-h,-h+1,0,h-1,h,h+1):cases.append(dict(kind=kind,parity=parity,dx=dx,dy=dy))
lines,report=run_oracle(Source(),'missile-contact-oracle','return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n');report['cases']=cases
(ROOT/'reference/missile_contact_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'observations')
