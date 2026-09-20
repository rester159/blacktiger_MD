#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
cases=[]
for profile,constructor in enumerate((0x8000,0x991d,0x9b24)):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
 slot,row,level=fixture(r,0,3,constructor,approach=0,vertical=0,wait_frames=300,hold_position=True)
 s=state(r);score=s.score;assert s.actors[slot].life==(3,6,8)[profile];px=s.p.x;py=s.p.y
 seen=set();waves=False
 for _ in range(2400):
  s=state(r);s.mode=1;s.p.x=px;s.p.y=py;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
  raw=r.read('dragon_shots',20*24)
  seen.update(raw[i*20+15] for i in range(24) if raw[i*20+14])
  raw=r.read('container_traps',18*24);waves|=sum(bool(raw[i*18+14]) for i in range(24))>=6
  if 0 in seen and (not profile or (1 in seen and waves)):break
 else:raise AssertionError(('dragon attacks missing',profile,seen,waves))
 s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('dragon-%d.png'%profile)
 # Check native weak-point damage with each weapon, using the live boss shape.
 for kind,damage in ((0,8),(1,4)):
  s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r);a=s.actors[slot];a.hp=80;a.state=0;a.hit=0
  raw=bytearray(r.read('dragons',20*24));at=slot*20;struct.pack_into('>H',raw,at+2,1000);raw[at+4]=raw[at+5]=0;raw[at+10]=24;raw[at+11]=0;r.write('dragons',0,raw)
  r.write('dragon_shots',0,bytes(20*24));weakx=struct.unpack_from('b',raw,at+18)[0];weaky=-24 if profile==2 else 0
  for q in s.shots:q.active=0
  q=s.shots[0];q.active=1;q.enemy=0;q.life=30;q.damage=8;q.kind=kind;q.vx=q.vy=0;q.x=a.x+(56+weakx)*256;q.y=a.y+(24+weaky)*256
  s.mode=1;s.p.invincible=10000;put(r,s)
  for _ in range(30):
   r.run(1)
   if not state(r).shots[0].active:break
  assert state(r).actors[slot].hp==80-damage,(profile,kind,state(r).actors[slot].hp)
 s=state(r);s.mode=2;put(r,s);r.run(20);raw=bytearray(r.read('dragons',20*24));struct.pack_into('>H',raw,slot*20+2,1);r.write('dragons',0,raw)
 initial=s.actors[slot].life
 for layer in range(initial):
  for _ in range(2400):
   s=state(r);a=s.actors[slot];raw=r.read('dragons',20*24);weakx=struct.unpack_from('b',raw,slot*20+18)[0]
   s.mode=1;s.p.invincible=10000
   q=s.shots[0];q.active=1;q.enemy=0;q.life=2;q.damage=254;q.kind=1;q.vx=q.vy=0;q.x=a.x+(56+weakx)*256;q.y=a.y+(0 if profile==2 else 24)*256
   put(r,s);r.run(1)
   if state(r).actors[slot].life<initial-layer:break
  else:raise AssertionError(('dragon layer did not break',profile,layer))
 s=state(r);assert s.score==score+1000 and s.spawned[row]&2 and s.boss_dead and s.actors[slot].state==2
 for _ in range(1000):
  r.run(1);s=state(r)
  if s.mode==5:break
 else:raise AssertionError(('dragon clear missing',profile))
 assert not any(a.active for a in s.actors)
 cases.append(dict(profile=profile,round=level+1,row=row,layers=initial,attack_kinds=sorted(seen),ground_flames=waves,weak_point_weapons=True,reward=1000,round_clear=True));r.close()
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);projectiles=[]
rom=(ROOT/'out/release/rom.bin').read_bytes()
roots=struct.unpack_from('>21H',rom,r.symbols['dragon_shot_roots'])
for kind,mode,full in ((0,8,0),(1,11,0),(2,25,0),(2,27,0),(0,8,1)):
 s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.armor=4;s.p.hp=4;s.p.invincible=0
 raw=bytearray(20*24);slot=16 if kind==2 else 0
 struct.pack_into('>HHbbBxHhh6B',raw,slot*20,0,100,0,0,0,roots[19 if kind==2 else 16 if kind else 0],128 if kind==2 else 136,896 if kind==2 else 904,1,kind,mode,0,1,0)
 if full:
  for i in range(16,24):struct.pack_into('>HHbbBxHhh6B',raw,i*20,0,100,0,0,0,roots[19],0,0,1,2,27,0,0,0)
 r.write('dragon_shots',0,raw);s.mode=1;start=s.frame;put(r,s)
 for _ in range(20):
  r.run(1)
  if (state(r).frame-start)&65535>=3:break
 assert state(r).p.armor==4-int(not(mode&2) and not full),(kind,mode,state(r).p.armor)
 if kind==0:
  raw=r.read('dragon_shots',20*24);assert not raw[14] and any(raw[i*20+14] for i in range(16,24))
 projectiles.append(dict(kind=kind,mode=mode,damage=int(not(mode&2) and not full),full_pool=bool(full),orb_becomes_explosion=kind==0 and not full))
r.close()
report=dict(passed=True,cases=cases,projectile_contacts=projectiles,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual source placements, natural attacks, both weapon types, all health layers and clear callbacks. Full natural player routes and original cutscene timing remain unverified.')
(ROOT/'reports/dragon-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
