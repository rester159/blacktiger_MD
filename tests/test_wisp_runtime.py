#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
slot,row,level=fixture(r,0,2,0xa6f8);s=state(r);xy=(s.actors[slot].x,s.actors[slot].y);s.mode=1;put(r,s)
r.write('loot_random',0,b'\0\0')
# Hold a controlled player height while allowing the production actor and renderer to run.
for _ in range(110):
 s=state(r);s.p.x=xy[0]-80*256;s.p.y=xy[1];s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
s=state(r);assert (s.actors[slot].x,s.actors[slot].y)!=xy,'No source motion'
assert not any(q.active and q.enemy for q in s.shots),'Placeholder turret shots remain'
score,kills=s.score,s.kills
for _ in range(2):
 s=fire(r,slot,100,0)
 assert s.actors[slot].active and s.actors[slot].hp==1 and s.spawned[row]==1
 assert (s.score,s.kills)==(score,kills)
r.close();report={'passed':True,'source_round':level+1,'source_row':row,'source_motion_no_turret_shots':True,'hits_restart_without_death_reward':True,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'One real source spawn with controlled player height/RNG and projectile injections. Complete player/contact and retirement fidelity remain unverified.'}
(ROOT/'reports/wisp-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
