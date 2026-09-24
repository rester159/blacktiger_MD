"""The out-of-map flailer row must not wrap into the reported Level 6 wall."""
import hashlib,json,struct
from test_runtime import ROOT,Runner,state,put
rom=(ROOT/'out/release/rom.bin').read_bytes();meta=json.loads((ROOT/'reports/assets.json').read_text());checks=[]
for x in (1976,-72):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(exploration=True);r.run(20)
 s=state(r);s.round=5;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
 s=state(r);s.mode=2;put(r,s);r.run(20)
 invalid=[]
 for row in range(meta['rounds'][5]['spawns']):
  sx,sy,definition,persistent=struct.unpack_from('>4H',rom,r.symbols['spawn5']+row*8)
  if sx>=2048 or sy>=1024:invalid.append((row,sx,sy))
 assert invalid==[(114,16352,224)],invalid
 s=state(r);s.mode=1;s.p.x=x*256;s.p.y=352*256;s.p.vx=s.p.vy=0;s.cam_x=(x-112)&65535;s.cam_y=208
 for a in s.actors:a.active=0
 s.spawned[111]=2  # Already-rescued NPC beside the reported player position.
 put(r,s);seen=set()
 for _ in range(600):
  r.run(1);s=state(r)
  assert s.mode==1
  for a in s.actors:
   if a.active:
    assert a.source!=114,'dormant off-map flailer wrapped into the wall'
    seen.add(a.source)
 assert 102 in seen and 2 in seen,('valid local/across-edge actors missing',seen)
 r.capture('v33-level6-wall-fixed.png' if x>0 else 'v33-level6-wall-negative-lap.png')
 checks.append(dict(player_x=x,frames=600,invalid_spawn_excluded=True,valid_sources=sorted(seen)))
 r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),checks=checks,scope=__doc__+' Initial player positions injected at both equivalent horizontal laps; nearby NPC marked rescued to keep gameplay active; normal source spawning and actor updates thereafter. Valid opposite-edge actors must remain enabled.')
(ROOT/'reports/level6-wall-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
