#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);checks=[]
for variant,pc in enumerate((0x8000,0x81a2)):
 slot,row,level=fixture(r,0,2,pc,approach=32,wait_frames=240);s=state(r);hp=(4,16)[variant];assert s.actors[slot].hp==hp
 a=s.actors[slot];xy=(a.x,a.y);s.mode=1;s.p.invincible=10000
 q=s.shots[0];q.active=1;q.enemy=0;q.life=5;q.damage=100;q.vx=q.vy=0;q.x=a.x+16*256;q.y=a.y+16*256;put(r,s)
 r.run(10);s=state(r);assert s.actors[slot].hp==hp and not s.shots[0].active,'Early projectile damaged emerging actor'
 for _ in range(100):
  r.run(1)
  if r.read('emerging',24*12)[slot*12+9]:break
 else:raise AssertionError('Never became vulnerable')
 before=state(r).kills;score=state(r).score
 s=fire(r,slot,1,0);assert s.actors[slot].hp==hp-1 and s.kills==before
 s=fire(r,slot,100,0);assert s.kills==before+1 and s.spawned[row]==2
 assert s.score==score+(50,100)[variant] and (s.actors[slot].x,s.actors[slot].y)==xy
 r.run(150);assert not state(r).actors[slot].active
 slot,row,level=fixture(r,0,2,pc,approach=32,wait_frames=240);s=state(r);s.mode=1;s.p.invincible=10000;put(r,s)
 hidden=False;reappeared=False
 for _ in range(500):
  r.run(1);s=state(r)
  if not s.actors[slot].active:hidden=True
  if hidden and s.actors[slot].active and s.actors[slot].source==row:reappeared=True;break
 assert hidden and reappeared and s.spawned[row]!=2,'Natural hide/respawn cycle failed'
 checks.append({'variant':variant,'round':level+1,'health':hp,'vulnerability_damage_death':True,'hide_respawn':True})
r.close();report={'passed':True,'variants':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Actual source spawns, early projectile immunity, exposed damage/score/death and normal hide/respawn. Original scanner cadence and full playthrough are not verified.'}
(ROOT/'reports/emerge-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
