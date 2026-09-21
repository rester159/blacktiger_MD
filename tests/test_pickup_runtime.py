#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);checks=[]
for pc in (0xb4af,0xb515):
 slot,row,level=fixture(r,0,4,pc);s=state(r);a=s.actors[slot];assert not a.state
 s.mode=1;s.p.x=a.x-8*256;s.p.y=a.y-8*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;s.clock=0
 s.time=80;s.coins=123;s.score=0
 if pc==0xb515:
  # Two controlled neighbors: an eligible enemy and a protected hidden wall.
  for index,definition in ((slot+1,8),(slot+2,0)):
   q=s.actors[index];q.active=1;q.definition=definition;q.hp=5;q.hit=9;q.state=0;q.source=150+index;q.x=a.x+96*256;q.y=a.y;q.vx=q.vy=0
  kills=s.kills
 start=s.frame;put(r,s)
 if pc==0xb515:
  raw=bytearray(26);struct.pack_into('>H',raw,2,100)
  struct.pack_into('>IIhh',raw,8,r.symbols['thrower_18'],r.symbols['thrower_21'],a.x//256,a.y//256-32)
  raw[20:25]=bytes([1,0,1,8,4]);r.write('missiles',0,raw)
 for _ in range(100):
  r.run(1);s=state(r)
  if ((s.frame-start)&65535)>=3:break
 assert s.spawned[row]==2 and not s.actors[slot].active
 assert s.coins==123
 if pc==0xb4af:assert s.time==110 and s.score==0
 else:
  assert s.time==80 and s.kills==kills+1 and not s.actors[slot+1].active
  assert r.read('missiles',26)[21]==1,'Screen attack missed eligible missile'
  assert s.actors[slot+2].active and s.actors[slot+2].hp==5
 checks.append({'constructor':pc,'round':level+1,'row':row,'reward_persistence_retirement':True})
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Two actual source spawns; time reward and one eligible/protected screen-attack pair with injected contact. Boss composition/death callbacks and full routes remain unverified.'}
(ROOT/'reports/pickup-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
