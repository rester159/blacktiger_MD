import json
from arcade_source import Source,ROOT
from actor_contract import load
from oracle_runner import run_oracle
source=Source();contracts=load(source)
shapes=sorted({(c['contact']['pool'],c['contact']['half_width'],c['contact']['half_height']) for c in contracts.values() if c['contact'] and c['contact']['pool'] in (32,48)})
cases=[]
for pool,w,h in shapes:
 for low in (0,1):
  for jumping in (0,1):
   crouched=low and not jumping
   ox=8 if pool==32 else 0;oy=ox+(10 if crouched else 0)
   cw,ch=(3,3) if crouched else (w,h)
   for x,y in [(x,y) for x in (-cw-4,-cw-3,-cw-2,0,cw+2,cw+3,cw+4) for y in (-ch-9,-ch-8,-ch-7,0,ch+7,ch+8,ch+9)]:
    cases.append(dict(pool=pool,width=w,height=h,dx=x-ox,dy=y-oy,low=low,jumping=jumping))
lines,report=run_oracle(source,'contact-oracle','return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n')
report['cases']=cases
(ROOT/'reports/contact-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print('observations',len(lines)-1)
