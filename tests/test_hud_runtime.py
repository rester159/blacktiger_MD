"""Compare actual HUD VRAM glyphs/colors to original arcade character ROM and writes."""
import json,hashlib,ctypes as C
import numpy as np
from test_runtime import ROOT,Runner,state,put
from arcade_source import Source
from extract import decode
from hud_assets import observed,color,rgb as channels
src=Source();board=json.loads((ROOT/'assets/board.json').read_text());tx,pal,_=observed()
chars=decode(b''.join(src.files[f['path']] for f in board['regions']['chars']['files']),board['layouts']['characters'])
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
vram=(C.c_uint8*65536).in_dll(r.lib,'vram');cram=(C.c_uint16*64).in_dll(r.lib,'cram')
def word(a):return vram[a^1]*256+vram[(a+1)^1]
def glyph(x,y,code,attr):
 w=word(0xc000+y*128+x*2);tile=w&2047;bank=(w>>13)&3
 raw=bytes(vram[(tile*32+i)^1] for i in range(32));actual=np.array([n for b in raw for n in (b>>4,b&15)]).reshape(8,8)
 expected=chars[code+((attr&224)<<3)]
 assert np.array_equal(actual==0,expected==3),(x,y,code,attr,'shape/transparency')
 colors=[color(pal,768+(attr&31)*4+i) for i in range(3)]
 banks=np.frombuffer((ROOT/"res/generated/object_palette.bin").read_bytes(),">u2").reshape(2,16)
 available=[[i for i in range(1,16) if i not in (7,8,9,10)],list(range(1,16))]
 costs=[sum(min(sum((channels(c)-channels(banks[b][i]))**2) for i in available[b]) for c in colors) for b in range(2)]
 assert bank==2+int(np.argmin(costs))
 for pen in range(3):
  at=768+(attr&31)*4+pen;rgb=(pal[at]>>5)|(((pal[at]&15)>>1)<<3)|(((pal[1024+at]&15)>>1)<<6)
  values=set(int(cram[bank*16+v]) for v in actual[expected==pen])
  best=banks[bank-2][available[bank-2][int(np.argmin([sum((channels(colors[pen])-channels(banks[bank-2][i]))**2) for i in available[bank-2]]))]]
  expected_rgb=((int(best)>>1)&7)|(((int(best)>>5)&7)<<3)|(((int(best)>>9)&7)<<6)
  assert not values or values=={expected_rgb},(x,y,code,attr,"color",values,expected_rgb)
def icon(x,y,ptr):
 b=src.read(6,ptr,8)
 for i in range(4):glyph(x+i%2,y+i//2,b[i*2],b[i*2+1])
def digits(x,y,value,n,style=0,spaces=False):
 text=str(value%10**n).rjust(n,' ' if spaces else '0')
 for i,c in enumerate(text):glyph(x+i,y,32 if c==' ' else int(c),style)
for armor in range(9):
 hp=armor%6;weapon=armor%5+1
 s=state(r);s.mode=2;s.p.hp=hp;s.p.armor=armor;s.p.weapon=weapon;s.coins=12345;s.score=8765432;s.time=199;put(r,s)
 r.write('container_keys',0,bytes([armor]));r.write('shop_antidotes',0,b'\x02');r.run(12)
 for y in (0,2):
  for x in range(32):
   at=(y+2)*32+x;glyph(x,y,tx[at],tx[at+1024])
 digits(2,1,8765432,7,7,True);digits(13,1,8765432,7,7,True)
 digits(1,3,3,1);digits(3,3,19,2);digits(26,4,12345,5)
 for i in range(hp):
  for j in range(2):glyph(7+i*2+j,3,0x80+j,0x29+min(i,2))
 for x in range(7+hp*2,17):assert word(0xc000+3*128+x*2)==0
 icon(24,3,0xb20c);icon(7,25,0xb214);icon(19,25,0xb21c)
 icon(11,25,src.word(6,0xb22c+(weapon-1)*2));icon(15,25,src.word(6,0xb25e+armor*2))
 digits(7,27,armor,2);digits(19,27,2,2)
r.capture('hud-inventory.png');r.close()
report=dict(passed=True,cases=9,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Live BG_A VRAM: original character-ROM shapes, transparent pixels, positions and nearest actor-palette RGB333 colors for labels, score/high score, timer, Zenny, vitality, keys, antidotes and all weapon/armor tiers. Actor palettes retain their pre-HUD allocation.')
(ROOT/'reports/hud-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
