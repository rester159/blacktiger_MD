#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
cases=[]
for face in (0,1):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
 s=state(r);s.p.face=face;put(r,s)
 slot,row,level=fixture(r,0,4,0xa4d0,approach=0,vertical=0,hold_position=True,player_face=face)
 s=state(r);a=s.actors[slot];x=a.x//256-s.cam_x;y=a.y//256-s.cam_y
 assert s.spawned[row]==1 and abs(x-(0 if face else 224))<=16,(face,x,y,s.spawned[row])
 assert 80<=y<=192,(face,x,y)
 assert a.face==(1 if face else -1)
 cases.append(dict(player_face=face,round=level+1,row=row,screen_x=x,screen_y=y));r.close()
report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual trigger row spawns from either screen edge on supported ground. Movement, attacks and final persistence behavior still require the actor body port.')
(ROOT/'reports/edge-spawn-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
