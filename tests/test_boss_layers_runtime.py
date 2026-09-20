#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);cases=[]
for constructor,hp in ((0x9eb1,16),(0x9f16,24)):
 slot,row,level=fixture(r,0,4,constructor);s=state(r);a=s.actors[slot];assert a.hp==hp and a.life==2
 score=s.score;kills=s.kills;s=fire(r,slot,1,0)
 assert s.actors[slot].hp==hp-1 and s.actors[slot].life==2 and s.actors[slot].hit==0
 s=fire(r,slot,100,0)
 assert s.mode==1 and s.actors[slot].active and s.actors[slot].hp==16 and s.actors[slot].life==1
 assert s.kills==kills and s.score==score,'First layer incorrectly ended boss'
 assert s.actors[slot].hit==0,'Generic hit cooldown leaked into boss phase'
 s=fire(r,slot,100,0)
 assert s.mode==5 and s.kills==kills+1 and s.score==score+500
 cases.append(dict(constructor=constructor,round=level+1,initial_hp=hp,second_hp=16,reward=500))
r.close();report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Injected hits on both actual boss rows prove the first layer does not clear the round. Boss motion, component rendering and final-clear timing remain provisional.'}
(ROOT/'reports/boss-layer-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
