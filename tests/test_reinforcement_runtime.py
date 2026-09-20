#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
def defeat(r,slot):
 for _ in range(12):
  for wait in range(160):
   s=state(r)
   if not s.actors[slot].active or s.actors[slot].state==2:return s
   if not (r.read('fighters',16*24)[slot*16+10]&1):break
   s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
  else:raise AssertionError('fighter did not become vulnerable')
  s=fire(r,slot,255,0)
 raise AssertionError('fighter did not lose its layers')
cases=[]
for pc in (0x8344,0x9af6,0x8ef4):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
 slot,row,level=fixture(r,0,2,pc,approach=0,vertical=0,hold_position=True)
 raw=r.read('reinforcement_rows',480);assert raw[row*3+1:row*3+3]==bytes([1,1])
 s=state(r);assert s.spawned[row]==0
 rom=(ROOT/'out/release/rom.bin').read_bytes();x,y,definition,_=struct.unpack_from('>4H',rom,r.symbols[f'spawn{level}']+row*8)
 # Defeating the first appearance must not consume the second constructor attempt.
 s=state(r);s.p.x=(x+70)*256;put(r,s)
 s=defeat(r,slot);assert s.spawned[row]==0
 s.mode=2;put(r,s);r.run(20)
 # Outside the source proximity rectangle, eligible-call delay stops advancing.
 start=r.read('reinforcement_rows',480)[row*3:row*3+3]
 for _ in range(50):
  s=state(r);s.mode=1;s.p.x=(x+70)*256;s.p.y=y*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
 assert r.read('reinforcement_rows',480)[row*3:row*3+3]==start
 for _ in range(800):
  s=state(r);s.mode=1;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
  s=state(r)
  if s.spawned[row]&2:break
 else:raise AssertionError(('second appearance missing',hex(pc)))
 assert r.read('reinforcement_rows',480)[row*3:row*3+3]==bytes([0,1,2])
 actors=[i for i,a in enumerate(s.actors) if a.active and a.source==row];assert len(actors)==1
 s=defeat(r,actors[0]);assert s.spawned[row]==2
 for _ in range(180):
  s=state(r);s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
 assert not any(a.active and a.source==row for a in state(r).actors)
 before=r.read('reinforcement_rows',480)[row*3:row*3+3]
 s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(80)
 assert r.read('reinforcement_rows',480)[row*3:row*3+3]==before and state(r).spawned[row]==2
 s=state(r);s.round=0;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(80)
 assert r.read('reinforcement_rows',480)[row*3:row*3+3]==bytes(3)
 cases.append(dict(restart_preserves=True,new_round_resets=True,constructor=pc,round=level+1,row=row,two_appearances=True,proximity_pauses_delay=True,no_third_appearance=True));r.close()
report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual source rows use the two-attempt constructor schedule. All three native fighter profiles integrated; complete routes remain unverified.')
(ROOT/'reports/reinforcement-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
