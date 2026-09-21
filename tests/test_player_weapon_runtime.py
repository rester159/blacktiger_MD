#!/usr/bin/env python3
"""Real Genesis input: chain timing/rendering and one-hit collision gate."""
import json,hashlib,struct
from test_runtime import ROOT,Runner,state,put
ref=json.loads((ROOT/'reference/player_motion_oracle.json').read_text())
source={}
for line in (ROOT/'reference/player_motion_oracle_events.txt').read_text().splitlines():
 if not line.startswith('ATTACK|'):continue
 _,case,tick,raw,counters,slots=line.split('|');c=ref['cases'][int(case)]
 if c.get('attack') and c['geometry']==0 and not c['reversed'] and c['pattern']==[16] and not c['hit']:
  raw=bytes.fromhex(raw);co=bytes.fromhex(counters);slots=bytes.fromhex(slots)
  source[c['tier'],int(tick)]=[raw[0],raw[1],raw[3],raw[2],co[0],co[3],co[4],sum(bool(slots[i*5]) for i in range(6))]
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);checks=0
for tier in range(5):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.mode=1;s.p.x=112*256;s.p.y=896*256;s.p.weapon=tier+1;s.p.face=0;s.p.invincible=10000;s.previous_input=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 r.write('player_attack',0,bytes(12));r.write('player_daggers',0,bytes(18*9));r.write('player_motion',0,struct.pack('>5H20B',65520,752,128,144,0,*([0]*20)));put(r,s)
 previous=s.frame;tick=0
 for _ in range(240):
  r.run(1,2);s=state(r)
  if s.frame==previous:continue
  previous=s.frame;tick+=1;a=r.read('player_attack',12)
  actual=[a[0],a[1],a[4],a[5],a[7],a[8],a[10],a[11]]
  assert actual==source[tier,tick],(tier,tick,actual,source[tier,tick])
  checks+=1
  if tick==10:
   s.mode=2;s.p.invincible=0;put(r,s);r.run(12)
   r.capture('player-chain-tier-%d.png'%(tier+1))
   sat=r.read('vdpSpriteCache',64*8);pieces=[];keys=struct.unpack('>80H',r.read('sprite_keys',160))
   for at in range(0,512,8):
    y,size,link,attr,x=struct.unpack_from('>HBBHH',sat,at)
    if size==5:
     key=keys[((attr&2047)-1088)//4];pieces.append((key&2047,x-128+s.cam_x,y-128+s.cam_y))
    if not link:break
   expected=(0x6f+tier,112+32+16*(a[11]-1),902)
   assert expected in pieces,(tier,expected,pieces)
   s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);previous=s.frame
  if tick==60:break
 else:raise AssertionError(('Controller stopped',tier,tick))
# Ground crawlers sit below the standing chain; a crouched chain hits them.
s=state(r);s.mode=2;put(r,s);r.run(20)
s=state(r);s.mode=1;s.p.x=128*256;s.p.y=896*256;s.p.weapon=1;s.p.face=0;s.p.invincible=10000;s.previous_input=0
for a in s.actors:a.active=0
for q in s.shots:q.active=0
for i in range(160):s.spawned[i]=2
roots=json.loads((ROOT/'reference/crawler.json').read_text())['roots']
for i in range(2):
 a=s.actors[i];a.active=1;a.definition=8;a.hp=1;a.life=1;a.state=0;a.hit=0;a.source=i;a.x=176*256;a.y=912*256;a.vx=a.vy=0;a.face=-1
 r.write('crawlers',i*14,struct.pack('>HHbbBxHBBBB',0,100,0,0,0,roots[10],0,0,8,0))
r.write('player_attack',0,bytes(12));r.write('player_daggers',0,bytes(18*9));r.write('shop_poison',0,b'\x26');put(r,s);kills=s.kills;hit=False
for _ in range(60):
 r.run(1,34);a=r.read('player_attack',12)
 if a[9]:
  assert a[8] and a[7]==10 and sum(v.state==1 for v in state(r).actors[:2])==1,(a.hex(),state(r).kills,kills)
  hit=True;break
assert hit,'Chain never hit ground crawler'
r.run(30,34);assert state(r).kills==kills+1,'Chain hit more than one actor during a single attack'
r.close();rom=(ROOT/'out/release/rom.bin').read_bytes()
report=dict(passed=True,controller_updates=checks,rendered_chain_heads=5,one_hit_gate=True,rom_sha256=hashlib.sha256(rom).hexdigest(),scope='Input-driven five-tier chain timing matches arcade traces; hardware sprites show the matching head reach; crouched chain applies one damage event and shortens its hold.')
(ROOT/'reports/player-weapon-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
