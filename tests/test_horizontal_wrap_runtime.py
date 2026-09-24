"""Horizontal map joins: movement, scrolling, terrain pixels and native spawns."""
import hashlib,json,struct
from test_runtime import ROOT,Runner,state,put,check_video_cache
rom=(ROOT/'out/release/rom.bin').read_bytes();meta=json.loads((ROOT/'reports/assets.json').read_text());checks=[]
def setup(level,x,y,isolated=True):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(exploration=True);r.run(20)
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
 s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
 s.mode=1;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0
 s.cam_x=(x-112)&65535;s.cam_y=max(0,min(y-144,meta['rounds'][level]['height']-224))
 for a in s.actors:a.active=0
 if isolated:
  for i in range(160):s.spawned[i]=2
 put(r,s);r.run(20);return r

def signed(v):return (v+32768)%65536-32768
# Continuous support across these seams isolates the wrap from jumping rules.
for level,y in ((0,368),(1,736),(2,1056),(3,272),(4,224),(5,32)):
 width=meta['rounds'][level]['width']
 for direction in (-1,1):
  x=16 if direction<0 else width-48;r=setup(level,x,y)
  before=state(r);start_reload=int.from_bytes(r.read('video_reload_count'),'big');camera=signed(before.cam_x)
  for frame in range(100):
   r.run(1,64 if direction<0 else 128);s=state(r)
   next_camera=signed(s.cam_x)
   assert abs(next_camera-camera)<=4,(level,direction,'camera jumped',camera,next_camera)
   camera=next_camera
   assert s.mode==1,(level,direction,'left gameplay',s.mode)
   if (s.p.x//256<=-16 if direction<0 else s.p.x//256>=width+16):break
  else:raise AssertionError((level,direction,'edge still blocked',s.p.x//256,s.p.y//256))
  assert int.from_bytes(r.read('video_reload_count'),'big')==start_reload,'crossing reloads the level'
  assert s.p.armor==before.p.armor and s.p.lives==before.p.lives and s.time==before.time
  s.mode=2;put(r,s);r.run(30);check_video_cache(r,state(r))
  assert int.from_bytes(r.read('video_cache_faults'),'big')==0
  checks.append(dict(level=level+1,direction=direction,x=s.p.x//256,continuous_camera=True,wrapped_tiles_match=True));r.close()
# Reproduce the screenshots' actual platforms: both need an ordinary jump to
# clear the terrain at the join. Real terrain stays intact.
for level,x,y,mask in ((1,1992,528,129),(2,40,848,65),(3,1992,224,129),(4,1992,480,129)):
 r=setup(level,x,y);r.capture(f'wrap-level-{level+1}-before.png');r.run(35,mask);s=state(r)
 width=meta['rounds'][level]['width']
 assert s.mode==1 and (s.p.x<0 if mask==65 else s.p.x>width*256),(level,'reported seam',s.p.x//256)
 r.capture(f'wrap-level-{level+1}-after.png');r.close()
# Native source rows on the far side must spawn into the current lap, not
# disappear or materialize thousands of pixels away.
spawn_checks=[]
for x,y,direction in ((2040,416,1),(24,224,-1)):
 r=setup(3,x,y,False);r.run(40);s=state(r);across=[]
 for actor in s.actors:
  if not actor.active:continue
  raw_x=struct.unpack_from('>H',rom,r.symbols['spawn3']+actor.source*8)[0]
  if (raw_x<128 and actor.x//256>2000 if direction>0 else raw_x>=1920 and actor.x//256<0):across.append(actor.source)
 assert across,('no opposite-edge actors in visible lap',direction)
 spawn_checks.append(dict(direction=direction,rows=across));r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),checks=checks,reported_platforms_crossed=[2,3,4,5],opposite_edge_actor_rows=spawn_checks,scope=__doc__+' Player positions injected at fixture entry; normal controller input thereafter. Isolated geometry cases suppress actors; a separate native-spawn case verifies the opposite edge. No complete playthrough or hardware test.')
(ROOT/'reports/horizontal-wrap-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
