import json
from arcade_source import Source,ROOT
from extract_spitter import ROOTS,extract
from oracle_runner import run_oracle
s=Source();contract=extract(s);(ROOT/'reference/spitter.json').write_text(json.dumps(contract,indent=2)+'\n')
cases=[]
for name,root,px,y,wall,random,hit,shot_hit,ticks in [
 ('emerge_throw_right',0,220,128,0,0,0,0,1300),('emerge_throw_left',0,64,128,0,0,0,0,1300),
 ('walk_right',0,220,128,0,1,0,0,500),('walk_left',0,64,128,0,1,0,0,500),
 ('wall_right',1,220,128,96,1,0,0,220),('fall',5,220,80,0,1,0,0,180),
 ('unthrown_death',1,220,128,0,1,20,0,100),('thrown_death',9,220,128,0,0,100,0,180),
 ('projectile_hit',9,220,128,0,0,0,40,180),('aim_rejected',0,128,128,0,0,0,0,700)]:
 cases.append(dict(name=name,root_index=root,root=ROOTS[root],px=px,py=16,y=y,vy=0,wall=wall,random=random,face=0,ticks=ticks,hit_tick=hit,damage=1,hit2_tick=hit+10 if hit else 0,damage2=16,shot_hit=shot_hit))
for direction in range(32):
 cases.append(dict(name='aim_'+str(direction),root_index=9,root=ROOTS[9],px=220,py=16,y=128,vy=0,wall=0,random=0,face=0,ticks=180,hit_tick=0,damage=1,hit2_tick=0,damage2=16,shot_hit=40,aim=direction))
collision=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(collision.index(0),collision.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items() if isinstance(v,int))+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'spitter-oracle',args);report['cases']=cases;report['scope']='Original-ROM observations for the third recurring walker; native equivalence is checked by tests/test_spitter.py.'
(ROOT/'reference/spitter_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'source ticks')
