"""Compile exact arcade HUD glyphs/layout into reserved Genesis tiles."""
import json,hashlib
import numpy as np
from arcade_source import Source,ROOT
from extract import decode,pack
from hud_assets import observed,color,rgb
s=Source();board=json.loads((ROOT/'assets/board.json').read_text());tx,pal,_=observed()
chars=decode(b''.join(s.files[f['path']] for f in board['regions']['chars']['files']),board['layouts']['characters'])
palette=np.frombuffer((ROOT/'res/generated/object_palette.bin').read_bytes(),'>u2').reshape(2,16).tolist()
patterns=[];lookup={};glyphs={}
slots=list(range(1012,1072))+list(range(1504,1536))+list(range(7,16))
def glyph(code,attr):
 key=(code,attr)
 if key in glyphs:return glyphs[key]
 colors=[color(pal,768+(attr&31)*4+i) for i in range(3)]
 costs=[sum(min(np.sum((rgb(c)-rgb(v))**2) for v in p[1:]) for c in colors) for p in palette]
 bank=int(np.argmin(costs))
 pens=[1+int(np.argmin([np.sum((rgb(c)-rgb(v))**2) for v in palette[bank][1:]])) for c in colors]+[0]
 if attr&31 not in (26,27):assert costs[bank]==0,(code,attr,colors)
 raw=pack(np.array(pens,dtype=np.uint8)[chars[code+((attr&224)<<3)]])
 if raw not in lookup:lookup[raw]=len(patterns);patterns.append(raw)
 assert len(patterns)<=len(slots),(len(patterns),len(slots))
 word=slots[lookup[raw]]+((bank+2)<<13)+0x8000;glyphs[key]=word;return word
mapping=[0]*896
for y in [0,1,2,3,4,25,26,27]:
 for x in range(32):
  at=(y+2)*32+x;mapping[y*32+x]=glyph(tx[at],tx[at+1024])
digits=[[glyph(n,bank) for n in range(10)]+[glyph(32,bank)] for bank in (0,7)]
vital=[glyph(c,0x20+b) for b in (9,10,11) for c in (0x80,0x81)]
def icon(ptr):
 b=s.read(6,ptr,8);return [glyph(b[i],b[i+1]) for i in range(0,8,2)]
weapons=[icon(s.word(6,0xb22c+i*2)) for i in range(5)]
armors=[icon(s.word(6,0xb25e+i*2)) for i in range(9)]
def arr(name,typ,values):return 'static const '+typ+' '+name+'[]={'+','.join(map(str,values))+'};\n'
out='/* Original source character HUD, source positions; RGB333 palette adaptation. */\n'
out+=arr('arcade_hud_patterns','u32',[f'0x{int.from_bytes(b[i:i+4],"big"):08x}' for b in patterns for i in range(0,32,4)])
out+=arr('arcade_hud_map','u16',mapping)+arr('arcade_hud_digits','u16',[v for row in digits for v in row])+arr('arcade_hud_vital','u16',vital)
out+=arr('arcade_hud_weapons','u16',[v for row in weapons for v in row])+arr('arcade_hud_armors','u16',[v for row in armors for v in row])+arr('arcade_hud_slots','u16',slots[:len(patterns)])
out+='#define ARCADE_HUD_TILES '+str(len(patterns))+'\n'
(ROOT/'src/hud_data.inc').write_text(out)
report=dict(source_set=s.lock['aggregate_sha256'],trace_sha256=hashlib.sha256((ROOT/'reference/hud_oracle_events.txt').read_bytes()).hexdigest(),glyph_tiles=len(patterns),palette=palette,scope='Original HUD glyph shapes and placement for all tiers. Source colors reduced to RGB333; armor tiers 7/8 use nearest shared-palette colors. Actor atlas is requantized to share these two palettes; backgrounds unchanged.')
(ROOT/'reference/hud_graphics.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
