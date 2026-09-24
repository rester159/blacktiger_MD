#!/usr/bin/env python3
import hashlib,json
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire
from test_loot_runtime import drops
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
slot,row,level=fixture(r,0,4,0xb338);s=state(r);a=s.actors[slot]
assert a.hp==255 and s.spawned[row]==1
x,y=a.x,a.y;score=s.score;kills=s.kills
s=fire(r,slot,16,0);assert s.actors[slot].hp==239 and s.actors[slot].hit==0
assert s.actors[slot].x==x and s.actors[slot].y==y
# Trigger within 64 pixels; follow below it so the landing stays within the camera.
s.mode=1;s.p.x=x-32*256;s.p.y=y+128*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s)
phases=set();capture=False
for _ in range(600):
 r.run(1);s=state(r);raw=r.read('boulders',14*24)[slot*14:(slot+1)*14]
 if s.actors[slot].active:
  phases.add(raw[12])
  if raw[11] and not capture:
   assert raw[12]==2 and abs(s.actors[slot].vx)==256
   s.mode=2;put(r,s);r.run(20);r.capture('boulder-bounce.png');s=state(r);s.mode=1
   # Center the contact rather than placing it on a moving bounce edge.
   s.p.x=s.actors[slot].x;s.p.y=s.actors[slot].y;s.p.vx=s.p.vy=0;s.p.armor=4;s.p.hp=4;s.p.invincible=0;put(r,s)
   contact_start=s.frame
   for contact_tick in range(120):
    r.run(1);s=state(r)
    if s.p.armor!=4 or ((s.frame-contact_start)&65535)>=12:break
   assert s.p.armor==2 and s.p.hp==4,'Bounce contact retained falling damage'
   s.p.invincible=10000;put(r,s);capture=True
 else:break
else:raise AssertionError('Boulder did not finish its fall/bounces')
assert phases=={50,2} and capture,phases
assert s.spawned[row]==2 and s.score==score and s.kills==kills and not drops(r)
assert s.mode==1 and s.boss_dead==0
# A weapon can break an untriggered boulder; it must not permanently consume the row.
slot,row,level=fixture(r,0,4,0xb338);s=state(r);score=s.score
s=fire(r,slot,255,0);assert s.actors[slot].active and s.actors[slot].state==1 and s.spawned[row]==1
# Move outside spawn range but within the existing actor's despawn margin to observe retirement.
s.p.x=s.actors[slot].x+280*256;s.p.y=s.actors[slot].y;put(r,s)
for _ in range(120):
 r.run(1);s=state(r)
 if not s.actors[slot].active:break
else:raise AssertionError('Destroyed boulder did not retire')
assert s.spawned[row]==0 and s.score==score+300 and not drops(r)
r.close();report={'passed':True,'source_round':level+1,'source_row':row,'contact_damage_phases':sorted(phases),'weapon_health':255,'activation_persistence':2,'untriggered_retirement_persistence':0,'natural_score':0,'weapon_score':300,'no_drop':True,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/boulder-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
