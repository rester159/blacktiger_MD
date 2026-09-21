"""Compile observed arcade presentation into native tiles, palettes and events."""
import json,hashlib,struct,gzip
import numpy as np
from arcade_source import Source,ROOT
from extract import decode,pack
s=Source();board=json.loads((ROOT/'assets/board.json').read_text())
def gfx(r,l):return decode(b''.join(s.files[f['path']] for f in board['regions'][r]['files']),board['layouts'][l])
tiles=gfx('tiles','tiles');sprites=gfx('sprites','sprites');chars=gfx('chars','characters')
trace=gzip.decompress((ROOT/'reference/intro_oracle_events.txt.gz').read_bytes())
frames=[]
for line in trace.decode().splitlines():
 f=line.split('|')
 if f[0]=='SCREEN' and 708<=int(f[1])<1550:frames.append((int(f[1])-708,*map(bytes.fromhex,f[2:])))
base=next(f[1] for f in frames if f[0]==42)
patterns=[];tilelookup={}
def tile(pix):
 raw=pack(pix)
 if raw not in tilelookup:tilelookup[raw]=len(patterns);patterns.append(raw)
 return 16+tilelookup[raw]
mapping=[]
for y in range(28):
 for x in range(32):
  sy=y+2;at=((sy//2)*16+x//2)*2;code,attr=base[at:at+2];assert (attr>>3)&15==1
  pix=tiles[code|((attr&7)<<8)]
  if attr&128:pix=pix[:,::-1]
  mapping.append(tile((pix[(sy%2)*8:(sy%2+1)*8,(x%2)*8:(x%2+1)*8]+1)&15))
assert len(patterns)<624
font=[];fontlookup={};spritepatterns=[];spritelookup={};blocks=[];blocklookup={};palettes=[];pallookup={};events=[];textwrites=[]
def wordcolor(p,i):return ((p[i]>>5)<<1)|(((p[i]&15)>>1)<<5)|(((p[i+1024]&15)>>1)<<9)
previous_tx=[0]*896;previous_sp=None;previous_pal=None
for tick,bg,tx,pal,sp in frames:
 # Palette 0 palace, 1 dragons, 2 source text palette 0, 3 source text palette 7.
 p=[wordcolor(pal,16+15)]+[wordcolor(pal,16+i) for i in range(15)]
 p += [0]+[wordcolor(pal,512+7*16+i) for i in range(15)]
 p += [0]+[wordcolor(pal,768+bank*4+i) for bank in (0,7,24) for i in range(3)]+[0]*22
 p=tuple(p)
 if p!=previous_pal:
  if p not in pallookup:pallookup[p]=len(palettes);palettes.append(p)
  events.append((tick,0,pallookup[p]));previous_pal=p
 block=[]
 for i in range(0,512,4):
  code=sp[i]|((sp[i+1]&224)<<3);attr=sp[i+1];x=sp[i+3]-((attr&16)<<4);y=sp[i+2]-16
  if not(-15<=x<256 and -15<=y<224):continue
  pix=sprites[code]
  if np.all(pix==15):continue
  assert attr&7==7,(tick,code,attr)
  if code not in spritelookup:
   spritelookup[code]=len(spritepatterns)//4
   pix=(pix+1)&15
   for xx in (0,8):
    for yy in (0,8):spritepatterns.append(pack(pix[yy:yy+8,xx:xx+8]))
  block.append((x,y,spritelookup[code],int(bool(attr&8))))
 # Arcade draws from the end; low SAT indices are in front on Genesis too.
 block=tuple(block);assert len(block)<=64
 if block!=previous_sp:
  if block not in blocklookup:blocklookup[block]=len(blocks);blocks.append(block)
  events.append((tick,1,blocklookup[block]));previous_sp=block
 for cell in range(896):
  sourcecell=cell+64;attr=tx[sourcecell+1024];code=tx[sourcecell]+((attr&224)<<3)
  bank=attr&31;assert bank in (0,7,24)
  pix=chars[code];raw=pack(np.where(pix==3,0,pix+1+(0,7,24).index(bank)*3).astype(np.uint8))
  if raw not in fontlookup:fontlookup[raw]=len(font);font.append(raw)
  value=640+fontlookup[raw]+(2<<13)+0x8000
  if value!=previous_tx[cell]:
   textwrites.append((cell,value));events.append((tick,2,len(textwrites)-1));previous_tx[cell]=value
assert len(font)<384
# Group initial text writes into one map upload; later events remain sparse.
initial=[v for cell,v in textwrites[:896]];assert [c for c,v in textwrites[:896]]==list(range(896))
events=[e for e in events if not(e[1]==2 and e[2]<896)]
def arr(name,typ,rows):return 'static const '+typ+' '+name+'[]={'+','.join(rows)+'};\n'
def u16s(name,values):return arr(name,'u16',map(str,values))
def binary(name,data):return arr(name,'u32',[f'0x{int.from_bytes(data[i:i+4],"big"):08x}' for i in range(0,len(data),4)])
out='/* Native intro presentation data; no original instructions. */\n'
out+=binary('intro_bg',b''.join(patterns))+u16s('intro_map',mapping)+binary('intro_font',b''.join(font))+u16s('intro_text',initial)
out+=binary('intro_sprites',b''.join(spritepatterns))+u16s('intro_palettes',[v for p in palettes for v in p])
offsets=[];bodies=[]
for block in blocks:
 offsets.append(len(bodies));bodies.append(len(block))
 for x,y,index,flip in block:bodies.extend([x&65535,y&65535,index,flip])
out+=u16s('intro_blocks',bodies)+u16s('intro_offsets',offsets)
out+=arr('intro_writes','IntroWrite',['{'+','.join(map(str,e))+'}' for e in textwrites])
out+=arr('intro_events','IntroEvent',['{'+','.join(map(str,e))+'}' for e in events])
out+=f'#define INTRO_BG_TILES {len(patterns)}\n#define INTRO_FONT_TILES {len(font)}\n#define INTRO_EVENTS {len(events)}\n#define INTRO_DURATION {len(frames)}\n'
(ROOT/'src/intro_data.inc').write_text(out)
report=dict(source_set=s.lock['aggregate_sha256'],trace_sha256=hashlib.sha256(trace).hexdigest(),frames=len(frames),background_tiles=len(patterns),font_tiles=len(font),sprite_tiles=len(spritepatterns),sprite_blocks=len(blocks),palette_states=len(palettes),events=len(events),scope='Native timed presentation of original palace, dragon animation, palette flashes/fades and character writes; RGB333 adaptation; original start music command 0x30. No original CPU code in cartridge.')
(ROOT/'reference/intro_graphics.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
