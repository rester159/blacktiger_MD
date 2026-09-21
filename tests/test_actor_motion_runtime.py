"""Real actor paths retire at source screen edges, preserving consumed rows."""
import hashlib,json
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);checks=[]
for bank,constructor in ((0,0x93ed),(0,0x9b85),(0,0xa35c),(2,0xa6f8)):
 for persistence in (1,3):
  slot,row,level=fixture(r,0,bank,constructor)
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
r.close();report=dict(passed=True,cases=checks,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual spawn/update paths for three skeleton variants and wisp; controlled right-edge retirement, no kill reward, consumed-state preservation. Other actor families and edge sprite wrapping remain separate.')
(ROOT/'reports/actor-motion-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
