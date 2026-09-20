#!/usr/bin/env python3
"""Actual source hazard spawn, fatal contact and production respawn in cartridge."""
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
slot,row,level=fixture(r,0,1,0xb2a9);s=state(r);a=s.actors[slot];xy=(a.x,a.y)
s.mode=1;s.p.armor=4;s.p.invincible=10000;s.p.hp=4;s.p.lives=3
q=s.shots[0];q.active=1;q.enemy=0;q.life=20;q.damage=200;q.vx=q.vy=0;q.x=a.x+8*256;q.y=a.y+8*256;put(r,s)
r.run(30);s=state(r);assert s.mode==1 and s.actors[slot].active and s.kills==0
assert (s.actors[slot].x,s.actors[slot].y)==xy
# A pickup processed after the hazard must not override/continue a fatal frame.
assert slot+1<24
pickup=s.actors[slot+1];pickup.active=1;pickup.definition=7;pickup.source=159;pickup.x=xy[0];pickup.y=xy[1]
coins=s.coins;time=s.time
s.p.x=xy[0]-8*256;s.p.y=xy[1]-8*256;s.p.vx=s.p.vy=0;put(r,s)
for _ in range(100):
 r.run(1);s=state(r)
 if s.mode==4:break
assert s.mode==4 and s.p.hp==0 and s.p.armor==4 and s.p.lives==3
assert s.actors[slot].active and s.spawned[row]!=2
assert s.coins==coins and s.time==time and s.actors[slot+1].active and not s.actors[slot+1].state
s.mode_timer=0;put(r,s)
for _ in range(100):
 r.run(1);s=state(r)
 if s.mode==1:break
assert s.p.lives==2 and s.p.hp==4 and s.mode==1
r.close();report={'passed':True,'source_round':level+1,'source_row':row,'stationary_weapon_immune':True,'armor_invulnerability_bypassed':True,'single_life_respawn':True,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Actual source spawn with injected projectile/contact; production death/respawn path. Full route and source death animation timing are not covered.'}
(ROOT/'reports/hazard-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
