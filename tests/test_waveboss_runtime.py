#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
cases=[]
for profile,constructor in enumerate((0x98a3,0x98e8)):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
 slot,row,level=fixture(r,0,1,constructor,approach=32,vertical=64,wait_frames=300)
 s=state(r);score=s.score;assert s.actors[slot].life==5+profile
 seeds=False;waves=False
 for _ in range(1800):
  s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
  seeds|=any(r.read('waveboss_seeds',18*8)[i*18+14] for i in range(8))
  raw=r.read('container_traps',18*24)
  waves|=sum(bool(raw[i*18+14]) for i in range(24))>=6
  if seeds and waves:break
 else:raise AssertionError(('boss attack missing',profile,seeds,waves))
 s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('waveboss-%d.png'%profile)
 # Freeze the active body while probing the actual cartridge collision dispatch.
 for kind,dy,damage in ((1,-4,4),(1,24,0),(0,-4,8),(0,24,0)):
  s=state(r);s.mode=2;put(r,s);r.run(20)
  s=state(r);a=s.actors[slot];a.hp=80;a.state=0;a.hit=0;a.vx=a.vy=0
  raw=bytearray(r.read('wavebosses',16*24));at=slot*16
  struct.pack_into('>H',raw,at+2,1000);raw[at+4]=raw[at+5]=0;raw[at+10]=24;raw[at+11]=0
  r.write('wavebosses',0,raw)
  for q in s.shots:q.active=0
  q=s.shots[0];q.active=1;q.enemy=0;q.life=10;q.damage=8;q.kind=kind;q.vx=q.vy=0;q.x=a.x+24*256;q.y=a.y+dy*256
  s.mode=1;s.p.invincible=10000;put(r,s)
  for _ in range(20):
   r.run(1)
   if not state(r).shots[0].active:break
  else:raise AssertionError(('collision did not consume weapon',profile,kind,dy))
  assert state(r).actors[slot].hp==80-damage,(profile,kind,dy,state(r).actors[slot].hp)
 # Restore natural animation timing after the controlled collision probes.
 s=state(r);s.mode=2;put(r,s);r.run(20)
 raw=bytearray(r.read('wavebosses',16*24));struct.pack_into('>H',raw,slot*16+2,1);r.write('wavebosses',0,raw)
 # Aim at the head, above the body that blocks daggers without losing health.
 initial=s.actors[slot].life
 for layer in range(initial):
  for _ in range(1200):
   s=state(r);a=s.actors[slot];s.mode=1;s.p.invincible=10000
   q=s.shots[0];q.active=1;q.enemy=0;q.life=2;q.damage=254;q.kind=1;q.vx=q.vy=0;q.x=a.x+24*256;q.y=a.y-4*256
   put(r,s);r.run(1)
   if state(r).actors[slot].life<initial-layer:break
  else:raise AssertionError(('head hit did not break layer',profile,layer))
 # A video refresh can return between the final life decrement and its
 # reward write in the pipelined game tick. Let that in-flight tick finish.
 r.run(2)
 s=state(r);assert s.score==score+(15000 if profile else 5000) and s.spawned[row]&2
 assert s.boss_dead and s.actors[slot].state==2
 for _ in range(800):
  r.run(1);s=state(r)
  if s.mode==5:break
 else:raise AssertionError(('clear callback missing',profile))
 assert not any(a.active for a in s.actors)
 cases.append(dict(profile=profile,round=level+1,row=row,layers=initial,seeds=seeds,waves=waves,reward=s.score-score,round_clear=True,head_damage_and_body_block=True))
 r.close()
report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/waveboss-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
