#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
def run(constructor,antidotes,invincible=0):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
 slot,row,level=fixture(r,0,1,constructor,approach=32,vertical=0,wait_frames=500,hold_position=True)
 s=state(r);definition=s.actors[slot].definition;score=s.score;x=s.actors[slot].x;y=s.actors[slot].y
 # Keep the real placement in view and the player within its source proximity gate.
 seen=set();retired=False;respawned=False
 for _ in range(500):
  s=state(r);s.mode=1;s.p.x=x-32*256;s.p.y=y;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
  s=state(r);active=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
  if not active:retired=True
  if active and retired:respawned=True;slot=active[0];break
  if active:
   raw=r.read('eruptions',10*24);seen.add(raw[active[0]*10+9])
 assert retired and respawned and seen=={0,1},(retired,respawned,seen)
 s=state(r);s.mode=2;put(r,s);r.run(20);r.capture('eruption-%04x.png'%constructor)
 # Freeze an actual flame in its damaging phase and exercise the game contact dispatch.
 s=state(r);s.p.x=x;s.p.y=y;s.p.vx=s.p.vy=0;s.p.hp=4;s.p.armor=2;s.p.invincible=invincible
 for a in s.actors:a.active=0
 s.actors[slot].active=1;s.actors[slot].definition=definition;s.actors[slot].x=x;s.actors[slot].y=y
 raw=bytearray(10*24);struct.pack_into('>HHbbBBBB',raw,10*slot,0,100,0,0,0,0,1,1);r.write('eruptions',0,raw)
 r.write('shop_antidotes',0,bytes([antidotes]));r.write('status_gate',0,b'\0');r.write('shop_poison',0,b'\0')
 s.mode=1;put(r,s)
 for _ in range(20):
  r.run(1)
  if (r.read('status_gate',1)[0] if invincible else state(r).p.armor<2):break
 else:raise AssertionError('Flame contact did not damage armor')
 assert state(r).p.armor==(2 if invincible else 1)
 assert r.read('shop_poison',1)[0]==(38 if constructor in (0x8b9b,0x8bf5) and not antidotes else 0)
 assert r.read('shop_antidotes',1)[0]==(0 if constructor in (0x8b9b,0x8bf5) else antidotes)
 # A collected POW removes the immune flame without a kill reward.
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);before=s.score;kills=s.kills;s.p.invincible=10000
 meta=json.loads((ROOT/'reports/assets.json').read_text());pickup=next(d['id'] for d in meta['actor_definitions'] if d['bank']==4 and d['address']==0xb515)
 a=s.actors[23];a.active=1;a.definition=pickup;a.source=159;a.state=a.hit=0;a.x=s.p.x+8*256;a.y=s.p.y+8*256
 s.mode=1;put(r,s)
 for _ in range(20):
  r.run(1)
  if not state(r).actors[slot].active:break
 else:raise AssertionError('POW did not remove flame')
 s=state(r);assert s.score==before and s.kills==kills
 r.close();return {'constructor':constructor,'round':level+1,'row':row,'antidotes':antidotes,'invincible':invincible,'recurrence_contact_pow':True}
cases=[run(pc,0) for pc in (0x8a5d,0x8a03,0x8b9b,0x8bf5)]+[run(0x8b9b,1),run(0x8b9b,0,1000)]
report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/eruption-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
