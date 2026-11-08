#!/usr/bin/env python3
"""Controller-driven opening-menu credits and complete text rendering."""
import ctypes as C,hashlib,json,re
from test_runtime import ROOT,Runner,state
names=[line[2:].split(' — ')[0].upper() for line in (ROOT/'docs/credits.md').read_text().splitlines() if line.startswith('- ')]
assert len(names)==len(set(names))==45 and all(len(n)<=30 for n in names)
pages=(len(names)+7)//8
r=Runner(ROOT/'out/release/rom.bin');r.run(100)
def tap(key):r.run(6,key);r.run(6)
def front():return list(r.read('frontend',9))
vram=(C.c_uint8*65536).in_dll(r.lib,'vram')
def word(x,y):
 at=0xc000+y*128+x*2
 return ((vram[at^1]<<8)|vram[(at+1)^1])&2047
rom=(ROOT/'out/release/rom.bin').read_bytes()
font_data=rom[r.symbols['title_font']:r.symbols['title_font']+96*32]
def glyph(c):
 raw=font_data[(ord(c)-32)*32:(ord(c)-31)*32]
 return [[n for byte in raw[y*4:y*4+4] for n in (byte>>4,byte&15)] for y in range(8)]
def centered(y,s):
 # Compare rendered pixel indices, including sub-tile optical centering.
 glyphs=[glyph(c) for c in s]
 expected=[sum((g[row] for g in glyphs),[]) for row in range(8)]
 used=[x for x in range(len(s)*8) if any(expected[row][x] for row in range(8))]
 left,right=min(used),max(used)+1
 start=(256-(right-left))//2
 expected=[[0]*start+row[left:right]+[0]*(256-start-right+left) for row in expected]
 actual=[[] for _ in range(8)]
 for x in range(32):
  tile=word(x,y)
  raw=bytes(vram[(tile*32+k)^1] for k in range(32))
  for row in range(8):actual[row].extend(n for byte in raw[row*4:row*4+4] for n in (byte>>4,byte&15))
 assert actual==expected,(y,s,'rendered pixels')
centered(18,'HOME');centered(20,'ARCADE');centered(22,'CREDITS');r.capture('credits-opening-menu.png')
# Up wraps directly to Credits; Start opens it without inserting a coin.
tap(16);assert front()[2]==2
tap(8);assert front()[1:4]==[7,2,0] and front()[4]==0
for page in range(pages):
 assert front()[3]==page
 centered(2,'THANK YOU');centered(4,'PLAYTESTING AND COMMENTS')
 for i,name in enumerate(names[page*8:page*8+8]):centered(7+i*2,name)
 # The last, shorter page must erase the previous page's remaining names.
 for i in range(len(names[page*8:page*8+8]),8):
  assert all(word(x,7+i*2) in (0,1440) for x in range(32))
 r.capture('credits-page-%d.png'%(page+1));tap(128)
assert front()[3]==0
tap(64);assert front()[3]==pages-1
tap(32);assert front()[3]==0
tap(16);assert front()[3]==pages-1
r.run(700);assert state(r).mode==0 and front()[1]==7,'Credits entered attract mode'
for back in (8,2,1):
 tap(back);assert front()[1:3]==[0,2] and front()[4]==0
 centered(22,'CREDITS')
 tap(2);assert front()[1:4]==[7,2,0]
tap(1);tap(32);assert front()[2]==0
# Arcade remains the second entry and returns to its own selection.
tap(32);tap(2);assert front()[0:2]==[0,1]
tap(1);assert front()[1:3]==[0,1]
# Also enter/leave after choosing Home; Start must work in either mode.
tap(16);tap(8);assert front()[0:2]==[1,1]
tap(1);tap(32);tap(32);tap(8);assert front()[0:2]==[1,7]
tap(8);assert front()[0:3]==[1,0,2]
r.close()
report=dict(passed=True,names=len(names),pages=pages,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Controller navigation, all names rendered in VRAM, page wrap, stale text clearing, idle stability, all back buttons, no accidental coins, Arcade and Home return paths.')
(ROOT/'reports/credits-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
