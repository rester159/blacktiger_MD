"""Read real VDP scroll/pixels for mountain and stained-glass parallax."""
import ctypes as C,hashlib,json
import numpy as np
from PIL import Image
from test_runtime import ROOT,Runner,state,put,check_video_cache
checks=[]
for level,cx,cy in [(4,640,768),(6,784,304)]:
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(80)
 s=state(r);s.mode=2;s.cam_x=cx;s.cam_y=cy;s.p.x=s.p.y=-1024*256
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 put(r,s);r.run(80)
 v=(C.c_uint8*65536).in_dll(r.lib,'vram')
 def word(a):return (v[a^1]<<8)|v[(a+1)^1]
 def near():
  s=state(r);pixels=np.zeros((224,256),np.uint8)
  for y in range(224):
   wy=y+s.cam_y
   for x in range(256):
    wx=x+s.cam_x;w=word(0xe000+(((wy//8)&31)*64+((wx//8)&63))*2)
    tx=7-(wx&7) if w&0x800 else wx&7;ty=7-(wy&7) if w&0x1000 else wy&7
    b=v[((w&2047)*32+ty*4+tx//2)^1];pen=b&15 if tx&1 else b>>4
    pixels[y,x]=(((w>>13)&3)*16+pen) if pen else 0
  return pixels
 a=r.frame.copy();na=near();hud=[word(0xc000+y*128+x*2) for y in range(5) for x in range(32)]
 s=state(r);s.cam_x+=16;put(r,s);r.run(40);b=r.frame.copy();nb=near()
 assert np.array_equal(na[:,16:],nb[:,:-16]),(level,'foreground did not move exactly 16px')
 mask=(na[:,8:]==0)&(nb[:,:-8]==0);mask[:40]=False;mask[200:]=False;mask[88:112]=False
 assert mask.sum()>1000,(level,'insufficient exposed backdrop')
 assert len(np.unique(a[:,8:][mask],axis=0))>2,(level,'backdrop is blank')
 assert np.array_equal(a[:,8:][mask],b[:,:-8][mask]),(level,'background did not move exactly 8px')
 for row in range(28):
  assert word(0xf000+row*32+2)==(-(cx+16))&65535
  assert word(0xf000+row*32)==((-(cx+16)//2)&65535 if 5<=row<25 else 0)
 assert hud==[word(0xc000+y*128+x*2) for y in range(5) for x in range(32)]
 check_video_cache(r,state(r))
 s=state(r);s.mode=3;put(r,s);r.run(30)
 registers=(C.c_uint8*32).in_dll(r.lib,'reg')
 assert registers[11]&3==0 and word(0xf000)==word(0xf002)==0,'Shop planes shifted'
 assert r.read('arena_video_active',1)==b'\0'
 s=state(r);s.mode=2;put(r,s);r.run(30)
 assert np.array_equal(near(),nb),'shop changed foreground'
 assert int.from_bytes(r.read('video_cache_faults'),'big')==0
 assert int.from_bytes(r.read('vblank_flush_overruns'),'big')==0
 s=state(r);s.mode=0;put(r,s);r.run(30);assert r.read('arena_video_active',1)==b'\0'
 checks.append(dict(level=level+1,foreground_pixels=16,background_pixels=8,exposed_pixels=int(mask.sum()),hud_fixed=True,shop_restored=True,title_reset=True))
 r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),checks=checks,scope='Real ROM VRAM and pixel comparisons; source terrain stays at normal speed, masked scenery at half speed. Source layouts/collision are unchanged. Not a full-level playthrough.')
(ROOT/'reports/backdrop-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
