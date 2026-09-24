"""Level 5 parallax has no source-mountain fragments on the foreground plane."""
import hashlib,json
import numpy as np
from test_runtime import ROOT,Runner,state,put,check_video_cache
from test_assets import decode
from arcade_source import Source
source=Source();raw=source.read(12,0x8000,16384)
patterns=decode((ROOT/'res/generated/bg4.bin').read_bytes())
world=np.fromfile(ROOT/'res/generated/map4.bin',dtype='>u2').reshape(128,256)
mountains=[];previously_missed=[]
for y in range(64):
 for x in range(128):
  at=(x&15)|((y&15)<<4)|((x&112)<<4)|((y&48)<<7)
  lo,attr=raw[at*2:at*2+2];code=lo+((attr&7)<<8)
  if not 0x380<=code<=0x3df:continue
  for dy in range(2):
   for dx in range(2):
    word=int(world[y*2+dy,x*2+dx]);assert not patterns[(word&2047)-16].any(),('mountain fragment',x,y,hex(code))
  mountains.append([x*16,y*16])
  if code>=0x3d8:previously_missed.append([x*16,y*16,code])
assert previously_missed, 'test does not cover the omitted mountain base tiles'
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(exploration=True);r.run(20)
s=state(r);s.round=4;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
checks=[]
for name,cx,cy in (('left-ridge',128,736),('middle-ridge',640,768),('right-ridge',1088,736),('red-ridge',1232,0)):
 s=state(r);s.mode=2;s.cam_x=cx;s.cam_y=cy;s.p.x=s.p.y=-1024*256
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 put(r,s);r.run(60);check_video_cache(r,state(r))
 assert r.read('arena_video_active',1)==b'\1', 'level 5 parallax disabled'
 r.capture(f'v32-level5-{name}.png')
 for dx,dy in ((16,0),(16,16),(0,16)):
  s=state(r);s.cam_x=cx+dx;s.cam_y=cy+dy;put(r,s);r.run(30);check_video_cache(r,state(r))
 checks.append(dict(view=name,camera=[cx,cy],parallax=True))
assert int.from_bytes(r.read('video_cache_faults'),'big')==0
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),mountain_cells_removed=len(mountains),formerly_missed_cells=previously_missed,checks=checks,scope=__doc__+' Every source mountain cell in every palette is checked, including the previously omitted base tiles. Native camera fixtures validate resident tiles; half-speed movement has separate backdrop tests.')
(ROOT/'reports/level5-parallax-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
