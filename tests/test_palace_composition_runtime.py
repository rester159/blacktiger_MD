"""Level 8 restores all original scenery and scrolls it with the terrain, without parallax."""
import hashlib,json
import numpy as np
from test_runtime import ROOT,Runner,state,put,check_video_cache
from test_assets import decode
palette=np.fromfile(ROOT/'res/generated/pal7.bin',dtype='>u2')
source=np.load(ROOT/'res/generated/scenery7.npy')
patterns=decode((ROOT/'res/generated/bg7.bin').read_bytes())
world=np.fromfile(ROOT/'res/generated/map7.bin',dtype='>u2').reshape(128,256)
actual=np.zeros(source.shape,np.uint16)
for y in range(128):
 for x in range(256):
  w=int(world[y,x]);tile=patterns[(w&2047)-16]
  if w&0x800:tile=tile[:,::-1]
  if w&0x1000:tile=tile[::-1]
  actual[y*8:y*8+8,x*8:x*8+8]=palette[tile+((w>>13)&1)*16]
assert np.array_equal(actual,palette[source]),'Original level 8 scenery was masked, moved, or repeated'
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(exploration=True);r.run(20)
s=state(r);s.round=7;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
checks=[]
for name,cx,cy in (('start',0,720),('lower-hall',784,720),('open-air',1408,416),('upper-hall',832,64),('boss',1648,48)):
 s=state(r);s.mode=2;s.cam_x=cx;s.cam_y=cy;s.p.x=s.p.y=-1024*256
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 put(r,s);r.run(60);check_video_cache(r,state(r))
 assert r.read('arena_video_active',1)==b'\0','Level 8 parallax still active'
 r.capture(f'v29-level8-{name}.png')
 before=r.frame.copy()
 s=state(r);s.cam_x=cx+16;put(r,s);r.run(30)
 assert np.array_equal(before[40:85,16:],r.frame[40:85,:-16]), 'Original scenery does not move with the foreground'
 check_video_cache(r,state(r))
 for dx,dy in ((16,0),(16,16),(0,16)):
  s=state(r);s.cam_x=cx+dx;s.cam_y=cy+dy;put(r,s);r.run(30);check_video_cache(r,state(r))
 checks.append(dict(view=name,camera=[cx,cy],parallax=False,scroll_positions=5))
assert int.from_bytes(r.read('video_cache_faults'),'big')==0
assert int.from_bytes(r.read('vblank_flush_overruns'),'big')==0
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),source_pixels_preserved=int(source.size),checks=checks,scope=__doc__+' Full indexed-map color comparison plus injected native camera fixtures; All source scenery colors, architecture and sky retained. Pixel scrolling verified at 1:1 speed; Boss Rush has separate parallax checks. Not a full playthrough.')
(ROOT/'reports/palace-composition-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
