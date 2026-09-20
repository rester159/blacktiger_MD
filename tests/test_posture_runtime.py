#!/usr/bin/env python3
"""One real contact update distinguishes standing, crouched and jumping postures."""
import json,hashlib,struct
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);cases=[]
for low,jumping in ((0,0),(1,0),(1,1)):
 for dx,dy in ((0,-3),(6,10),(7,10),(0,21),(0,22),(-6,-1)):
  s=state(r);s.mode=2;put(r,s);r.run(20)
  s=state(r);s.mode=1;s.frame=9;s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.climb=0;s.p.hp=4;s.p.armor=0;s.p.invincible=0;s.previous_input=0;s.time=100;s.clock=0
  for a in s.actors:a.active=0
  for q in s.shots:q.active=0
  for i in range(160):s.spawned[i]=2
  motion=bytearray(struct.pack('>5H20B',0,752,128,144,144,*([0]*20)))
  if jumping:motion[11]=255;motion[12]=192;motion[15]=motion[16]=motion[23]=motion[29]=1
  r.write('player_motion',0,motion);r.write('player_attack',0,bytes(12));r.write('player_daggers',0,bytes(18*9))
  raw=bytearray(26*12);struct.pack_into('>HH',raw,0,3,2)
  struct.pack_into('>IIhh',raw,8,r.symbols['thrower_21'],r.symbols['thrower_21'],136+dx,904+dy)
  raw[20:25]=bytes([1,0,1,8,4]);r.write('missiles',0,raw);put(r,s)
  for _ in range(60):
   r.run(1,32 if low else 0)
   if not r.read('missiles',26)[20]:break
  crouched=low and not jumping
  hit=abs(dx)<=(6 if crouched else 11) and abs(dy-(10 if crouched else 0))<=(11 if crouched else 12)
  s=state(r);assert s.p.hp==(3 if hit else 4),(low,jumping,dx,dy,s.p.hp,hit)
  cases.append(dict(low=low,jumping=jumping,dx=dx,dy=dy,hit=hit))
r.close();report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Real Down input shrinks and lowers projectile contact; an active jump overrides the stored low-posture bit.')
(ROOT/'reports/posture-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
