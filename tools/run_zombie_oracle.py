import json
from arcade_source import Source,ROOT
from extract_zombie import ROOTS
from oracle_runner import run_oracle
s=Source();cases=[]
for name,root,px,y,wall,hit,ticks in [('emerge_left',0,64,128,0,0,320),('emerge_right',0,220,128,0,0,320),('wall_left',2,64,128,96,0,220),('wall_right',1,220,128,96,0,220),('fall',5,220,80,0,0,100),('death',1,220,128,0,20,100)]:
 cases.append(dict(name=name,root_index=root,root=ROOTS[root],px=px,py=16,y=y,vy=0,wall=wall,face=0,ticks=ticks,hit_tick=hit,damage=1,hit2_tick=0,damage2=0))
collision=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(collision.index(0),collision.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items() if isinstance(v,int))+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'zombie-oracle',args);report['cases']=cases
(ROOT/'reference/zombie_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'ticks')
