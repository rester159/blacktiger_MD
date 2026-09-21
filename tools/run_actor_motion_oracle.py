import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
positions=[-513,-512,-465,-464,-257,-256,-209,-208,-49,-48,-47,-33,-32,-17,-16,-1,0,1,239,240,255,256,257,303,304,464,465,511,512]
cases=[]
for axis in range(2):
 for pos in positions:
  for velocity in (-3,0,3):
   for mode in (8,24):
    for persistence in (1,3):
     cases.append(dict(x=pos if axis==0 else 128,y=96 if axis==0 else pos,vx=velocity if axis==0 else 2,vy=1 if axis==0 else velocity,mode=mode,persistence=persistence))
def lua(c):return '{'+','.join(k+'='+str(v) for k,v in c.items())+'}'
lines,report=run_oracle(Source(),'actor-motion-oracle','return {'+','.join(map(lua,cases))+'}')
report['cases']=cases
(ROOT/'reference/actor_motion_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases))
