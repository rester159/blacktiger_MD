"""Compile original ending observations into typed native presentation events."""
import hashlib,json
import numpy as np
from arcade_source import ROOT

def generate(source,emit,decode,pack,words,round_colors,groups,pen_map,world_raw):
 ref=json.loads((ROOT/'reference/ending_oracle.json').read_text())
 assert ref['source_set']==source.lock['aggregate_sha256']
 for key,path in [('trace_sha256','reference/ending_oracle_events.txt'),('lua_sha256','tools/ending_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
 board=json.loads((ROOT/'assets/board.json').read_text())
 def graphics(region,layout):return decode(b''.join(source.files[f['path']] for f in board['regions'][region]['files']),board['layouts'][layout])
 tiles=graphics('tiles','tiles');chars=graphics('chars','characters');events=[];palettes=[];used={32};scene=None
 for line in (ROOT/'reference/ending_oracle_events.txt').read_text().splitlines():
  f=line.split('|');kind=f[0]
  if kind in ('WAIT','COMPLETE'):continue
  tick=int(f[1])
  if kind=='TEXT':
   cell=int(f[2])-64;char=int(f[3]);assert 0<=cell<896;used.add(char);events.append([tick,cell,char,0])
  elif kind=='CLEAR':events.append([tick,0,0,1])
  elif kind=='PALETTE':events.append([tick,0,len(palettes),2]);palettes.append(bytes.fromhex(f[2]))
  elif kind=='HIDE':events.append([tick,0,2,3])
  elif kind=='SCENE':scene=(bytes.fromhex(f[2]),bytes.fromhex(f[3]));events.append([tick,0,1,3])
  elif kind=='END':events.append([tick,0,0,4])
 assert scene and len(palettes)==10 and ref['ticks']==events[-1][0]
 source.expect(None,0x7ca9,'cd2403');source.expect(None,0x7c4b,'cd0403');source.expect(None,0x7c63,'cd1c03');source.expect(None,0x7c52,'cd2403');source.expect(None,0x7cf0,'cd2803')
 source.expect(None,0x20c7,'3aa1f3fe08caad21')
 assert scene[0]==source.read(4,source.word(4,0x924a),512)
 # Remap palette changes through the existing quantized round-eight pens.
 # Weight each native pen by the source colors that contribute pixels to it.
 weights=np.zeros((32,256),dtype=np.int64)
 for at in range(0,len(world_raw),2):
  code,attr=world_raw[at:at+2];pal=(attr>>3)&15
  freq=np.bincount(tiles[code|((attr&7)<<8)].flatten(),minlength=16)
  for pen,count in enumerate(freq):weights[int(groups[pal])*16+pen_map[pal][pen],pal*16+pen]+=int(count)
 def rgb(w):return np.array([(w>>1)&7,(w>>5)&7,(w>>9)&7])
 def color(lo,hi):return ((lo>>5)<<1)|(((lo&15)>>1)<<5)|(((hi&15)>>1)<<9)
 adapted=[]
 for index,p in enumerate(palettes):
  if index<6:assert p==source.read(1,0xb57a+index*192,192)
  colors=list(round_colors[:256])
  for i in range(96):colors[96+i]=color(p[i],p[96+i])
  target=np.array([rgb(w) for w in colors]);out=[]
  for row in weights:
   c=np.rint(row@target/row.sum()).astype(int) if row.sum() else np.zeros(3,dtype=int)
   out.append(int(c[0]*2+c[1]*32+c[2]*512))
  adapted.append(out)
 emit('ending_fades',words([w for row in adapted for w in row]))
 bg,p=scene;colors=[color(p[i],p[1024+i]) for i in range(1024)]
 palette=[0]+colors[96:111]+[0]+colors[112:127]
 emit('ending_palette',words(palette));emit('ending_text_palette',words([0]+colors[796:799]))
 unique={bytes(32):0};patterns=bytearray(32);mapping=[]
 for y in range(28):
  sy=y+2
  for x in range(32):
   at=((sy//2)*16+x//2)*2;code,attr=bg[at:at+2];pal=(attr>>3)&15;assert pal in (6,7)
   pix=tiles[code|((attr&7)<<8)]
   if attr&128:pix=pix[:,::-1]
   raw=pack((pix[(sy%2)*8:(sy%2+1)*8,(x%2)*8:(x%2+1)*8]+1)&15)
   if raw not in unique:unique[raw]=len(unique);patterns.extend(raw)
   mapping.append(16+unique[raw]+((pal-6)<<13))
 emit('ending_patterns',bytes(patterns),'u32');emit('ending_map',words(mapping))
 font=bytearray();glyphs=[0]*256;dedup={}
 for char in sorted(used):
  raw=pack(np.where(chars[char]==3,0,chars[char]+1).astype(np.uint8))
  if raw not in dedup:dedup[raw]=len(dedup);font.extend(raw)
  slot=dedup[raw];glyphs[char]=(1408+slot if slot<32 else 1072+slot-32)|(3<<13)
 assert len(dedup)<=48 and len(unique)<=1056
 emit('ending_font',bytes(font),'u32');emit('ending_glyphs',words(glyphs))
 (ROOT/'src/ending_timeline.inc').write_text('/* Typed source presentation events, not arcade instructions. */\nstatic const EndingEvent ending_events[]={'+','.join('{'+','.join(map(str,row))+'}' for row in events)+'};\n#define ENDING_EVENTS '+str(len(events))+'\n')
 (ROOT/'src/ending_visual_data.inc').write_text('#define ENDING_TILES '+str(len(unique))+'\n#define ENDING_FONT_TILES '+str(len(dedup))+'\n')
 report=dict(source_set=ref['source_set'],ticks=ref['ticks'],events=len(events),palette_steps=len(palettes),background_tiles=len(unique),font_tiles=len(dedup),characters=sorted(used),scope='Typed character/clear/palette/scene/end events. Initial terrain palette changes are weighted adaptations through existing round-eight quantized pens; credits backdrop and glyphs retain RGB333 colors. Scheduling and final hero sprite retention need whole-board comparison.')
 (ROOT/'reference/ending.json').write_text(json.dumps(report,indent=2)+'\n');return report
