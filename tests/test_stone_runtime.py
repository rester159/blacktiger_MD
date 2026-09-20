#!/usr/bin/env python3
"""Real ordinary stone row: vulnerability, layered damage, source drop and persistence."""
import hashlib,json
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
from test_loot_runtime import drops
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
slot,row,level=fixture(r,0,4,0x9a4c);s=state(r)
assert s.actors[slot].hp==2 and s.actors[slot].life==4 and s.boss_dead==0
s=fire(r,slot,100,0)
assert s.actors[slot].hp==2 and s.actors[slot].life==4,'Pre-activation immunity failed'
for _ in range(100):
 s=state(r);s.mode=1;s.p.x=s.actors[slot].x-32*256;s.p.y=max(0,s.actors[slot].y-80*256);s.p.vx=s.p.vy=0;s.p.invincible=10000
 put(r,s);r.run(1)
 if r.read('bosses',18*24)[slot*18+13]:break
else:raise AssertionError('Stone did not activate')
s=state(r);score=s.score;kills=s.kills;coins=s.coins
s=fire(r,slot,1,0);assert s.actors[slot].hp==1 and s.actors[slot].life==4 and s.actors[slot].hit==0
for layer in (3,2,1):
 s=fire(r,slot,100,0)
 assert s.actors[slot].hp==2 and s.actors[slot].life==layer
 assert s.score==score and s.kills==kills and s.spawned[row]==1 and not drops(r)
s.mode=2;put(r,s);r.run(20);r.capture('stone-worn.png')
r.write('loot_random',0,b'\0\0')
s=fire(r,slot,100,0)
assert s.score==score+15 and s.kills==kills+1 and s.spawned[row]==2
assert s.mode==1 and s.boss_dead==0 and s.actors[slot].state==2 and s.coins==coins
live=drops(r);assert len(live)==1 and live[0][-1]==2,live
for _ in range(150):
 r.run(1);s=state(r)
 if not s.actors[slot].active:break
else:raise AssertionError('Stone did not retire')
assert s.mode==1 and s.boss_dead==0 and s.spawned[row]==2
r.close();report={'passed':True,'source_round':level+1,'source_row':row,'initial_hp':2,'layers':4,'reset_hp':2,'score':15,'drop_kind':3,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Actual ordinary stone row, controlled hits and RNG. Proximity immunity, layered damage, worn graphics, source drop, retirement and persistence; no full natural playthrough.'}
(ROOT/'reports/stone-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
