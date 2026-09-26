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
# Arcade selection outline: six overlapping sprite pieces, not the title Yashichi.
sprite_art=decode(b''.join(s.files[r['path']] for r in board['regions']['sprites']['files']),board['layouts']['sprites'])
cursor_colors=[color(p,528+i) for i in range(15)]
cursor_pens=np.array([1+int(np.argmin([np.sum((rgb(c)-rgb(v))**2) for v in pals[1][1:]])) for c in cursor_colors]+[0],np.uint8)
cursor=b''.join(pack(cursor_pens[sprite_art[code]][y:y+8,x:x+8]) for code in (0x148,0x149,0x14a,0x150,0x151,0x152) for x,y in ((0,0),(0,8),(8,0),(8,8)))
out+=arr('shop_cursor_tiles','u32',[hex(int.from_bytes(cursor[i:i+4],'big')) for i in range(0,len(cursor),4)])
out+=arr('shop_cursor_positions','u8',s.read(None,0x6e45,48))
out+='#define SHOP_TILES '+str(len(patterns))+'\n';assert len(patterns)+40<=320
(ROOT/'src/shop_visual_data.inc').write_text(out)
(ROOT/'reference/shop_graphics.json').write_text(json.dumps(dict(tiles=len(patterns),source_set=s.lock['aggregate_sha256'],trace_sha256=hashlib.sha256((ROOT/'reference/shop_screen_oracle_events.txt').read_bytes()).hexdigest(),scope='Original panel character cells and item sprite codes; nearest existing actor palette colors.'),indent=2)+'\n')
print(len(patterns))
# The seated merchant is background artwork at the original shop camera,
# not the small rescued NPC sprite. Decode the original Level 1 room.
from extract import quant,colid,COL
shop_x,shop_y=__import__('struct').unpack('<HH',s.read(None,0x69e3,4))
mem=bytearray(2048);ptr=s.word(6,0x8136)
for _ in range(20):
 start,dest,count=__import__('struct').unpack('<HHH',s.read(6,ptr,6))
 if start==65535:break
 mem[dest-0xd800:dest-0xd800+count]=s.read(6,start,count);ptr+=6
source_colors=np.array([((mem[i]>>5),(mem[i]&15)>>1,(mem[i+1024]&15)>>1) for i in range(256)])
bg=decode(b''.join(s.files[r['path']] for r in board['regions']['tiles']['files']),board['layouts']['tiles'])
source_map=s.read(8,0x8000,16384);canvas=np.zeros((224,256),np.uint16)
for yy in range(14):
 for xx in range(16):
  x=shop_x//16+xx;y=shop_y//16+yy+1 # Arcade visible area begins at scanline 16.
  at=(x&15)|((y&15)<<4)|((x&0x70)<<4)|((y&0x30)<<7)
  low,attr=source_map[at*2:at*2+2];tile=bg[low+((attr&7)<<8)]
  if attr&128:tile=tile[:,::-1]
  canvas[yy*16:yy*16+16,xx*16:xx*16+16]=tile+((attr>>3)&15)*16
hist=np.zeros((16,512),np.int64)
for pen,n in enumerate(np.bincount(canvas.reshape(-1),minlength=256)):
 c=source_colors[pen];hist[pen//16,int(c[0]+c[1]*8+c[2]*64)]+=n
groups=np.arange(16)%2
for _ in range(5):
 banks=[quant(hist[groups==g].sum(0) if hist[groups==g].any() else hist.sum(0)) for g in range(2)]
 costs=np.array([((COL[:,None,:]-bank[None,:,:])**2).sum(2).min(1) for bank in banks])
 groups=(hist@costs.T).argmin(1)
banks=[np.vstack(([0,0,0],quant(hist[groups==g].sum(0) if hist[groups==g].any() else hist.sum(0)))) for g in range(2)]
back_tiles=[];back_lookup={};back_map=[];preview=np.zeros((224,256,3),np.uint8)
for y in range(0,224,8):
 for x in range(0,256,8):
  target=source_colors[canvas[y:y+8,x:x+8]];choices=[]
  for bank,pal in enumerate(banks):
   d=((target[:,:,None,:]-pal[None,None,1:,:])**2).sum(3);pens=d.argmin(2)+1
   choices.append((int(d.min(2).sum()),bank,pens))
  _,bank,pens=min(choices,key=lambda v:v[0]);raw=pack(pens)
  if raw not in back_lookup:back_lookup[raw]=len(back_tiles);back_tiles.append(raw)
  back_map.append(16+back_lookup[raw]+(bank<<13));preview[y:y+8,x:x+8]=banks[bank][pens]*255//7
assert len(back_tiles)<996
out+=arr('shop_backdrop_palette','u16',[int(c[0]*2+c[1]*32+c[2]*512) for bank in banks for c in bank])
out+=arr('shop_backdrop_map','u16',back_map)
out+=arr('shop_backdrop_tiles','u32',[hex(int.from_bytes(b[i:i+4],'big')) for b in back_tiles for i in range(0,32,4)])
out+='#define SHOP_BACKDROP_TILES '+str(len(back_tiles))+'\n'
(ROOT/'src/shop_visual_data.inc').write_text(out)
from PIL import Image
Image.fromarray(preview).save(ROOT/'reports/shop-backdrop-native.png')
Image.fromarray((source_colors[canvas]*255//7).astype(np.uint8)).save(ROOT/'reports/shop-backdrop-arcade.png')
ref=json.loads((ROOT/'reference/shop_graphics.json').read_text());ref.update(backdrop_tiles=len(back_tiles),shop_camera=[shop_x,shop_y],visible_y_offset=16,scope='Original panel and icons plus seated merchant room decoded from original Level 1 shop camera/map, with two native background palettes.')
(ROOT/'reference/shop_graphics.json').write_text(json.dumps(ref,indent=2)+'\n')
