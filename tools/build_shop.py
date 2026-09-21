"""Adapt observed arcade shop characters to reserved, temporary sprite VRAM."""
import json,hashlib
import numpy as np
from arcade_source import ROOT,Source
from extract import decode,pack
from hud_assets import color,rgb
s=Source();board=json.loads((ROOT/'assets/board.json').read_text())
f=next(l.split('|') for l in (ROOT/'reference/shop_screen_oracle_events.txt').read_text().splitlines() if l.startswith('SHOP|'))
ref=json.loads((ROOT/'reference/shop_screen_oracle.json').read_text())
assert ref['source_set']==s.lock['aggregate_sha256']
assert ref['trace_sha256']==hashlib.sha256((ROOT/'reference/shop_screen_oracle_events.txt').read_bytes()).hexdigest()
sp=bytes.fromhex(f[4])
assert [sp[i]|((sp[i+1]&224)<<3) for i in range(0x28,0x50,4)]==[0x11c,0x11d,0x11e,0x11f,0x118,0x119,0x11a,0x11b,0x107,0x109]
tx,p=map(bytes.fromhex,f[2:4]);chars=decode(b''.join(s.files[r['path']] for r in board['regions']['chars']['files']),board['layouts']['characters'])
pals=np.frombuffer((ROOT/'res/generated/object_palette.bin').read_bytes(),'>u2').reshape(2,16)
patterns=[];lookup={}
def glyph(code,attr):
 colors=[color(p,768+(attr&31)*4+i) for i in range(3)]
 costs=[sum(min(np.sum((rgb(c)-rgb(v))**2) for v in pal[1:]) for c in colors) for pal in pals];bank=int(np.argmin(costs))
 pens=[1+int(np.argmin([np.sum((rgb(c)-rgb(v))**2)for v in pals[bank][1:]]))for c in colors]+[1]
 raw=pack(np.array(pens,dtype=np.uint8)[chars[code+((attr&224)<<3)]])
 if raw not in lookup:lookup[raw]=len(patterns);patterns.append(raw)
 return 1088+lookup[raw]+((bank+2)<<13)+0x8000
mapping=[glyph(tx[y*32+x],tx[1024+y*32+x]) for y in range(16,27) for x in range(32)]
font=[glyph(c,0)for c in range(32,91)]
def arr(name,typ,data):return 'static const '+typ+' '+name+'[]={'+','.join(map(str,data))+'};\n'
out='/* Original arcade shop border, item cells, exit sign and lettering. */\n'
out+=arr('shop_tiles','u32',[hex(int.from_bytes(b[i:i+4],'big'))for b in patterns for i in range(0,32,4)])
out+=arr('shop_map','u16',mapping)+arr('shop_font','u16',font)
# Icons occupy the same temporary sprite VRAM, with opaque black behind them.
atlas=(ROOT/'res/generated/object_patterns.bin').read_bytes();icons=bytearray()
for code in (0x11c,0x11d,0x11e,0x11f,0x107,0x118,0x119,0x11a,0x11b,0x109):
 for v in atlas[(code+6*2048)*128:(code+6*2048+1)*128]:
  icons.append(((v>>4 or 1)<<4)|(v&15 or 1))
out+=arr('shop_icons','u32',[hex(int.from_bytes(icons[i:i+4],'big'))for i in range(0,len(icons),4)])
out+='#define SHOP_TILES '+str(len(patterns))+'\n';assert len(patterns)+40<=320
(ROOT/'src/shop_visual_data.inc').write_text(out)
(ROOT/'reference/shop_graphics.json').write_text(json.dumps(dict(tiles=len(patterns),source_set=s.lock['aggregate_sha256'],trace_sha256=hashlib.sha256((ROOT/'reference/shop_screen_oracle_events.txt').read_bytes()).hexdigest(),scope='Original panel character cells and item sprite codes; nearest existing actor palette colors.'),indent=2)+'\n')
print(len(patterns))
