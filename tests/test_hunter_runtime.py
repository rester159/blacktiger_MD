#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);checks=[]
for boss,constructor,health in ((0,0x9f83,20),(1,0x9fc4,46)):
 slot,row,level=fixture(r,0,1,constructor,approach=32,vertical=0)
 s=state(r);score=s.score;kills=s.kills
 assert s.actors[slot].hp==health and s.actors[slot].life==3
 fired=False
 for _ in range(1200):
  s=state(r);s.mode=1;s.p.invincible=10000;s.p.x=s.actors[slot].x-32*256;s.p.y=s.actors[slot].y;put(r,s);r.run(1)
  raw=r.read('hunter_shells',18*12)
  if any(raw[i*18+14] and raw[i*18+16]==8+boss for i in range(12)):fired=True;break
 assert fired,('Hunter did not fire',boss)
 s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('hunter-boss.png' if boss else 'hunter.png')
 for layer in (2,1,0):
  for attempt in range(40):
   for _ in range(250):
    raw=r.read('hunters',14*24);s=state(r)
    if not (raw[slot*14+10]&1) and not s.actors[slot].state:break
    s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
   else:raise AssertionError(('Hunter stayed immune',boss,layer))
   s=state(r);s.mode=2;put(r,s);r.run(20)
   s=state(r);s.actors[slot].x=(s.cam_x+120)*256;s.actors[slot].y=(s.cam_y+64)*256;put(r,s)
   s=fire(r,slot,255,0)
   for _ in range(15):
    if s.actors[slot].life==layer:break
    r.run(1);s=state(r)
   if s.actors[slot].life==layer:break
  else:raise AssertionError(('Hunter layer did not break',boss,layer))
  assert s.score==score+(500 if not layer else 0)
  if layer:assert s.actors[slot].hp==health
 assert s.kills==kills+1 and s.spawned[row]&2
 if boss:
  assert s.boss_dead and s.mode==1,'Boss death animation skipped'
  for _ in range(300):
   r.run(1);s=state(r)
   if s.mode==5:break
  else:raise AssertionError('Hunter boss did not clear')
  assert not any(a.active for a in s.actors)
  assert not any(r.read('hunter_shells',216)[i*18+14] for i in range(12))
 else:
  for _ in range(160):
   r.run(1);s=state(r)
   if not s.actors[slot].active:break
  assert not s.actors[slot].active and s.mode==1 and not s.boss_dead
 checks.append(dict(boss=bool(boss),round=level+1,row=row,health_per_layer=health,layers=3,score=500,firing=True))
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Actual normal/boss spawn rows, source firing, three damage layers, reward, death animation and boss clear cleanup. Native 180-tick round-clear presentation remains provisional.'}
(ROOT/'reports/hunter-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
