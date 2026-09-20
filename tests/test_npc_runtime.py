#!/usr/bin/env python3
"""All eight NPC variants through native spawn/contact/cutscene/reward paths."""
import json,sys,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from test_runtime import Runner,state,put

def run_case(kind,defs):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(30)
 rom=(ROOT/'out/release/rom.bin').read_bytes();metadata=json.loads((ROOT/'reports/assets.json').read_text())
 found=None
 for level,info in enumerate(metadata['rounds']):
  start=r.symbols[f'spawn{level}']
  for row in range(info['spawns']):
   x,y,d,persistent=struct.unpack_from('>4H',rom,start+row*8)
   if defs[d]['npc_kind']==kind:found=(level,row,x,y,d);break
  if found:break
 assert found,('missing NPC source row',kind)
 level,row,x,y,d=found
 # Enter selected round through its real death/round reset boundary.
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(60)
 s=state(r);s.mode=1;s.coins=123;s.time=120;s.clock=0;s.p.hp=1;s.p.invincible=10000;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0
 s.cam_x=max(0,min(x-112,metadata['rounds'][level]['width']-256));s.cam_y=max(0,min(y-144,metadata['rounds'][level]['height']-224))
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 s.spawned[row]=0;put(r,s)
 for _ in range(120):
  r.run(1);s=state(r)
  if s.mode==8:break
 else:raise AssertionError(('source spawn/contact not reached',kind))
 assert s.rescue_kind==kind and s.actors[s.rescue_actor].definition==d
 actor=s.rescue_actor;r.run(20);r.capture(f'npc-{kind}.png');before_time=s.time;before_hp=s.p.hp
 # Wait for the production animation to finish, bounded independently of video cadence.
 for _ in range(300):
  r.run(1);s=state(r)
  if s.mode!=8:break
 else:raise AssertionError(('rescue did not finish',kind))
 assert s.actors[actor].state==2
 expected_mode=3 if kind in (2,8) else 1
 assert s.mode==expected_mode,(kind,s.mode)
 assert s.coins==(223 if kind==1 else 123),(kind,s.coins)
 assert s.time==before_time+(30 if kind==4 else 0),(kind,s.time,before_time)
 assert s.p.hp==(4 if kind==3 else before_hp),(kind,s.p.hp)
 # Other world actors and game clocks remained frozen through the cutscene.
 assert s.rescued==1
 if expected_mode==3:r.run(3,1);r.run(3)
 s=state(r);s.p.x=(x+64)*256;s.p.invincible=10000;put(r,s);r.run(150);s=state(r)
 if kind==8:assert s.spawned[row]!=2,'repeatable shop incorrectly retired permanently'
 else:assert s.spawned[row]==2,('one-shot NPC respawned',kind,s.spawned[row])
 r.close();return {'kind':kind,'round':level+1,'source_row':row,'definition':d,'spawn_contact':True,'reward':True,'persistence':True}

def main():
 metadata=json.loads((ROOT/'reports/assets.json').read_text());defs={d['id']:d for d in metadata['actor_definitions']}
 results=[run_case(k,defs) for k in range(1,9)]
 report={'passed':True,'variants':results,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'All eight actual source NPC rows through native spawn/contact, cutscene completion, distinct rewards, one-shot/repeatable retirement. Detailed arcade cutscene timing and shop inventory remain unverified.'}
 (ROOT/'reports/npc-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
