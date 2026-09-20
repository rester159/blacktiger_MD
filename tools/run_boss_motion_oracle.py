import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
from extract_boss_motion import ROOTS
s=Source();cases=[]
for variant,template in enumerate((0xa22b,0xa28b)):
 for name,root,px,y,wall,random,ticks,hit in [
  ('approach',0,240,128,0,0,160,0),('near_left',0,96,128,0,0,240,0),
  ('near_right',0,176,128,0,0,240,0),('idle',1,176,128,0,12,100,0),
  ('toward_jump',1,176,128,0,4,240,0),('away_jump',1,176,128,0,0,240,0),
  ('high_jump',1,176,128,0,2,240,0),('wall',1,240,128,96,4,160,0),
  ('fall',11,220,80,0,0,120,0),('phase_death',1,220,128,0,4,180,20)]:
  cases.append(dict(name=name,variant=variant,template=template,root_index=root,root=ROOTS[root],px=px,py=16,y=y,vy=0,wall=wall,random=random,face=0,ticks=ticks,hit_tick=hit,damage=100,hit2_tick=hit+20 if hit else 0,damage2=100))
c=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(c.index(0),c.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in case.items() if isinstance(v,int))+'}' for case in cases)+'}}\n'
lines,report=run_oracle(s,'boss-motion-oracle',args);report['cases']=cases
(ROOT/'reference/boss_motion_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'source ticks')
