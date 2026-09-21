#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);cases=[]
for constructor,hp in ((0x9eb1,16),(0x9f16,24)):
 slot,row,level=fixture(r,0,4,constructor);s=state(r);a=s.actors[slot];assert a.hp==hp and a.life==2
 parts=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
 assert parts==list(range(2 if constructor==0x9eb1 else 4)),parts
 for part in parts[1:]:
  assert s.actors[part].life==4 and s.actors[part].hp==(6 if constructor==0x9eb1 else 4)
 # Enter the source proximity gate before injecting vulnerable hits.
 x,y=a.x,a.y
 for _ in range(80):
  s=state(r);s.mode=1;s.p.x=x-32*256;s.p.y=max(0,y-80*256);s.p.vx=s.p.vy=0;s.p.invincible=10000
  for i in range(160):s.spawned[i]=2
  put(r,s);r.run(1)
  if r.read('bosses',18*24)[slot*18+13]:break
 else:raise AssertionError('Boss did not activate')
 s=state(r);score=s.score;kills=s.kills;s=fire(r,slot,1,0)
 assert s.actors[slot].hp==hp-1 and s.actors[slot].life==2 and s.actors[slot].hit==0
 s=fire(r,slot,100,0)
 assert s.mode==1 and s.actors[slot].active and s.actors[slot].hp==16 and s.actors[slot].life==1
 assert s.kills==kills and s.score==score,'First layer incorrectly ended boss'
 assert s.actors[slot].hit==0,'Generic hit cooldown leaked into boss phase'
 s.mode=2;s.cam_x=max(0,s.actors[slot].x//256-112);s.cam_y=max(0,s.actors[slot].y//256-112);put(r,s);r.run(30);r.capture('boss-%x-phase.png'%constructor)
 s=state(r);s.mode=1;put(r,s)
 s=fire(r,slot,100,0)
 assert s.mode==1 and s.kills==kills+1 and s.score==score+500
 assert s.actors[slot].active and s.actors[slot].state==2,'Final hit skipped the death sequence'
 assert s.boss_dead==1
 for part in parts[1:]:assert s.actors[part].state==2 and s.actors[part].active,part
 s.p.hp=4;s.p.armor=0;s.p.invincible=0
 q=s.shots[0];q.active=1;q.enemy=1;q.damage=10;q.life=20;q.vx=q.vy=0;q.x=s.p.x+16*256;q.y=s.p.y+16*256;put(r,s)
 r.run(3);s=state(r);assert s.p.hp==4,'Death-sequence contact lock failed'
 start=s.frame
 for _ in range(250):
  r.run(1);s=state(r)
  if s.mode==5:break
 else:raise AssertionError('Death animation did not clear round')
 assert all(not s.actors[part].active for part in parts[1:]),'Upper cleanup did not retire'
 assert s.score==score+500,'Forced cleanup awarded extra score'
 assert ((s.frame-start)&65535)>=95,'Clear occurred before source death animation completed'
 cases.append(dict(constructor=constructor,round=level+1,initial_hp=hp,second_hp=16,reward=500))
r.close();report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Injected hits on both actual boss rows prove the first layer does not clear the round. Source death animation must finish before clear. Two/four-part construction and forced upper cleanup are checked; complete victory presentation remains provisional.'}
(ROOT/'reports/boss-layer-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
