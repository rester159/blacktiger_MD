#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
slot,row,level=fixture(r,0,2,0xb67f);s=state(r);xy=(s.actors[slot].x,s.actors[slot].y);s.mode=1;put(r,s)
r.run(150);s=state(r)
assert (s.actors[slot].x,s.actors[slot].y)==xy,'Stationary actor moved'
assert not any(q.active and q.enemy for q in s.shots),'Placeholder turret projectiles remain'
assert s.actors[slot].hp==2
before=s.kills;score=s.score
s=fire(r,slot,1,0);assert s.actors[slot].hp==1 and s.kills==before
s=fire(r,slot,1,0);assert s.kills==before+1 and s.spawned[row]==2
assert s.score==score+json.loads((ROOT/'reference/sentry.json').read_text())['score']
r.run(150);assert not state(r).actors[slot].active
r.close()
report={'passed':True,'source_round':level+1,'source_row':row,'stationary_no_projectiles':True,'damage_score_persistence_retirement':True,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'One real constructor spawn through linked cartridge; controlled damage injections, not a natural playthrough.'}
(ROOT/'reports/sentry-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
