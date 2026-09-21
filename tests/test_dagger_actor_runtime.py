#!/usr/bin/env python3
import hashlib,json,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,meta
rom=(ROOT/'out/release/rom.bin').read_bytes()
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);checks=[]
for pool,bank,pc,w,h in ((32,2,0xacac,8,8),(48,2,0xb67f,6,6)):
 for parity,dx,dy in ((0,0,0),(1,0,0),(int(pool==48),w+4,0),(int(pool==48),w+5,0),(int(pool==48),0,h+2),(int(pool==48),0,h+3)):
  slot,row,level=fixture(r,0,bank,pc,approach=32,vertical=32)
  s=state(r);s.mode=2;put(r,s);r.run(12);s=state(r)
  for i,a in enumerate(s.actors):
   if i!=slot:a.active=0
  for q in s.shots:q.active=0
  for i in range(160):s.spawned[i]=2
  a=s.actors[slot];a.hp=100;a.hit=a.state=0
  # Keep the single dagger sample out of solid terrain so this isolates actor collision.
  positions=[]
  for yy in range(s.cam_y+48,s.cam_y+128,16):
   for xx in range(s.cam_x+64,s.cam_x+160,16):
    tx=xx+(8 if pool==48 else 0)+dx;ty=yy+(8 if pool==48 else 0)+dy
    cell=(ty//16)*(meta['rounds'][level]['width']//16)+tx//16
    if rom[r.symbols['collision'+str(level)]+cell]!=3:positions.append((xx,yy))
  assert positions
  a.x,a.y=(v*256 for v in positions[0])
  if pool==32:
   raw=bytearray(14);struct.pack_into('>HH',raw,0,0,100);raw[11]=1;r.write('pairs',slot*14,raw)
  s.mode=1;s.frame=9+parity;s.p.invincible=10000;s.p.vx=s.p.vy=0;s.clock=0
  q=s.shots[0];q.active=1;q.enemy=0;q.kind=1;q.damage=16;q.life=2;q.vx=q.vy=0
  q.x=a.x+((8 if pool==48 else 0)+dx)*256;q.y=a.y+((8 if pool==48 else 0)+dy)*256
  put(r,s)
  for _ in range(20):
   r.run(1);s=state(r)
   if not s.shots[0].active:break
  hit=parity==int(pool==48) and abs(dx)<=w+4 and abs(dy)<=h+2
  assert s.actors[slot].hp==(92 if hit else 100),(pool,parity,dx,dy,s.actors[slot].hp)
  checks.append(dict(pool=pool,parity=parity,dx=dx,dy=dy,hit=hit,damage=8 if hit else 0))
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'One-contact-tick daggers against stationary controlled small/medium native actors: parity, inclusive edges and half strength.'}
(ROOT/'reports/dagger-actor-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
