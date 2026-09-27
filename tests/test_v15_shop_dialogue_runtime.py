"""Exact US labels/prices, stale-digit removal and sprites behind dialogue."""
import ctypes as C,hashlib,json,struct
import numpy as np
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
rom=(ROOT/'out/release/rom.bin').read_bytes()
def words(r):
 v=(C.c_ubyte*65536).in_dll(r.lib,'vram')
 return lambda at:(v[at^1]<<8)|v[(at+1)^1]
def tap(r,key):r.run(8,key);r.run(8)
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
assert r.read('shop_difficulty',1)==b'\0'
s=state(r);s.mode=3;s.shop_item=0;s.coins=20000;put(r,s);r.run(30)
font=struct.unpack_from('>59H',rom,r.symbols['shop_font']);w=words(r)
cols=[3,7,12,17,23,27];prices=[100,1000,2400,9600,30,80,300,800,1600,150]
def labels(expected):
 for i,value in enumerate(expected):
  row,col=divmod(i,5);width=cols[col+1]-cols[col]
  actual=[w(0xc000+(20+row*3)*128+(cols[col]+x)*2) for x in range(width)]
  assert actual==[font[ord(c)-32] for c in str(value).ljust(width)],(i,value,actual)
labels(prices);exit_before=[w(0xc000+23*128+x*2) for x in range(27,31)]
# Long price -> short price must remove all previous digits, preserving EXIT.
r.write('shop_difficulty',0,b'\7');tap(r,128)
r.write('shop_difficulty',0,b'\0');tap(r,64);labels(prices)
assert [w(0xc000+23*128+x*2) for x in range(27,31)]==exit_before
r.capture('v15-us-shop.png')
for item,price in enumerate(prices):
 row,col=divmod(item,5);s=state(r);s.shop_item=row*6+col;s.coins=20000;s.p.weapon=1;s.p.armor=0;put(r,s)
 r.write('shop_antidotes',0,b'\0');r.write('container_keys',0,b'\0');r.run(8);tap(r,2)
 assert state(r).coins==20000-price,(item,price,state(r).coins)
r.close()
# Initialize the actual ladder sentry, then freeze its sprite across the message.
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
slot,_,_=fixture(r,0,2,0xb67f)
s=state(r);s.mode=8;s.rescue_kind=1;s.rescue_actor=23;s.p.invincible=0
s.actors[slot].x=(s.cam_x+96)*256;s.actors[slot].y=(s.cam_y+52)*256
for i,a in enumerate(s.actors):
 if i!=slot:a.active=0
put(r,s);r.write('npc_sequence',0,struct.pack('>HHHBB',100,0,0,1,1));r.run(20)
w=words(r);sat=[];index=0
for _ in range(64):
 at=0xf400+index*8;y=(w(at)&511)-128;size_link=w(at+2);attr=w(at+4);x=(w(at+6)&511)-128
 sat.append((x,y,8*((size_link>>8&3)+1),attr))
 index=size_link&127
 if not index:break
snake=[s for s in sat if s[0]==96 and s[1]==52];assert snake,sat
assert all(not attr&0x8000 for x,y,h,attr in sat if y<80 and y+h>48),sat
with_snake=r.frame[48:80].copy();r.capture('v15-dialogue-snake.png')
s=state(r);s.actors[slot].active=0;put(r,s);r.run(20)
# Every opaque dialogue pixel stays identical with and without the snake.
glyphs=struct.unpack('>2048H',(ROOT/'res/generated/npc_dialogue_glyphs.bin').read_bytes())
v=(C.c_ubyte*65536).in_dll(r.lib,'vram');mask=np.zeros((32,256),bool)
for y in range(4):
 for x in range(32):
  tile=w(0xc000+(y+6)*128+x*2)&2047
  raw=bytes(v[(tile*32+i)^1] for i in range(32));pens=np.array([[b>>4,b&15] for b in raw]).reshape(8,8)
  mask[y*8:y*8+8,x*8:x*8+8]=pens!=0
assert mask.sum()>3000
assert np.array_equal(with_snake[mask],r.frame[48:80][mask]),'Sprite covered opaque dialogue'
r.close()
report=dict(passed=True,us_prices=prices,actual_purchase_charges=True,stale_digits_cleared=True,exit_preserved=True,dialogue_opaque_pixels=int(mask.sum()),ladder_sentry_behind_dialogue=True,rom_sha256=hashlib.sha256(rom).hexdigest())
(ROOT/'reports/v15-shop-dialogue-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
