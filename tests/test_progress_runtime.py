#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);s=state(r)
assert (s.p.hp,s.p.armor,s.p.lives,s.coins,r.read('container_keys',1)[0],r.read('progress_max_hp',1)[0])==(1,2,3,200,0,1)
r.run(3,8);r.run(20);checks=[]
for maximum,threshold in enumerate((2000,12000,22000,32000),1):
 slot,row,level=fixture(r,0,4,0xb338);s=state(r);s.score=threshold-300;s.p.hp=1;put(r,s)
 assert r.read('progress_max_hp',1)[0]==maximum
 s=fire(r,slot,255,0)
 assert s.score==threshold and s.p.hp==1 and r.read('progress_max_hp',1)[0]==maximum+1
 # Production respawn heals to the earned maximum without resetting it or money.
 s.mode=4;s.mode_timer=0;s.p.lives=3;s.coins=321;put(r,s);r.run(90);s=state(r)
 assert s.p.hp==maximum+1 and s.coins==321 and s.p.lives==2
 checks.append(dict(threshold=threshold,maximum=maximum+1,award_does_not_heal=True,respawn_uses_maximum=True))
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Source initial resources, real boulder score award crossing four thresholds, no implicit healing and native respawn restoration. NPC/chest/hidden-item healing has separate five-HP integration fixtures.'}
(ROOT/'reports/progress-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
