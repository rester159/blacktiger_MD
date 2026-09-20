#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);checks=[]
rom=(ROOT/'out/release/rom.bin').read_bytes();data=json.loads((ROOT/'reference/container.json').read_text())
assert rom[r.symbols['container_initial']:r.symbols['container_initial']+64]==bytes(v for row in data['round_contents'] for v in row)
for pc in (0xacbe,0xacd3):
 slot,row,level=fixture(r,0,1,pc);s=state(r);a=s.actors[slot];x,y=a.x,a.y;score=s.score;coins=s.coins;kills=s.kills
 _,_,_,persistent=struct.unpack_from('>4H',rom,r.symbols['spawn'+str(level)]+8*row)
 assert 33<=persistent<41
 assert a.life==r.read('container_contents',8)[persistent-33]-16
 s=fire(r,slot,100,0)
 assert s.actors[slot].active and s.actors[slot].hp==0 and not s.actors[slot].state
 assert (s.score,s.coins,s.kills)==(score,coins,kills)
 r.run(80);s=state(r);assert (s.actors[slot].x,s.actors[slot].y)==(x,y)
 s.mode=2;put(r,s);r.run(15);r.capture('closed-container-%x.png'%pc)
 checks.append(dict(constructor=pc,round=level+1,row=row,content_index=a.life,stationary_and_weapon_immune=True))
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':'Closed containers and shuffled content selection only. Opening/rewards have separate integration checks; key acquisition remains unfinished.'}
(ROOT/'reports/container-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
