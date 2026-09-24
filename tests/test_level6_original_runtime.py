"""Level 6 retains original scenery geometry with the approved stone-color ramp and no parallax."""
import hashlib,json
import numpy as np
from test_runtime import ROOT,Runner,state,put,check_video_cache
from test_assets import decode
palette=np.fromfile(ROOT/'res/generated/pal5.bin',dtype='>u2')
source=np.load(ROOT/'res/generated/scenery5.npy')
patterns=decode((ROOT/'res/generated/bg5.bin').read_bytes())
world=np.fromfile(ROOT/'res/generated/map5.bin',dtype='>u2').reshape(128,256)
actual=np.zeros(source.shape,np.uint16)
for y in range(128):
 for x in range(256):
  w=int(world[y,x]);tile=patterns[(w&2047)-16]
  if w&0x800:tile=tile[:,::-1]
  if w&0x1000:tile=tile[::-1]
  actual[y*8:y*8+8,x*8:x*8+8]=palette[tile+((w>>13)&1)*16]
assert np.array_equal(actual,palette[source]),'Original level 6 scenery was masked, moved, or repeated'
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(exploration=True);r.run(20)
s=state(r);s.round=5;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
checks=[]
for name,cx,cy in (('temple',1568,0),('islands',160,208),('clouds',384,512),('spiked-platforms',256,368),('blue-arrows',576,224)):
 s=state(r);s.mode=2;s.cam_x=cx;s.cam_y=cy;s.p.x=s.p.y=-1024*256
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 put(r,s);r.run(60);check_video_cache(r,state(r))
 assert r.read('arena_video_active',1)==b'\0','Level 6 parallax still active'
 r.capture(f'v33-level6-{name}.png')
 for dx,dy in ((16,0),(16,16),(0,16)):
  s=state(r);s.cam_x=cx+dx;s.cam_y=cy+dy;put(r,s);r.run(30);check_video_cache(r,state(r))
 checks.append(dict(view=name,camera=[cx,cy],parallax=False,scroll_positions=4))
assert int.from_bytes(r.read('video_cache_faults'),'big')==0
assert int.from_bytes(r.read('vblank_flush_overruns'),'big')==0
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),source_pixels_preserved=int(source.size),checks=checks,scope=__doc__+' Full indexed-map color comparison plus injected native camera fixtures; original temple placement and all islands/clouds retained; spiked-island stone uses the approved nearby-rock colors. Not a full playthrough.')
(ROOT/'reports/level6-original-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
