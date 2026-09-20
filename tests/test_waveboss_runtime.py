#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
cases=[]
for profile,constructor in enumerate((0x98a3,0x98e8)):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
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
 # Aim at the head, above the body that blocks daggers without losing health.
 initial=s.actors[slot].life
 for layer in range(initial):
  for _ in range(1200):
   s=state(r);a=s.actors[slot];s.mode=1;s.p.invincible=10000
   q=s.shots[0];q.active=1;q.enemy=0;q.life=2;q.damage=254;q.kind=1;q.vx=q.vy=0;q.x=a.x+24*256;q.y=a.y-4*256
   put(r,s);r.run(1)
   if state(r).actors[slot].life<initial-layer:break
  else:raise AssertionError(('head hit did not break layer',profile,layer))
 s=state(r);assert s.score==score+(15000 if profile else 5000) and s.spawned[row]&2
 assert s.boss_dead and s.actors[slot].state==2
 for _ in range(800):
  r.run(1);s=state(r)
  if s.mode==5:break
 else:raise AssertionError(('clear callback missing',profile))
 assert not any(a.active for a in s.actors)
 cases.append(dict(profile=profile,round=level+1,row=row,layers=initial,seeds=seeds,waves=waves,reward=s.score-score,round_clear=True))
 r.close()
report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/waveboss-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
