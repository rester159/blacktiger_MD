"""Export only the compiled parallax tiles, horizontally repeated as in play."""
import re
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
rom=(ROOT/'out/release/rom.bin').read_bytes()
symbols={v[2]:int(v[0],16) for line in (ROOT/'out/release/symbol.txt').read_text().splitlines() if len(v:=line.split())>=3}
for k,v in list(symbols.items()):
 if '.lto_priv.' in k:symbols.setdefault(k.split('.lto_priv.')[0],v)
shots=[]
levels=(3,4,6,7)
for level in levels:
 width=16 if level==7 else 64
 name='arena_far' if level==7 else f'backdrop_{level}_map'
 at=symbols[name];words=np.frombuffer(rom[at:at+width*20*2],dtype='>u2').reshape(20,width)
 base=884 if level==7 else 656 if level==3 else 700
 at=symbols['arena_far_patterns' if level==7 else f'backdrop_{level}_far']
 palette=np.fromfile(ROOT/f'res/generated/pal{level}.bin',dtype='>u2')
 rgb=np.array([[int(c)>>s&7 for s in (1,5,9)] for c in palette],dtype=np.uint16)*255//7
 pixels=np.zeros((160,width*8,3),np.uint8)
 for y in range(20):
  for x in range(width):
   word=int(words[y,x]);start=at+((word&2047)-base)*32
   raw=np.frombuffer(rom[start:start+32],np.uint8)
   tile=np.stack((raw>>4,raw&15),axis=1).reshape(8,8)
   if word&0x800:tile=tile[:,::-1]
   if word&0x1000:tile=tile[::-1]
   pixels[y*8:y*8+8,x*8:x*8+8]=rgb[tile+((word>>13)&1)*16]
 if level==7:
  assert np.all(pixels[:,:,0]<=pixels[:,:,2]),'Warm foreground fragments remain in palace backdrop'
 tiled=np.tile(pixels,(1,1024//pixels.shape[1],1))
 shot=Image.fromarray(tiled);shot.save(ROOT/f'reports/parallax-only-level{level+1}-v26.png');shots.append(shot)
sheet=Image.new('RGB',(1024,len(shots)*184),(14,14,18));d=ImageDraw.Draw(sheet)
for i,shot in enumerate(shots):
 y=i*184;d.text((6,y+5),f'LEVEL {levels[i]+1} - PARALLAX ONLY',fill='white');sheet.paste(shot,(0,y+24))
sheet.save(ROOT/'reports/parallax-only-v26.png')
print('Exported native far-plane tiles only: levels 4, 5, 7, 8, horizontally repeated.')
