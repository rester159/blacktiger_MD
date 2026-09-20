#!/usr/bin/env python3
import hashlib,json,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
cases=[]
for profile,pc in enumerate((0x8344,0x9af6,0x8ef4)):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
 slot,row,level=fixture(r,0,2,pc,approach=0,vertical=0,hold_position=True)
 s=state(r);score=s.score;s.spawned[row]=2;put(r,s)
 for _ in range(800):
  s=state(r);a=s.actors[slot];s.mode=1;s.p.x=a.x+(32 if profile==2 else -32)*256;s.p.y=a.y;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
  if any(r.read('reinforcement_shots',14*24)[i*14+12] for i in range(24)):break
 else:raise AssertionError(('fighter never attacked',profile))
 s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('reinforcement-%d.png'%profile)
 for layer in range((2,4,2)[profile]):
  for _ in range(160):
   if not r.read('fighters',16*24)[slot*16+10]&1:break
   s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
  else:raise AssertionError('fighter stayed immune')
  s=state(r);hp=s.actors[slot].hp;life=s.actors[slot].life
  s=fire(r,slot,1,0);assert s.actors[slot].hp==hp-1 and s.actors[slot].life==life and s.score==score
  s=fire(r,slot,255,0);assert s.actors[slot].life==life-1
  if life>1:assert s.score==score and s.actors[slot].hp==(3,18,12)[profile]
 assert s.score==score+(20,80,30)[profile] and s.actors[slot].state==2 and s.mode==1
 r.run(160);assert not state(r).actors[slot].active
 cases.append(dict(profile=profile,round=level+1,row=row,natural_attack=True,layers=(2,4,2)[profile],reward=(20,80,30)[profile]));r.close()
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);contacts=[]
for part in (0,2,8):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.armor=4;s.p.hp=4;s.p.invincible=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 r.write('reinforcement_shots',0,bytes(14*24));r.write('reinforcement_shots',0,struct.pack('>HHbbBxhhBB',0,100,0,0,0,136,904,1,part))
 s.mode=1;start=s.frame;put(r,s)
 for _ in range(15):
  r.run(1)
  if (state(r).frame-start)&65535>=3:break
 expected=int(part%6==2);assert state(r).p.armor==4-expected
 contacts.append(dict(part=part,damage=expected))
r.close();report=dict(passed=True,cases=cases,contacts=contacts,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual source placements, natural attacks, all health layers, nonfatal and fatal hits, rewards, retirement and both projectile contact directions. Low-posture targeting awaits the native player posture port.')
(ROOT/'reports/reinforcement-body-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
