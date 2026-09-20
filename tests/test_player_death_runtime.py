#!/usr/bin/env python3
"""Lethal projectile direction and complete source-duration cartridge restart."""
import json,hashlib,struct
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);cases=[]
for left in (0,1):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.mode=1;s.frame=9;s.cam_x=0;s.cam_y=688;s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.hp=1;s.p.armor=0;s.p.invincible=0;s.p.climb=0;s.p.lives=3;s.time=100;s.clock=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(len(s.spawned)):s.spawned[i]=2
 raw=bytearray(26*12);struct.pack_into('>HH',raw,0,3,2)
 struct.pack_into('>IIhh',raw,8,r.symbols['thrower_21'],r.symbols['thrower_21'],144 if left else 128,904)
 raw[20:25]=bytes([1,0,1,8,4]);r.write('missiles',0,raw)
 put(r,s)
 for _ in range(60):
  r.run(1);s=state(r)
  if s.mode==4:break
 assert s.mode==4
 d=r.read('player_death',9);assert d[4]==left and d[7]==1,(left,list(d))
 observed=set();last=329
 for _ in range(1500):
  r.run(1);s=state(r);d=r.read('player_death',9)
  if s.mode!=4:break
  assert s.p.lives==3
  assert 1<=s.mode_timer<=last,(s.mode_timer,last)
  last=s.mode_timer;observed.add(d[5])
  if left==0 and d[5] in (2,12,24):r.capture(f"player-death-{d[5]}.png")
 assert s.mode==1 and s.p.lives==2,(s.mode,s.p.lives)
 assert last==1 and set(range(1,34))<=observed,(last,sorted(observed))
 cases.append(dict(profile=left,frames_observed=len(observed-{0}),single_life_restart=True))
r.close();report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Production lethal projectile path, both ordinary directions, all 33 animation frames and life debit only after the 329th update; source sprite details checked by host oracle.')
(ROOT/'reports/player-death-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
