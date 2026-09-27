"""Actual menu pixels, arcade poison colors, seated shop scene and terrain restoration."""
import ctypes as C,json,struct,hashlib
import numpy as np
from PIL import Image
from test_runtime import ROOT,Runner,state,put,check_video_cache
rom=ROOT/'out/release/rom.bin';checks=[]
def pause(r):
 s=state(r);s.mode=2;put(r,s);r.run(20);return state(r)
def centered(r,row,start,end):
 mask=r.frame[row*8:(row+1)*8,start:end].any(2);xs=np.nonzero(mask)[1]+start
 assert len(xs) and abs((xs.min()+xs.max()+1)/2-128)<=1,(row,xs.min(),xs.max())
def body(r):
 sat=r.read('vdpSpriteCache',8);y,size,link,attr,x=struct.unpack('>HBBHH',sat)
 assert size==15 and (attr>>13)&3==2,(size,hex(attr))
 vram=(C.c_uint8*65536).in_dll(r.lib,'vram');tile=attr&2047
 raw=bytes(vram[(tile*32+i)^1] for i in range(512));a=np.frombuffer(raw,np.uint8);pens=np.stack((a>>4,a&15),1).reshape(-1)
 cram=(C.c_uint16*64).in_dll(r.lib,'cram');colors=np.array([cram[32+i] for i in range(16)],np.uint16)[pens]
 return pens,colors
r=Runner(rom);r.run(100)
centered(r,18,96,168);centered(r,20,104,152)
assert not r.frame[184:192].any(),'main select hint still present'
logo=r.frame[:128].copy();r.run(8,2);r.run(25)
assert r.read('attract_running',1)==b'\1'
# Arcade presentation now has its own source-timed ranking/demo renderer.
for _ in range(2):r.run(8,8);r.run(8)
assert r.read('frontend',9)[4]==2 and r.read('attract_credit',1)==b'\1'
checks.append('centered main text, absent hint, Arcade attract and coin interruption')
r.run(8,2);r.run(40);r.run(8,2);r.run(20)
assert state(r).mode==1
vram=(C.c_uint8*65536).in_dll(r.lib,'vram')
actual=bytes(vram[(0xc000+3*128+22*2+i)^1] for i in range(20))
start=r.symbols['arcade_hud_map']+3*64+22*2
assert actual==rom.read_bytes()[start:start+20],'credit text overwrote the Zenny icon row'
checks.append('Arcade gameplay currency row matches original HUD; no credit overlay')

r.close()
# Same hero geometry and original purple skin overlay against unrelated backgrounds.
import sys
sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
source=Source();source.expect(None,0x195c,'21411b1106da010400edb01106de010400edb0c9')
raw=source.read(None,0x1b41,8)
expected_skin=np.array([(raw[i]>>5)|(((raw[i]&15)>>1)<<3)|(((raw[i+4]&15)>>1)<<6) for i in range(4)],np.uint16)
reference={}
r=Runner(rom);r.run(100);r.start_game();r.run(40)
for level,armor in ((level,armor) for level in (0,4,7) for armor in (0,2)):
 s=pause(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(45)
 s=pause(r);s.p.invincible=0;s.p.armor=armor;put(r,s)
 motion=bytearray(r.read('player_motion',30));motion[14]=motion[24]=motion[25]=0;r.write('player_motion',0,motion)
 r.write('shop_poison',0,b'\0');r.run(15);normal,normal_colors=body(r)
 hud_before=r.frame[:40].copy()
 base_cram=np.array((C.c_uint16*64).in_dll(r.lib,'cram')).copy()
 r.write('shop_poison',0,b'\x26');r.run(15);poison,colors=body(r)
 assert np.array_equal(normal,poison),'poison changed original pixel indices'
 assert np.isin(normal,[7,8,9,10]).any(),'skin shades missing from hero'
 assert np.isin(colors,expected_skin).any(),'purple poison skin missing'
 actual_cram=np.array((C.c_uint16*64).in_dll(r.lib,'cram')).copy()
 expected_cram=base_cram.copy();expected_cram[39:43]=expected_skin
 assert np.array_equal(r.frame[:40],hud_before),'poison tinted the HUD'
 assert np.array_equal(actual_cram,expected_cram),'poison changed colors outside the four source skin shades'
 if armor not in reference:reference[armor]=colors
 else:assert np.array_equal(colors,reference[armor]),'poison color depends on background'
 r.write('shop_poison',0,b'\0');r.run(15)
 assert np.array_equal(body(r)[1],normal_colors),'cure did not restore skin'
checks.append('armored and unarmored: exact arcade purple skin overlay; unchanged armor, transparency and unrelated palettes; cure restores colors on Levels 1, 5, 8')
r.close()
r=Runner(rom);r.run(100);r.start_game();r.run(40)
s=pause(r);s.mode=1;s.p.exploration=1;s.p.invincible=0
for actor in s.actors:actor.active=0
for i in range(160):s.spawned[i]=2
put(r,s)
for armor in (2,0):
 s=state(r);s.p.armor=armor;put(r,s);r.write('shop_poison',0,b'\x26');poses=set()
 for mask,ticks in ((128,45),(129,24),(0,35),(34,20),(64,35),(16,20)):
  for _ in range(ticks//3):
   r.run(3,mask);pens,colors=body(r)
   attr=struct.unpack_from('>H',r.read('vdpSpriteCache',8),4)[0]
   key=struct.unpack('>20H',r.read('body_keys',40))[((attr&2047)-1088)//16]
   assert key//2048==0,('poison left the hero palette atlas',key)
   poses.add(key%2048)
 assert len(poses)>=6,poses
 if armor==0:assert any(code>=256 for code in poses),'unarmored high sprite codes were not exercised'
checks.append('arcade poison colors remain stable through real walk, jump and attack inputs')
r.close()

# Death has no intrusive TRY AGAIN text; normal HUD remains visible.
r=Runner(rom);r.run(100);r.start_game();r.run(40)
s=pause(r);s.mode=4;s.mode_timer=150;put(r,s);r.run(15)
assert state(r).mode==4
vram=(C.c_uint8*65536).in_dll(r.lib,'vram')
assert not any(vram[(0xc000+11*128+i)^1] for i in range(64)),'death text remains on playfield'
assert r.frame[:40].any(),'death erased HUD'
checks.append('death animation keeps HUD and has no TRY AGAIN overlay')
r.close()

# Shop borrows background tiles, then restores the real level on exit.
expected=np.array(Image.open(ROOT/'reports/shop-backdrop-native.png').convert('RGB'))
# Genesis Plus GX uses 0x00/22/.../ee DAC levels before RGB565 expansion.
levels=np.rint(expected.astype(float)*7/255).astype(np.uint16)*34
expected=np.stack((((levels[:,:,0]>>3)*255//31),((levels[:,:,1]>>2)*255//63),((levels[:,:,2]>>3)*255//31)),2)
for level in range(8):
 r=Runner(rom);r.run(100);r.start_game();r.run(30)
 s=pause(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(45)
 s=pause(r);s.mode=3;s.p.invincible=10000;put(r,s);r.run(35)
 if level==0:
  from extract import decode
  board=json.loads((ROOT/'assets/board.json').read_text())
  sprite_art=decode(b''.join(source.files[f['path']] for f in board['regions']['sprites']['files']),board['layouts']['sprites'])
  cursor_base=1088+json.loads((ROOT/'reference/shop_graphics.json').read_text())['tiles']+40
  vram=(C.c_uint8*65536).in_dll(r.lib,'vram')
  for i,code in enumerate((0x148,0x149,0x14a,0x150,0x151,0x152)):
   raw=np.frombuffer(bytes(vram[((cursor_base+i*4)*32+j)^1] for j in range(128)),np.uint8)
   tiles=np.stack((raw>>4,raw&15),-1).reshape(4,8,8)
   pixels=np.concatenate((np.concatenate((tiles[0],tiles[1]),0),np.concatenate((tiles[2],tiles[3]),0)),1)
   assert np.array_equal(pixels==0,sprite_art[code]==15),'shop frame differs from arcade sprite shape'
   visible=set(pixels[pixels!=0]);cram=(C.c_uint16*64).in_dll(r.lib,'cram')
   assert all(((cram[48+v]>>6)&7)>((cram[48+v]>>3)&7)>(cram[48+v]&7) for v in visible),'shop frame is not arcade blue'
  positions=source.read(None,0x6e45,48)
  for choice in (0,1,2,3,4,6,7,8,9,10,11):
   fixture=state(r);fixture.shop_item=choice;put(r,fixture);r.run(12)
   box=positions[choice*4:choice*4+4]
   for i in range(6):
    yy,size,link,attr,xx=struct.unpack('>HBBHH',r.read('vdpSpriteCache',48)[i*8:i*8+8])
    assert (xx-128,yy-128)==(box[0]+i%3*box[1],box[2]-16+i//3*box[3]),(choice,i,xx,yy)
    assert size==5 and attr&2047==1088+json.loads((ROOT/'reference/shop_graphics.json').read_text())['tiles']+40+i*4 and (attr>>13)&3==3
  checks.append('all 11 shop selections use original six-piece blue frame and source positions')
 actual=r.frame[40:112].astype(int);target=expected[40:112].astype(int)
 assert np.array_equal(actual,target),('merchant room mismatch',level,np.max(np.abs(actual-target)))
 r.run(8,1);r.run(35);assert state(r).mode==1
 assert r.read('video_cache_faults')==b'\0\0'
 s=pause(r)
 if level!=3:check_video_cache(r,s)
 r.close()
checks.append('full seated merchant room in all 8 levels; clean exit and restored terrain')
report=dict(passed=True,checks=checks,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),scope=__doc__)
(ROOT/'reports/menu-shop-poison-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
