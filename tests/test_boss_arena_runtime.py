"""Round 3 and 5 boss fights keep the player and camera inside the arena."""
import hashlib
from test_runtime import ROOT,Runner,state,put,finish_clear

r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(30)
checks=[]
for target in (2,4):
 while state(r).round<target:
  s=state(r);s.mode=5;s.mode_timer=1;finish_clear(r,s);r.run(8)
 s=state(r);assert s.round==target and s.mode==1
 camera=s.cam_x
 s.p.x=(camera+4)*256;s.p.vx=-2000;s.p.vy=0;s.previous_input=0
 for actor in s.actors:actor.active=0
 boss=s.actors[0];boss.active=1;boss.definition=39;boss.hp=80;boss.life=1;boss.state=2
 boss.x=(camera+100)*256;boss.y=s.p.y
 put(r,s);r.run(12);s=state(r)
 assert s.cam_x==camera and s.p.x>=(camera+8)*256,(target,'left edge',camera,s.cam_x,s.p.x//256)
 assert s.actors[0].active,'boss left the active fight'
 checks.append(dict(round=target+1,edge='left',camera=s.cam_x,player_x=s.p.x//256))
 s.p.x=(camera+220)*256;s.p.vx=2000;s.previous_input=0;put(r,s);r.run(12);s=state(r)
 assert s.cam_x==camera and s.p.x<=(camera+216)*256,(target,'right edge',camera,s.cam_x,s.p.x//256)
 assert s.actors[0].active,'boss left the active fight'
 checks.append(dict(round=target+1,edge='right',camera=s.cam_x,player_x=s.p.x//256))
r.close()
report=dict(passed=True,checks=checks,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual CLEAR-to-round transitions followed by an active boss fixture. Normal game ticks verify both horizontal player bounds and a fixed boss-room camera in rounds 3 and 5. This does not validate the physical cartridge or a complete natural boss fight.')
(ROOT/'reports/boss-arena-runtime-tests.json').write_text(__import__('json').dumps(report,indent=2)+'\n');print(__import__('json').dumps(report))
