#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
slot,row,level=fixture(r,0,0,0x8000,wait_frames=500);s=state(r)
assert s.actors[slot].hp==1 and not s.actors[slot].state
# Keep the player above the actor during controlled animation/contact tests.
y=s.actors[slot].y;s.mode=1;put(r,s)
for _ in range(240):
 s=state(r);s.p.y=max(0,y-80*256);s.p.vy=0;s.p.invincible=10000
 for i in range(160):s.spawned[i]=2
 put(r,s);r.run(1)
 if r.read('zombies',16*24)[slot*16+13]:break
else:raise AssertionError('Walker never became vulnerable')
s=state(r);before=s.kills;score=s.score
s=fire(r,slot,1,0)
assert s.kills==before+1 and s.score==score+json.loads((ROOT/'reference/zombie.json').read_text())['score']
for _ in range(100):
 s=state(r);s.p.y=max(0,y-80*256);s.p.vy=0;put(r,s);r.run(1)
 if not state(r).actors[slot].active:break
else:raise AssertionError('Death failed to retire')
assert state(r).spawned[row]==0,'Recurring walker was permanently suppressed'
r.close()
report={'passed':True,'round':level+1,'source_row':row,'spawn_exposure_death_recurrence':True,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Actual constructor row, procedural placement, emergence, lethal projectile, score and recurring retirement. Full route and original scanner cadence remain unverified.'}
(ROOT/'reports/zombie-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
