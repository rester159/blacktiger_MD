import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
shapes=sorted({(c['pool'],c['half_width'],c['half_height']) for d in json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions'] if (c:=d['constructor_evidence']['contact']) and c['pool'] in (32,48)})
for pool,w,h in shapes:
 for x,y in ((128,96),(-1,96),(256,96),(128,-1),(128,256),(2,2)):
  for dx,dy in ((0,0),(w+8,0),(-w-8,0),(w+9,0),(-w-9,0),(0,h+4),(0,-h-4),(0,h+5),(0,-h-5)):
   for parity in (0,1):
    cases.append(dict(pool=pool,w=w,h=h,x=x,y=y,sx=x+(8 if pool==48 else 0)+dx,sy=y+(8 if pool==48 else 0)+dy,damage=16,parity=parity))
for pool in (32,48):
 for damage in (1,2,4,8,16):cases.append(dict(pool=pool,w=8 if pool==32 else 12,h=8 if pool==32 else 12,x=128,y=96,sx=128+(8 if pool==48 else 0),sy=96+(8 if pool==48 else 0),damage=damage,parity=int(pool==48)))
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'chain-actor-oracle',args);report['cases']=cases
(ROOT/'reference/chain_actor_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
