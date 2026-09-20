import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
from extract_boulder import ROOTS
s=Source();cases=[]
for name,px,y,root,hit,damage in [
 ('distant',240,40,0,0,0),('left_edge_inside',64,40,0,0,0),('left_edge_outside',63,40,0,0,0),
 ('right_edge_inside',191,40,0,0,0),('right_edge_outside',192,40,0,0,0),
 ('below_left',96,40,0,0,0),('below_right',176,40,0,0,0),('same_x',128,40,0,0,0),
 ('low_byte_direction',320,40,1,0,0),('grounded',176,128,0,0,0),
 ('nonfatal',176,40,0,20,16),('destroy_before_activation',240,40,0,12,255),
 ('destroy_falling',176,40,0,20,255),('destroy_bouncing',176,40,0,55,255)]:
 cases.append(dict(name=name,template=0xb440,root_index=root,root=ROOTS[root],px=px,py=16,y=y,vy=0,wall=0,random=0,face=0,ticks=200,hit_tick=hit,damage=damage,hit2_tick=0,damage2=0))
c=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(c.index(0),c.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in case.items() if isinstance(v,int))+'}' for case in cases)+'}}\n'
lines,report=run_oracle(s,'boulder-oracle',args);report['cases']=cases
(ROOT/'reference/boulder_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'source ticks')
