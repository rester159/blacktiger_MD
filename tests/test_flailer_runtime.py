#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
cases=[]
for variant,constructor in enumerate((0xab33,0xab4a,0xb1c1,0xb1d8)):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
 slot,row,level=fixture(r,0,0,0xb1c1 if variant==3 else constructor,approach=32,vertical=0,wait_frames=300,hold_position=True)
 if variant==3:
  # This constructor's only table row has X=16352, outside the round's 2048-pixel
  # map and source scan window. Exercise its mirrored profile at a controlled slot.
  s=state(r);s.actors[slot].definition=next(d['id'] for d in json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions'] if d['bank']==0 and d['address']==constructor);put(r,s)
  ref=json.loads((ROOT/'reference/flailer.json').read_text())
  r.write('flailers',slot*18,struct.pack('>HHbbBxHBBBBBBBx',0,0,0,0,0,ref['roots'][1][1],8,0,0,1,0,0,255))
 s=state(r);score=s.score;life=24 if variant<2 else 56;assert s.actors[slot].life==life
 for _ in range(600):
  s=state(r);a=s.actors[slot];s.mode=1;s.p.x=a.x+(32 if variant&1 else -32)*256;s.p.y=a.y;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
  raw=r.read('flailers',18*24);weapon=raw[slot*18+16]
  if raw[slot*18+15] and weapon<24 and r.read('flailer_weapons',18*24)[weapon*18+14]:break
 else:raise AssertionError(('flail attack missing',variant))
 s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('flailer-%d.png'%variant)
 s=fire(r,slot,1,0);assert s.actors[slot].life==life-1 and s.score==score
 assert not r.read('flailer_weapons',18*24)[weapon*18+14],'Parent recoil did not cancel linked weapon'
 s=fire(r,slot,200,0);reward=20 if variant<2 else 50
 assert s.score==score+reward and s.actors[slot].state==2 and s.spawned[row]&2 and s.mode==1,(variant,s.score,s.actors[slot].state,s.mode)
 if variant==0:
  s.actors[slot].x=(s.cam_x+600)*256;put(r,s)
 r.run(120);assert not state(r).actors[slot].active
 assert state(r).spawned[row]&2
 cases.append(dict(variant=variant,actual_placement=variant!=3,round=level+1,row=row,health=life,attack=True,recoil_cancels_weapon=True,reward=reward))
 r.close()
# Controlled real contact dispatch for ordinary and poison weapons.
contacts=[];ref=json.loads((ROOT/'reference/flailer.json').read_text())
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
for profile,antidotes,gate in ((0,0,0),(0,1,0),(0,0,30),(1,0,0)):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.armor=4;s.p.hp=4;s.p.invincible=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 r.write('flailer_weapons',0,bytes(18*24));r.write('status_gate',0,bytes([gate]));r.write('shop_antidotes',0,bytes([antidotes]));r.write('shop_poison',0,b'\0')
 effect=struct.pack('>HHbbBxHhhBBBB',0,100,0,0,0,ref['roots'][profile][9],136,904,1,profile,0,0)
 r.write('flailer_weapons',0,effect);s.mode=1;start=s.frame;put(r,s)
 for _ in range(15):
  r.run(1)
  if (state(r).frame-start)&65535>=3:break
 s=state(r);expected=2 if profile==0 and not antidotes and not gate else 1 if profile else 0
 assert s.p.armor==4-expected,(profile,antidotes,gate,s.p.armor)
 assert r.read('shop_poison',1)[0]==(38 if profile==0 and not antidotes and not gate else 0)
 assert r.read('shop_antidotes',1)[0]==0
 contacts.append(dict(profile=profile,antidotes=antidotes,gate=gate,damage=expected))
r.close();report={'passed':True,'cases':cases,'contacts':contacts,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/flailer-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
