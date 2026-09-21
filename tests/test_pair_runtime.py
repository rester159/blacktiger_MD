#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
from test_loot_runtime import drops
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
slot,row,level=fixture(r,0,2,0xacac,approach=32,vertical=32);s=state(r)
parts=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
assert len(parts)==2 and s.spawned[row]==2,parts
assert all(s.actors[i].hp==1 for i in parts)
score=s.score;coins=s.coins;kills=s.kills
s=fire(r,slot,1,0);assert s.actors[slot].active and s.actors[slot].hp==1 and s.score==score,'Initial immunity failed'
for _ in range(200):
 s=state(r);s.mode=1;s.p.x=s.actors[slot].x-32*256;s.p.y=s.actors[slot].y-32*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
 raw=r.read('pairs',14*24)
 if all(raw[i*14+11] for i in parts):break
else:raise AssertionError('Paired flyers never became vulnerable')
s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('paired-flyers.png')
for part in parts:
 s=state(r)
 # Keep both live actors distinct for the targeted shot.
 for other in parts:
  if other!=part and s.actors[other].active:s.actors[other].x=s.actors[part].x+64*256
 put(r,s);s=fire(r,part,1,0)
 assert s.actors[part].state==1
assert s.score==score+20 and s.coins==coins and s.kills==kills+2 and not drops(r)
for _ in range(80):
 r.run(1);s=state(r)
 if all(not s.actors[i].active for i in parts):break
else:raise AssertionError('Paired death animations did not finish')
assert s.spawned[row]==2 and s.mode==1 and not s.boss_dead
r.close();report={'passed':True,'source_round':level+1,'source_row':row,'parts':2,'score_per_part':10,'no_guessed_chest_reward':True,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/pair-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
