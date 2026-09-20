#!/usr/bin/env python3
import json,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
def crawler_fire(r,slot,damage):
 s=state(r);s.mode=1;s.p.invincible=10000;a=s.actors[slot]
 q=s.shots[0];q.active=1;q.enemy=0;q.kind=1;q.damage=min(255,damage*2);q.life=30;q.vx=q.vy=0;q.x=a.x;q.y=a.y
 put(r,s)
 for _ in range(80):
  r.run(1);s=state(r)
  if not s.shots[0].active:return s
 raise AssertionError('Crawler dagger was not handled')
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
slot,row,level=fixture(r,0,3,0xaab3,approach=32,vertical=0)
s=state(r);score=s.score
s=fire(r,slot,255,0);assert s.actors[slot].active and not s.actors[slot].state and s.score==score,'Dormant seed was not immune'
parts=[]
for _ in range(700):
 s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1);s=state(r)
 parts=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
 if len(parts)==3:break
else:raise AssertionError(('Seed did not split',[(a.x//256,a.y//256,a.active) for a in s.actors if a.source==row]))
assert s.spawned[row]&2 and all(s.actors[i].life==2 for i in parts)
r.run(30);s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('crawler-split.png')
# The source's custom damage branch retires a weakly hit crawler without a score;
# a hit meeting its internal durability awards ten points.
for part,damage,reward in zip(parts,(1,2,255),(0,10,10)):
 for _ in range(160):
  raw=r.read('crawlers',14*24)
  if not (raw[part*14+12]&1):break
  s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
 else:raise AssertionError('Crawler never became vulnerable')
 s=state(r);s.mode=2;s.actors[part].x=(s.cam_x+120)*256
 for other in parts:
  if other!=part and s.actors[other].active:s.actors[other].x=s.actors[part].x+64*256
 put(r,s);r.run(20)
 before=state(r).score;s=crawler_fire(r,part,damage)
 for _ in range(20):
  if s.actors[part].state and s.score==before+reward:break
  r.run(1);s=state(r)
 assert s.actors[part].state and s.score==before+reward,(part,damage,s.score,before,s.actors[part].state)
assert state(r).score==score+20
r.close();report={'passed':True,'source_round':level+1,'source_row':row,'three_bodies':True,'initial_immunity':True,'weak_hit_score':0,'strong_hit_score':10,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/crawler-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
