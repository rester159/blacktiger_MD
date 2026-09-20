#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
slot,row,level=fixture(r,0,0,0x8389,wait_frames=600);s=state(r);y=s.actors[slot].y
assert s.actors[slot].hp==4
for _ in range(250):
 s=state(r);s.mode=1;s.p.y=max(0,y-80*256);s.p.vy=0;s.p.invincible=10000
 for i in range(160):s.spawned[i]=2
 put(r,s);r.write('loot_random',0,b'\0\0');r.run(1)
 if r.read('zombies',16*24)[slot*16+13]:break
else:raise AssertionError('Thrower did not emerge')
s=fire(r,slot,1,0);assert s.actors[slot].hp==3
for _ in range(100):
 s=state(r);s.p.y=max(0,y-80*256);s.p.vy=0;put(r,s);r.write('loot_random',0,b'\0\0');r.run(1)
 if r.read('zombies',16*24)[slot*16+15]:break
else:raise AssertionError('Throw callback never ran')
raw=r.read('missiles',26*12);assert any(raw[i*26+20] for i in range(12)),'Independent projectile missing'
s=state(r);s.mode=2;s.cam_x=max(0,s.actors[slot].x//256-112);s.cam_y=max(0,s.actors[slot].y//256-112);put(r,s);r.run(30);r.capture('thrower-flight.png')
s=state(r);s.mode=1;put(r,s)
# Let the projectile move clear of its parent before testing body damage.
for _ in range(12):
 s=state(r);s.p.y=max(0,y-80*256);s.p.vy=0;put(r,s);r.run(1)
s=state(r);before=s.kills;score=s.score;s=fire(r,slot,100,0)
assert s.kills==before+1 and s.score==score+json.loads((ROOT/'reference/thrower.json').read_text())['score']
raw=r.read('missiles',26*12);assert any(raw[i*26+20] for i in range(12)),'Parent death incorrectly retired projectile'
# A player projectile must destroy the independently surviving thrown object.
index=next(i for i in range(12) if raw[i*26+20]);mx,my=struct.unpack_from('>hh',raw,index*26+16)
s=state(r);q=s.shots[0];q.active=1;q.enemy=0;q.damage=1;q.life=40;q.vx=q.vy=0;q.x=mx*256;q.y=my*256;put(r,s)
for _ in range(12):
 r.run(1)
 if r.read('missiles',26*12)[index*26+21]:break
else:raise AssertionError('Player projectile did not hit thrown object')
for _ in range(180):
 s=state(r);s.p.y=max(0,y-80*256);s.p.vy=0;s.spawned[row]=2;put(r,s);r.run(1)
assert not state(r).actors[slot].active
assert not any(r.read('missiles',26*12)[i*26+20] for i in range(12))
r.close();report={'passed':True,'round':level+1,'source_row':row,'emergence_nonfatal_throw_death':True,'independent_projectile_retirement':True,'player_projectile_destroys_missile':True,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Actual source-row spawn, native nonfatal/fatal projectile hits, throw callback and independent projectile lifetime. Full-route playthrough remains unverified.'}
(ROOT/'reports/thrower-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
