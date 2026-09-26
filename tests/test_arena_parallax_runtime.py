"""Hardware scroll ratios, fixed HUD, window masks and mode transitions."""
import ctypes as C,json,hashlib,numpy as np
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100)
for key in (32,8,32,8):r.run(12,key);r.run(12)
s=state(r);s.mode=2;s.p.invincible=0;put(r,s);r.run(8)
v=(C.c_uint8*65536).in_dll(r.lib,'vram')
def word(a):return (v[a^1]<<8)|v[(a+1)^1]
frames=[];hud=[]
for cx in (832,840,848,856,864,856,848,840,832):
 s=state(r);s.cam_x=cx;put(r,s);r.run(4)
 assert r.read('arena_video_active',1)==b'\1'
 for row in range(28):
  assert word(0xf000+row*32+2)==(-cx)&65535,(cx,row,'wall scroll',hex(word(0xf000+row*32+2)))
  assert word(0xf000+row*32)==((-cx//2)&65535 if 5<=row<25 else 0),(row,'far/HUD scroll')
 frames.append(r.frame.copy());hud.append(tuple(word(0xc000+y*128+x*2)for y in range(5)for x in range(32)))
assert hud[0]==hud[4],'HUD tile cells moved'
# At camera +16: world-fixed masonry shifts 16px. Window scenery moves 8px.
a,b=frames[0],frames[2]
assert np.array_equal(a[45:85,50:90],b[45:85,34:74]),'wall alignment'
from PIL import Image
Image.fromarray(a).save(ROOT/'reports/parallax-a.png');Image.fromarray(b).save(ROOT/'reports/parallax-b.png')
assert np.array_equal(a[110:140,192:208],b[110:140,184:200]),'scenery is not half-speed'
r.capture('arena-parallax.png')
s=state(r);s.mode=3;put(r,s);r.run(12)
registers=(C.c_uint8*32).in_dll(r.lib,'reg')
assert registers[11]&3==0 and word(0xf000)==word(0xf002)==0,'shop planes moved'
assert r.read('arena_video_active',1)==b'\0'
s=state(r);s.mode=2;put(r,s);r.run(12)
assert word(0xf000+20*32)==(-832//2)&65535
s=state(r);s.mode=0;put(r,s);r.run(15);assert r.read('arena_video_active',1)==b'\0'
r.capture('arena-parallax-title-return.png');r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),camera_positions=[832,840,848,856,864,856,848,840,832],wall_ratio=1,scenery_ratio=0.5,hud_fixed=True,shop_fixed=True,title_reset=True)
(ROOT/'reports/arena-parallax-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

# Columns are now original terrain, so they cannot flicker with SAT load.
column_checks=[]
for rush in (False,True):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100)
 if rush:
  for key in (32,8,32,8):r.run(12,key);r.run(12)
 else:
  r.start_game();s=state(r);s.round=7;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(30)
 s=state(r);s.mode=2;s.p.x=s.p.y=-1024*256;s.cam_y=64;s.cam_x=928
 for actor in s.actors:actor.active=0
 put(r,s);r.run(40);a=r.frame.copy()
 assert bool(r.read('arena_video_active',1)[0])==rush
 s=state(r);s.cam_x+=8;put(r,s);r.run(12);b=r.frame.copy()
 # Shaft at world X 968: includes its gold edge and nearby masonry.
 assert np.array_equal(a[50:100,40:56],b[50:100,32:48]),('column detached',rush)
 v=(C.c_uint8*65536).in_dll(r.lib,'vram');slot=0
 for _ in range(64):
  at=0xf400+slot*8;tile=word(at+4)&2047
  assert not 844<=tile<884,'columns still consume actor sprites'
  slot=word(at+2)&127
  if not slot:break
 r.capture('v21-palace-columns-rush.png' if rush else 'v21-palace-columns.png')
 assert int.from_bytes(r.read('video_cache_faults'),'big')==0
 r.close();column_checks.append(dict(boss_rush=rush,camera_step=8,column_step=8,wall_step=8,scenery_step=4 if rush else 8,columns_in_terrain=True))
report['column_checks']=column_checks
(ROOT/'reports/arena-parallax-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(column_checks))
