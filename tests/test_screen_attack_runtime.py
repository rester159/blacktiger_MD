#!/usr/bin/env python3
"""POW pickup must consume damage layers and preserve simultaneous part rewards."""
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,meta
pickup=next(d['id'] for d in meta['actor_definitions'] if d['bank']==4 and d['address']==0xb515)
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);checks=[]
for constructor,parts,reward in ((0x9a4c,1,15),(0x9eb1,2,515),(0x9f16,4,545)):
 slot,row,level=fixture(r,0,4,constructor);s=state(r);score=s.score;kills=s.kills
 assert s.actors[slot].life>1
 q=s.actors[23];q.active=1;q.definition=pickup;q.source=159;q.state=q.hit=0;q.hp=0
 q.x=s.p.x+8*256;q.y=s.p.y+8*256;q.vx=q.vy=0
 s.mode=1;s.p.invincible=10000;s.p.vx=s.p.vy=0;put(r,s)
 for _ in range(60):
  r.run(1);s=state(r)
  if s.kills==kills+parts:break
 else:raise AssertionError(('Screen attack did not defeat all parts',constructor,s.kills,kills,[(a.life,a.hp,a.state) for a in s.actors[:parts]]))
 assert s.score==score+reward,(constructor,s.score-score,reward)
 assert s.spawned[row]==2 and s.spawned[159]==2
 assert s.mode==1,'Death presentation was skipped'
 for part in range(parts):assert s.actors[slot+part].life==0 and s.actors[slot+part].state==2
 assert s.boss_dead==(constructor!=0x9a4c)
 r.run(8);s=state(r);assert s.score==score+reward and s.kills==kills+parts
 checks.append(dict(constructor=constructor,parts=parts,reward=reward,all_layers_collapsed=True))
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Actual ordinary/stacked stone spawn rows and a collected POW pickup. Checks forced layer collapse, simultaneous component rewards, persistence and delayed clear.'}
(ROOT/'reports/screen-attack-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
