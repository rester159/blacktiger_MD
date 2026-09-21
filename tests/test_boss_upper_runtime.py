#!/usr/bin/env python3
"""Independent upper-part defeat must preserve the boss encounter and its row."""
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);cases=[]
for constructor,hp in ((0x9eb1,6),(0x9f16,4)):
 main,row,level=fixture(r,0,4,constructor);slot=main+1
 for _ in range(100):
  s=state(r);s.mode=1;s.p.x=s.actors[slot].x-32*256;s.p.y=max(0,s.actors[slot].y-80*256);s.p.vx=s.p.vy=0;s.p.invincible=10000
  put(r,s);r.run(1)
  if r.read('bosses',18*24)[slot*18+13]:break
 else:raise AssertionError('Upper did not activate')
 # Separate bodies so the injected projectile can only hit the tested upper section.
 s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
 for i,a in enumerate(s.actors):
  if a.active and i!=slot:a.x+=96*256
 score=s.score;kills=s.kills;put(r,s)
 s=fire(r,slot,1,0);assert s.actors[slot].hp==hp-1 and s.actors[slot].life==4
 for layer in (3,2,1):
  s=fire(r,slot,100,0)
  assert s.actors[slot].hp==2 and s.actors[slot].life==layer,(constructor,layer,s.actors[slot].hp,s.actors[slot].life)
  assert s.score==score and s.kills==kills and s.spawned[row]==1
 s=fire(r,slot,100,0)
 assert s.score==score+15 and s.kills==kills+1 and s.actors[slot].state==2
 assert s.spawned[row]==1 and s.boss_dead==0 and s.mode==1
 for _ in range(150):
  r.run(1);s=state(r)
  if not s.actors[slot].active:break
 else:raise AssertionError('Upper did not retire')
 assert s.mode==1 and s.actors[main].active and s.spawned[row]==1 and s.boss_dead==0
 cases.append(dict(constructor=constructor,initial_hp=hp,layers=4,reset_hp=2,reward=15,main_survives=True))
r.close();report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/boss-upper-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
