"""Transparent level 5/6 HUD composition and all-menu cursor gutter regressions."""
import ctypes as C,hashlib,json
import numpy as np
from test_runtime import ROOT,Runner,state,put,check_video_cache
checks=[]
for level,x,y in ((4,320,864),(5,800,560),(6,944,448),(7,800,864)):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
 s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
 s.cam_x=x-112;s.cam_y=max(0,y-144);s.p.x=x*256;s.p.y=y*256
 for actor in s.actors:actor.active=0
 put(r,s);r.run(40);a=r.frame.copy();check_video_cache(r,state(r))
 s=state(r);s.cam_x+=16;put(r,s);r.run(40);b=r.frame.copy();check_video_cache(r,state(r))
 v=(C.c_uint8*65536).in_dll(r.lib,'vram')
 def word(at):return (v[at^1]<<8)|v[(at+1)^1]
 clear=np.zeros((224,256),bool)
 for yy in (*range(40),*range(200,224)):
  for xx in range(256):
   w=word(0xc000+(yy//8)*128+(xx//8)*2)
   tx=7-(xx&7) if w&0x800 else xx&7;ty=7-(yy&7) if w&0x1000 else yy&7
   byte=v[((w&2047)*32+ty*4+tx//2)^1]
   clear[yy,xx]=(byte&15 if tx&1 else byte>>4)==0
 assert clear.sum()>11000,(level,'HUD fills obscure the world',int(clear.sum()))
 r.capture(f'v25-scenery-level{level+1}.png')
 for row in (*range(5),25,26,27):
  for i in range(64):v[(0xc000+row*128+i)^1]=0
 r.run(3)
 assert np.array_equal(b[clear],r.frame[clear]),(level,'transparent HUD changed scenery')
 checks.append(dict(level=level+1,cache_matches=True,transparent_hud_pixels=int(clear.sum()),scenery_preserved_behind_hud=True));r.close()
# Controller navigation covers every frontend family, including Arcade DIP.
r=Runner(ROOT/'out/release/rom.bin');r.run(100)
def tap(key):r.run(12,key);r.run(12)
def cursor(label_x,name):
 v=(C.c_uint8*65536).in_dll(r.lib,'vram')
 def word(a):return (v[a^1]<<8)|v[(a+1)^1]
 x=(word(0xf406)&511)-128;y=(word(0xf400)&511)-128;tile=word(0xf404)&2047
 right=-1
 for xx in range(16):
  for yy in range(16):
   at=(tile+(xx//8)*2+yy//8)*32+(yy%8)*4+(xx%8)//2
   val=v[at^1];pen=val&15 if xx&1 else val>>4
   if pen:right=max(right,x+xx)
 assert right>=x+8 and right<label_x*8-1,(name,x,right,label_x)
 assert 0<=y<224,(name,'cursor offscreen')
 r.capture(f'v20-cursor-{name}.png');checks.append(dict(menu=name,gutter_pixels=label_x*8-right-1))
cursor(13,'mode-picker');tap(2);assert r.read('attract_running',1)==b'\1';tap(32);cursor(2,'dip')
tap(1);tap(1);tap(32);tap(2);cursor(14,'home');tap(128);tap(8);cursor(2,'options');tap(1)
for key in (16,16,32,32,64,128,64,128):tap(key)
tap(2);cursor(2,'debug')
r.close()
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
s=state(r);s.mode=2;put(r,s);r.run(20)
for item in (0,1,2,3,4,6,7,8,9,10,11):
 s=state(r);s.mode=3;s.shop_item=item;put(r,s);r.run(20)
 # Shop uses the arcade frame around the cell, not a title cursor in its gutter.
 sat=r.read('vdpSpriteCache',48)
 assert sat[2]==5 and sat[3]==1 and sat[43]==0
 r.capture(f'v20-cursor-shop-{item}.png');checks.append(dict(menu=f'shop-{item}',arcade_frame_sprites=6))
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),checks=checks,scope=__doc__+' Camera fixtures injected; frontend navigation uses normal inputs. Source red/purple platforms retained.')
(ROOT/'reports/scenery-fixes-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
