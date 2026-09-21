#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
slot,row,level=fixture(r,0,1,0x92e6,approach=32,vertical=0,wait_frames=400)
s=state(r);score=s.score;assert s.actors[slot].life==18
for _ in range(700):
 s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
 raw=r.read('container_traps',18*24)
 parts=[i for i in range(24) if raw[i*18+14] and raw[i*18+17]>=3]
 if len(parts)==6:break
else:raise AssertionError('Teleporter did not create six attack parts')
s=state(r);s.p.x=(s.cam_x+112)*256;s.p.y=(s.cam_y+112)*256;s.p.vx=s.p.vy=0;put(r,s);r.run(20)
s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('teleporter-wave.png')
# Use an actual middle attack part at a controlled player contact boundary.
part=next(i for i in parts if raw[i*18+17]==4)
for antidotes in (0,1):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 r.write('status_reverse',0,bytes([0]));r.write('status_gate',0,bytes([0]));r.write('shop_antidotes',0,bytes([antidotes]))
 s=state(r);s.p.hp=4;s.p.armor=2;s.p.invincible=0;s.p.vx=s.p.vy=0
 for a in s.actors:a.active=0
 for i in range(160):s.spawned[i]=2
 r.write('container_traps',0,bytes(18*24))
 root=json.loads((ROOT/'reference/container.json').read_text())['wave_roots'][1]
 effect=struct.pack('>HHbbBxHhhBBBB',0,100,0,0,0,root,s.p.x//256+8,s.p.y//256+8,1,0,1,4)
 r.write('container_traps',0,effect);s.mode=1;put(r,s)
 for _ in range(25):
  r.run(1)
  if r.read('status_gate',1)[0]:break
 else:raise AssertionError('Wave status contact did not dispatch')
 s=state(r);assert (s.p.hp,s.p.armor)==(4,2)
 assert r.read('status_reverse',1)[0]==(0 if antidotes else 1)
 assert r.read('shop_antidotes',1)[0]==0
 r.write('container_traps',0,bytes(18*24))
 if not antidotes:
  s.mode=1;s.p.climb=0;s.p.face=0;s.p.invincible=10000;put(r,s);r.run(12,1<<7)
  assert state(r).p.face==1,'Right input did not reverse'
  s=state(r);s.mode=3;s.shop_item=10;s.coins=300;s.previous_input=0;put(r,s);r.run(3);r.run(4,1<<1)
  assert not r.read('status_reverse',1)[0] and state(r).coins==150,'Shop did not cure reversal'
  assert not r.read('shop_poison',1)[0]
# Actual row plus forced screen attack tests permanent defeat and source reward.
slot,row,level=fixture(r,0,1,0x92e6,approach=32,vertical=0,wait_frames=400);s=state(r);score=s.score
meta=json.loads((ROOT/'reports/assets.json').read_text());pickup=next(d['id'] for d in meta['actor_definitions'] if d['bank']==4 and d['address']==0xb515)
a=s.actors[23];a.active=1;a.definition=pickup;a.source=159;a.state=a.hit=0;a.x=s.p.x+8*256;a.y=s.p.y+8*256
s.mode=1;s.p.invincible=10000;put(r,s)
for _ in range(40):
 r.run(1);s=state(r)
 if s.score==score+100:break
else:raise AssertionError('Teleporter POW death failed')
assert s.actors[slot].state==2 and s.spawned[row]&2
# Second profile reuses the body engine but dispatches ordinary damaging flames.
slot,row2,level2=fixture(r,0,1,0x8d33,approach=32,vertical=0,wait_frames=400)
s=state(r);assert s.actors[slot].life==8
for _ in range(700):
 s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
 raw=r.read('container_traps',18*24)
 parts=[i for i in range(24) if raw[i*18+14] and raw[i*18+17]<3]
 if len(parts)==6:break
else:raise AssertionError('Second teleporter did not create six ordinary attack parts')
s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('teleporter-ground.png')
s=state(r);s.p.hp=4;s.p.armor=2;s.p.invincible=0;s.p.vx=s.p.vy=0
for a in s.actors:a.active=0
for i in range(160):s.spawned[i]=2
r.write('status_reverse',0,bytes([0]));r.write('status_gate',0,bytes([0]))
r.write('container_traps',0,bytes(18*24))
root=json.loads((ROOT/'reference/container.json').read_text())['trap_roots'][1]
effect=struct.pack('>HHbbBxHhhBBBB',0,100,0,0,0,root,s.p.x//256+8,s.p.y//256+8,1,0,1,1)
r.write('container_traps',0,effect);s.mode=1;put(r,s)
for _ in range(25):
 r.run(1)
 if state(r).p.armor<2:break
else:raise AssertionError('Ordinary flame did not damage armor')
assert not r.read('status_reverse',1)[0] and not r.read('status_gate',1)[0]
slot,row2,level2=fixture(r,0,1,0x8d33,approach=32,vertical=0,wait_frames=400)
s=state(r);score=s.score
a=s.actors[23];a.active=1;a.definition=pickup;a.source=159;a.state=a.hit=0;a.x=s.p.x+8*256;a.y=s.p.y+8*256
s.mode=1;s.p.invincible=10000;put(r,s)
for _ in range(40):
 r.run(1);s=state(r)
 if s.score==score+100:break
else:raise AssertionError('Second teleporter POW death failed')
assert s.actors[slot].state==2 and s.spawned[row2]&2
r.close();report={'passed':True,'round':level+1,'row':row,'ordinary_profile':{'round':level2+1,'row':row2,'six_part_attack':True,'armor_damage':True,'pow_reward':100},'six_part_attack':True,'status_without_health_damage':True,'horizontal_reversal':True,'automatic_antidote':True,'shop_cure':True,'pow_reward':100,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/teleporter-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
