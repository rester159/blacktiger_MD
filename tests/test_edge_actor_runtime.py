#!/usr/bin/env python3
import hashlib,json,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
slot,row,level=fixture(r,0,4,0xa4d0,approach=0,vertical=0,hold_position=True)
for _ in range(800):
 s=state(r);a=s.actors[slot];assert a.active,'Caster retired before attack'
 s.mode=1;s.p.x=a.x+32*256;s.p.y=a.y+32*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
 if any(r.read('edge_shots',20*24)[i*20+14] for i in range(24)):break
else:raise AssertionError('No natural aimed attack')
s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('edge-actor.png');score=s.score
for layer in range(2):
 for _ in range(400):
  s=state(r);assert s.actors[slot].active,'Caster retired before layer test'
  if not r.read('edge_actors',18*24)[slot*18+10]&1:break
  s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
 else:raise AssertionError('Caster did not become vulnerable')
 r.write('edge_shots',0,bytes(20*24));hp=state(r).actors[slot].hp;s=fire(r,slot,1,0)
 assert s.actors[slot].hp==hp-1 and s.actors[slot].life==2-layer and s.score==score
 s=fire(r,slot,255,0);assert s.actors[slot].life==1-layer
 if layer==0:assert s.score==score
assert s.score==score+100 and s.spawned[row]&2 and s.actors[slot].state==2 and s.mode==1
r.run(160);assert not state(r).actors[slot].active
r.close()
# Freeze each projectile profile to check live damage dispatch and weapon destruction.
contacts=[];ref=json.loads((ROOT/'reference/edge_actor.json').read_text())
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
for profile in (0,1):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.armor=4;s.p.hp=4;s.p.invincible=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 r.write('edge_shots',0,bytes(20*24));r.write('edge_shots',0,struct.pack('>HHbbBxHhhBBBBBx',0,100,0,0,0,ref['shot_roots'][profile*17],136,904,1,profile,(24,32)[profile],0,0))
 s.mode=1;start=s.frame;put(r,s)
 for _ in range(15):
  r.run(1)
  if (state(r).frame-start)&65535>=3:break
 assert state(r).p.armor==4-(1,3)[profile],(profile,state(r).p.armor)
 s=state(r);s.p.invincible=10000;q=s.shots[0];q.active=1;q.enemy=0;q.kind=0;q.damage=255;q.life=30;q.x=136*256;q.y=904*256;q.vx=q.vy=0;put(r,s)
 r.run(80);assert not r.read('edge_shots',20)[14]
 contacts.append(dict(profile=profile,damage=(1,3)[profile],weapon_destruction=True))
r.close();report=dict(passed=True,round=level+1,row=row,natural_attack=True,layers=2,reward=100,contacts=contacts,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual caster placement, natural aimed attack, both damage layers including recovery after the first defeat state, rewards, retirement and both projectile damage/destruction profiles. Full routes and source global pool contention remain unverified.')
(ROOT/'reports/edge-actor-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
