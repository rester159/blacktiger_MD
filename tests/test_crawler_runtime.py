#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
def crawler_fire(r,slot,damage):
 s=state(r);s.mode=1;s.p.invincible=10000;a=s.actors[slot]
 q=s.shots[0];q.active=1;q.enemy=0;q.kind=1;q.damage=min(255,damage*2);q.life=30;q.vx=q.vy=0;q.x=a.x;q.y=a.y
 put(r,s)
 for _ in range(80):
  r.run(1);s=state(r)
  if not s.shots[0].active:return s
 raise AssertionError('Crawler dagger was not handled')
cases=[]
for profile,(bank,constructor,health,reward_points) in enumerate(((3,0xaab3,2,10),(3,0xb153,8,15),(7,0xa3b6,16,15),(3,0xb7f3,3,15))):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
 slot,row,level=fixture(r,0,bank,constructor,approach=32,vertical=0)
 s=state(r);score=s.score
 s=fire(r,slot,255,0);assert s.actors[slot].active and not s.actors[slot].state and s.score==score,'Dormant seed was not immune'
 parts=[]
 for _ in range(700):
  s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1);s=state(r)
  parts=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
  if len(parts)==3:break
 else:raise AssertionError(('Seed did not split',[(a.x//256,a.y//256,a.active) for a in s.actors if a.source==row]))
 assert s.spawned[row]&2 and all(s.actors[i].life==health for i in parts)
 r.run(30);s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('crawler-split-%d.png'%profile)
 # The source's custom damage branch retires a weakly hit crawler without a score;
 # a hit meeting its internal durability awards ten points.
 for part,damage,reward in zip(parts,(1,health,255),(0,reward_points,reward_points)):
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
 # Every hit body must actually leave the actor pool, including weak hits.
 for _ in range(180):
  r.run(1)
  if all(not state(r).actors[i].active for i in parts):break
 assert all(not state(r).actors[i].active for i in parts), 'Harmless ghost survived its death animation'
 assert state(r).score==score+2*reward_points
 assert state(r).mode==1 and not state(r).boss_dead, "Crawler must not clear the round"
 r.close();cases.append(dict(profile=profile,source_round=level+1,source_row=row,three_bodies=True,initial_immunity=True,health=health,weak_hit_score=0,strong_hit_score=reward_points))
# Hold a live poison body in place to exercise the cartridge's contact dispatch.
contacts=[];ref=json.loads((ROOT/'reference/crawler.json').read_text())
definition=next(d['id'] for d in json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions'] if (d['bank'],d['address'])==(7,0xa3b6))
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
for antidotes,gate in ((0,0),(1,0),(0,30)):
 s=state(r);s.mode=2;s.cam_x=16;s.cam_y=752;put(r,s);r.run(60)
 s=state(r);s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.armor=4;s.p.hp=4;s.p.invincible=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 a=s.actors[0];a.active=1;a.definition=definition;a.x=136*256;a.y=904*256;a.state=0;a.hp=1;a.life=16;a.source=0
 r.write('crawlers',0,struct.pack('>HHbbBxHBBBB',0,100,0,0,0,ref['roots'][26+4],0,0,8,0))
 r.write('status_gate',0,bytes([gate]));r.write('shop_antidotes',0,bytes([antidotes]));r.write('shop_poison',0,b'\0')
 s.mode=1;start=s.frame;put(r,s)
 for _ in range(15):
  r.run(1)
  if (state(r).frame-start)&65535>=3:break
 expected=0 if antidotes or gate else 1
 assert state(r).p.armor==4-expected,(antidotes,gate,state(r).p.armor)
 assert r.read('shop_poison',1)[0]==(38 if expected else 0)
 assert r.read('shop_antidotes',1)[0]==0
 contacts.append(dict(antidotes=antidotes,gate=gate,damage=expected))
r.close()
report={'passed':True,'cases':cases,'poison_contacts':contacts,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/crawler-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
