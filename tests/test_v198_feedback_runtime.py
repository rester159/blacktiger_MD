"""v1.9.8 itch.io feedback: owned-item shop marks and armor-level hero colors on the linked ROM."""
import ctypes as C,hashlib,json,struct
from test_runtime import ROOT,Runner,state,put
from arcade_source import Source
rom=ROOT/'out/release/rom.bin';data=rom.read_bytes();src=Source();checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
def rgb333(w):return ((w>>1)&7)|(((w>>5)&7)<<3)|(((w>>9)&7)<<6)
def arcade_pen(raw,i):
 # Same palette RAM decoding as the source overlay at DA00/DE00.
 return rgb333(((raw[i]>>5)<<1)|(((raw[i]&15)>>1)<<5)|(((raw[10+i]&15)>>1)<<9))
r=Runner(rom);r.run(100);r.start_game();r.run(30)
cram=(C.c_uint16*64).in_dll(r.lib,'cram');vram=(C.c_uint8*65536).in_dll(r.lib,'vram')
# Fixed 193C copies table 1ACB[F3AD] over hero pens 0-9 every update; pens 1-4 differ by level.
src.expect(None,0x193c,'3aadf3');levels=[]
for level in range(9):
 s=state(r);s.mode=1;s.p.armor=level;s.p.invincible=10000;put(r,s);r.run(6)
 raw=src.read(None,src.word(None,0x1acb+level*2),20)
 expected=[arcade_pen(raw,i) for i in range(1,5)];actual=[int(cram[33+i]) for i in range(1,5)]
 assert actual==expected,(level,actual,expected);levels.append(dict(level=level,cram=actual))
check('hero pens 1-4 follow every source armor level',len(levels)==9 and len({tuple(v['cram']) for v in levels})==4)
check('skin pens stay unpoisoned while armor colors change',[int(cram[39+i]) for i in range(4)]==[rgb333(w) for w in struct.unpack_from('>4H',data,r.symbols['object_palette']+14)])
s=state(r);s.p.armor=8;s.mode=1;put(r,s);r.run(6);r.capture('v198-gold-armor.png')
# Fixed 645A/6461 + 6910: owned weapons 1..F3AC and armor tiers 1..F3AD/2 get the red X.
tile=r.symbols['shop_mark_tiles'];cells=struct.unpack_from('>16B',data,r.symbols['shop_mark_cells'])
def marks():
 sat=r.read('vdpSpriteCache',16*8);found=[];at=0
 for _ in range(16):
  y,size,link,attr,x=struct.unpack_from('>HBBHH',sat,at*8)
  pattern=bytes(vram[((attr&2047)*32+i)^1] for i in range(128))
  if pattern==data[tile:tile+128]:found.append(((x-128)//8,(y-128)//8))
  if not link:break
  at=link
 return sorted(found)
cases=[]
for weapon,armor in ((1,0),(3,5),(5,8),(2,1)):
 # Leave and re-enter the shop so each inventory opens a fresh panel, as in play.
 s=state(r);s.mode=1;put(r,s);r.run(10)
 s=state(r);s.mode=3;s.shop_item=4;s.coins=20000;s.p.weapon=weapon;s.p.armor=armor;put(r,s);r.run(30)
 owned=[i for i in range(min(4,weapon-1))]+[4+i for i in range(min(4,armor>>1))]
 expected=sorted((cells[i*2],cells[i*2+1]) for i in owned);actual=marks()
 assert actual==expected,(weapon,armor,actual,expected)
 check(f'shop marks weapon {weapon} armor {armor}',True);cases.append(dict(weapon=weapon,armor=armor,marks=len(actual)))
 if weapon==5:r.capture('v198-shop-owned-marks.png')
check('shop restores the default hero armor pens',[int(cram[34+i]) for i in range(4)]==[rgb333(w) for w in struct.unpack_from('>4H',data,r.symbols['object_palette']+4)])
# A purchase adds its mark immediately.
s=state(r);s.mode=3;s.shop_item=0;s.coins=20000;s.p.weapon=1;s.p.armor=0;put(r,s);r.run(30)
r.write('shop_difficulty',0,b'\0');r.run(8,2);r.run(20)
check('purchase marks the new weapon',state(r).p.weapon==2 and marks()==[(cells[0],cells[1])])
r.close()
report=dict(passed=True,checks=checks,armor_levels=levels,shop_cases=cases,rom_sha256=hashlib.sha256(data).hexdigest(),scope='Live CRAM against the source 1ACB armor table for all nine levels; live sprite attribute table and VRAM patterns for owned-item marks at the source 6CAF/6CB7 cells, including a controller purchase.')
(ROOT/'reports/v198-feedback-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
