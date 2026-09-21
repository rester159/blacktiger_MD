#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
slot,row,level=fixture(r,0,0,0xb84f,approach=64,vertical=0)
s=state(r);score=s.score;kills=s.kills
assert s.actors[slot].hp==6 and s.actors[slot].life==4
seen=False
for _ in range(250):
 s=state(r);s.mode=1;s.p.invincible=10000;s.p.x=s.actors[slot].x-64*256;s.p.y=s.actors[slot].y;put(r,s);r.run(1)
 raw=r.read('statue_shells',18*12)
 if any(raw[i*18+14] for i in range(12)):seen=True;break
assert seen,'Caster never fired'
s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('stationary-caster.png')
for layer in (3,2,1,0):
 for _ in range(100):
  raw=r.read('statues',14*24)
  if raw[slot*14+12]:break
  s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
 else:raise AssertionError('Caster stayed immune')
 # Isolate body damage from the caster's independently hittable shells.
 r.write("statue_shells",0,bytes(18*12))
 s=fire(r,slot,255,0)
 for _ in range(10):
  if s.actors[slot].life==layer:break
  r.run(1);s=state(r)
 assert s.actors[slot].life==layer,(layer,s.actors[slot].life)
 assert s.score==score+(100 if not layer else 0)
 if layer:assert s.actors[slot].hp==4
assert s.spawned[row]==2 and s.kills==kills+1
# Independent shell survives an absent parent and a weapon hit becomes a medium blast.
s=state(r);s.mode=2
for a in s.actors:a.active=0
for q in s.shots:q.active=0
s.p.invincible=10000;put(r,s);r.run(20)
r.write('statue_shells',0,bytes(18*12));r.write('statue_blasts',0,bytes(18*12))
roots=json.loads((ROOT/'reference/statue.json').read_text())['roots'];s=state(r)
x=s.cam_x+120;y=s.cam_y+80
shell=struct.pack('>HHbbBxHhhBBBB',0,0,0,0,0,roots[13],x,y,1,0,8,0)
r.write('statue_shells',0,shell);s.mode=1;put(r,s)
for _ in range(4):r.run(1)
raw=r.read('statue_shells',18);assert raw[14] and struct.unpack_from('>h',raw,10)[0]>x
s=state(r);s.mode=2;put(r,s);r.run(20)
raw=bytearray(r.read('statue_shells',18));raw[17]=1;r.write('statue_shells',0,raw)
s=state(r);s.mode=1;put(r,s)
for _ in range(4):r.run(1)
assert not r.read('statue_shells',18)[14] and r.read('statue_blasts',18)[14]
# Place the player at the blast's source coordinate; unarmored contact costs one HP.
s=state(r);s.mode=2;put(r,s);r.run(20)
blast=r.read('statue_blasts',18);bx,by=struct.unpack_from('>hh',blast,10)
s=state(r);s.p.x=bx*256;s.p.y=by*256;s.p.vx=s.p.vy=0;s.p.armor=0;s.p.hp=4;s.p.invincible=0;s.mode=1;put(r,s)
for _ in range(30):
 r.run(1)
 if state(r).p.hp<4:break
s=state(r);assert s.p.hp==3 and s.p.invincible,(s.p.hp,s.p.invincible)
# A live shell touching the player creates a separate blast at the player's origin.
s=state(r);s.mode=2;put(r,s);r.run(20)
r.write('statue_shells',0,bytes(18*12));r.write('statue_blasts',0,bytes(18*12))
s=state(r);s.p.hp=4;s.p.invincible=0;s.p.vx=s.p.vy=0
x=s.p.x//256+8;y=s.p.y//256+8
r.write('statue_shells',0,struct.pack('>HHbbBxHhhBBBB',0,0,0,0,0,roots[13],x,y,1,0,8,0))
s.mode=1;put(r,s)
for _ in range(30):
 r.run(1)
 if r.read('statue_blasts',18)[14]:break
else:raise AssertionError('Shell contact did not create a blast')
blast=r.read('statue_blasts',18);bx,by=struct.unpack_from('>hh',blast,10);s=state(r)
assert abs(bx-s.p.x//256)<3 and abs(by-s.p.y//256)<3,(bx,by,s.p.x//256,s.p.y//256)
r.close();report={'passed':True,'source_round':level+1,'source_row':row,'four_layers':True,'final_score':100,'natural_firing':True,'independent_shell_and_blast':True,'blast_damage':1,'shell_contact_burst':True,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/statue-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
