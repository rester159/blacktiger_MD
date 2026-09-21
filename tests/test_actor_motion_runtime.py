"""Real actor paths retire at source screen edges, preserving consumed rows."""
import hashlib,json
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);checks=[]
for bank,constructor in ((0,0x93ed),(0,0x9b85),(0,0xa35c),(2,0xa6f8),(0,0xab33),(1,0x92e6),(1,0x9f83),(2,0x8344),(4,0xa4d0),(3,0xaab3)):
 for persistence in (1,3):
  # Independent boot avoids retained source scanner delays and spawn quotas.
  r.close();r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
  options=dict(approach=32,vertical=0,wait_frames=300,hold_position=True) if constructor in (0xab33,0x9f83,0xaab3) else dict(approach=0,vertical=0,hold_position=True) if constructor in (0x8344,0xa4d0) else dict(approach=32,vertical=0,wait_frames=400,hold_position=True) if constructor==0x92e6 else {}
  slot,row,level=fixture(r,0,bank,constructor,**options)
  s=state(r);s.mode=2;put(r,s);r.run(60)
  s=state(r);s.mode=1;s.p.invincible=10000;s.spawned[row]=persistence
  # 320 is beyond the source right retirement boundary but well inside the
  # former broad +/-352 native pre-movement window. Keep the camera stationary.
  s.p.x=(s.cam_x+112)*256;s.p.y=(s.cam_y+144)*256
  a=s.actors[slot];a.x=(s.cam_x+320)*256;a.y=(s.cam_y+96)*256
  before_score=s.score;before_kills=s.kills;put(r,s)
  for _ in range(20):
   r.run(1);s=state(r)
   if not s.actors[slot].active:break
  assert not s.actors[slot].active,(bank,constructor,'missed retirement')
  assert s.spawned[row]==(persistence&2),(bank,constructor,persistence,s.spawned[row])
  assert s.score==before_score and s.kills==before_kills
  checks.append(dict(bank=bank,constructor=constructor,persistence=persistence))
# Hunter boss retains source mode bit 4 throughout ordinary movement. The same
# offscreen coordinate must not retire it; ordinary hunter above must retire.
slot,row,level=fixture(r,0,1,0x9fc4,approach=32,vertical=0)
s=state(r);s.mode=2;put(r,s);r.run(60)
s=state(r);s.mode=1;s.p.invincible=10000;s.p.x=(s.cam_x+112)*256;s.p.y=(s.cam_y+144)*256
s.actors[slot].x=(s.cam_x+320)*256;s.actors[slot].y=(s.cam_y+96)*256;start=s.frame;put(r,s)
for _ in range(120):
 r.run(1)
 if ((state(r).frame-start)&65535)>=4:break
else:raise AssertionError('protected boss fixture did not advance')
assert state(r).actors[slot].active,'protected hunter boss retired'
assert r.read('hunters',14*24)[slot*14+10]&16
r.close();report=dict(protected_hunter_boss=True,passed=True,cases=checks,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual spawn/update paths for ten definitions spanning skeletons, wisp, flailer, teleporter, hunter, reinforcement, edge caster and crawler; controlled right-edge retirement, no kill reward, consumed-state preservation. Hunter boss retirement suppression also checked. Other actor families and edge sprite wrapping remain separate.')
(ROOT/'reports/actor-motion-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
