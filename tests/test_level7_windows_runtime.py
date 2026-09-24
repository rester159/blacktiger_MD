"""All static and alternate-area window tiles must expose the parallax plane."""
import hashlib,json,struct
import numpy as np
from test_runtime import ROOT,Runner,state,put,check_video_cache
from test_assets import decode
from arcade_source import Source
raw=Source().read(14,0x8000,16384)
patterns=decode((ROOT/'res/generated/bg6.bin').read_bytes())
world=np.fromfile(ROOT/'res/generated/map6.bin',dtype='>u2').reshape(128,256)
rom=(ROOT/'out/release/rom.bin').read_bytes()
r=Runner(ROOT/'out/release/rom.bin')
ptr,count=struct.unpack_from('>IH',rom,r.symbols['bonus_rounds']+6*20)
patches={struct.unpack_from('>H',rom,ptr+i*40)[0]:ptr+i*40 for i in range(count)}
phases=[]
for bank in json.loads((ROOT/'reference/bonus.json').read_text())['rounds'][6]['background']:
 for at in (0,4):phases.append({v['offset']:v['tile'] for phase in bank[at:at+4] for v in phase})
checked=[0,0]
for y in range(64):
 for x in range(128):
  idx=(x&15)|((y&15)<<4)|((x&112)<<4)|((y&48)<<7)
  tile=int.from_bytes(raw[idx*2:idx*2+2],'little')
  def window(t):
   code=(t&255)|((t>>8&7)<<8)
   return 0x580<=code<=0x59f or code==0x500
  if window(tile):
   for dy in range(2):
    for dx in range(2):assert not patterns[(int(world[y*2+dy,x*2+dx])&2047)-16].any()
   checked[0]+=1
  at=patches.get(y*128+x)
  if at is not None:
   for phase,m in enumerate(phases):
    if window(m.get(idx*2,tile)):
     for word in struct.unpack_from('>4H',rom,at+2+phase*8):assert not patterns[(word&2047)-16].any(),(x,y,phase)
     checked[1]+=1
assert checked[0],checked
r.run(100);r.start_game(exploration=True);r.run(20)
s=state(r);s.round=6;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
for name,cx,cy in [('reported-windows',0,304),('middle-windows',784,304)]:
 s=state(r);s.mode=2;s.cam_x=cx;s.cam_y=cy;s.p.x=s.p.y=-1024*256
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 put(r,s);r.run(60);check_video_cache(r,state(r));r.capture('v33-level7-'+name+'.png')
 assert r.read('arena_video_active',1)==b'\1'
assert int.from_bytes(r.read('video_cache_faults'),'big')==0
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),static_window_and_empty_cells=checked[0],alternate_window_variants=checked[1],scope=__doc__+' Native injected camera fixtures plus separate half-speed pixel checks; not a playthrough.')
(ROOT/'reports/level7-windows-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
