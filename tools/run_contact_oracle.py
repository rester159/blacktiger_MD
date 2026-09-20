import json
from arcade_source import Source,ROOT
from actor_contract import load
from oracle_runner import run_oracle
source=Source();contracts=load(source)
shapes=sorted({(c['contact']['pool'],c['contact']['half_width'],c['contact']['half_height']) for c in contracts.values() if c['contact'] and c['contact']['pool'] in (32,48)})
cases=[]
for pool,w,h in shapes:
 offset=8 if pool==32 else 0
 for x,y in [(x,y) for x in (-w-4,-w-3,-w-2,0,w+2,w+3,w+4) for y in (-h-9,-h-8,-h-7,0,h+7,h+8,h+9)]:
  cases.append(dict(pool=pool,width=w,height=h,dx=x-offset,dy=y-offset))
lines,report=run_oracle(source,'contact-oracle','return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n')
report['cases']=cases
(ROOT/'reports/contact-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print('observations',len(lines)-1)
