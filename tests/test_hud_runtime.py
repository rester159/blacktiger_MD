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
 available=[[i for i in range(1,16) if i not in (2,3,4,5,7,8,9,10)],list(range(1,16))]
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
 hp=armor%6;weapon=armor%5+1;max_hp=min(5,hp+armor%3)
 s=state(r);s.mode=2;s.p.hp=hp;s.p.armor=armor;s.p.weapon=weapon;s.coins=12345;s.score=8765432;s.time=199;put(r,s)
 r.write('container_keys',0,bytes([armor]));r.write('shop_antidotes',0,b'\x02');r.write('progress_max_hp',0,bytes([max_hp]));r.run(12)
 for y in (0,2):
  for x in range(32):
   at=(y+2)*32+x;glyph(x,y,tx[at],tx[at+1024])
 digits(0,1,87654320,9,7,True);digits(11,1,87654320,9,7,True)
 digits(1,3,3,1);digits(3,3,19,2);digits(26,4,12345,5)
 # Fixed 2620/B878 slot colors; MAME-observed F40E<F3B6 slots switch to empty 82/83 glyphs.
 for i in range(max_hp):
  for j in range(2):glyph(7+i*2+j,3,(0x80 if i<hp else 0x82)+j,0x29+min(i,2))
 for x in range(7+max_hp*2,17):assert word(0xc000+3*128+x*2)==0
 icon(24,3,0xb20c);icon(7,25,0xb214);icon(19,25,0xb21c)
 icon(11,25,src.word(6,0xb22c+(weapon-1)*2));icon(15,25,src.word(6,0xb25e+armor*2))
 digits(7,27,armor,2);digits(19,27,2,2)
r.capture('hud-inventory.png')
# Expected strings come from executing fixed 054F/0568 in the arcade ROM.
score_cases=0
for line in (ROOT/'reference/score_npc_oracle_events.txt').read_text().splitlines():
 if not line.startswith('SCORE|'):continue
 _,stored,expected=line.split('|');s=state(r);s.score=int(stored);put(r,s);r.run(12)
 for i,c in enumerate(expected):glyph(i,1,32 if c==' ' else int(c),7)
 assert state(r).score==int(stored),'Display conversion changed stored score'
 score_cases+=1
r.capture('v197-score-nine-digits.png');r.close()
report=dict(passed=True,cases=9,empty_vitality_cases=sum(1 for a in range(9) if min(5,a%6+a%3)>a%6),source_score_cases=score_cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Live BG_A VRAM: original character-ROM shapes, transparent pixels, positions and nearest actor-palette RGB333 colors for labels, score/high score, timer, Zenny, vitality, keys, antidotes and all weapon/armor tiers. Actor palettes retain their pre-HUD allocation.')
(ROOT/'reports/hud-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
