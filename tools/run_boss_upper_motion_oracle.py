import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
from extract_boss_motion import UPPER_ROOTS
s=Source();cases=[]
for variant,template in enumerate((0xa25b,0xa2bb)):
 for name,root,px,y,wall,sample,ticks,hit in [
  ('approach',0,240,106,0,0,160,0),('near_left',0,96,106,0,0,240,0),
  ('near_right',0,176,106,0,0,240,0),('idle',1,176,128,0,8,100,0),
  ('toward_jump',1,176,128,0,0,240,0),('away_jump',1,176,128,0,3,240,0),
  ('high_jump',1,176,128,0,1,240,0),('wall',1,240,128,96,0,160,0),
  ('fall',11,220,80,0,0,120,0),('phase_death',1,220,128,0,0,200,20),
  ('upper2',15,176,84,0,0,240,0),('upper3',16,176,62,0,0,240,0)]:
  cases.append(dict(name=name,variant=variant,template=template,root_index=root,root=UPPER_ROOTS[root],px=px,py=16,y=y,vy=0,wall=wall,random=sample,face=0,ticks=ticks,hit_tick=hit,damage=100,hit2_tick=40 if hit else 0,damage2=100,hit3_tick=60 if hit else 0,hit4_tick=80 if hit else 0))
c=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(c.index(0),c.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in case.items() if isinstance(v,int))+'}' for case in cases)+'}}\n'
lines,report=run_oracle(s,'boss-upper-motion-oracle',args);report['cases']=cases
(ROOT/'reference/boss_upper_motion_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'source ticks')
