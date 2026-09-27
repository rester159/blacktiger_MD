"""Convert original attract presentation into native tiles and sparse display events.
No source CPU instructions or emulator are included in the cartridge.
"""
import gzip,json,struct,hashlib
from collections import Counter
import numpy as np
from arcade_source import ROOT,Source
from extract import decode,pack,rgb,quant,colid
from attract_codec import pack as compress,unpack
s=Source();board=json.loads((ROOT/'assets/board.json').read_text())
def gfx(r,l):return decode(b''.join(s.files[f['path']] for f in board['regions'][r]['files']),board['layouts'][l])
bg_gfx=gfx('tiles','tiles');fg_gfx=gfx('chars','characters')
path=ROOT/'reference/attract_oracle_frames.bin.gz'
raw=gzip.decompress(path.read_bytes())
assert len(raw)==5100*5126
# Task 0B21 advances E080 at 151, 993, 4186; 1324 starts the demo at 1414.
# Preserve the first complete odd/even title + gameplay pair, including blanks.
frames=[raw[i*5126:(i+1)*5126] for i in range(150,4185)]
credit=raw[4899*5126:4900*5126]
allframes=frames+[credit]
keys=[{},{}];hists=[np.zeros(512,dtype=np.int64),np.zeros(512,dtype=np.int64)]
def palette(frame):
 p=np.frombuffer(frame[2566:4614],np.uint8).astype(np.uint16)
 return ((p[:1024]>>5)<<1)|(((p[:1024]&15)>>1)<<5)|(((p[1024:]&15)>>1)<<9)
def key_bg(w,p):
 code=(w&255)|((w>>8&7)<<8);bank=w>>11&15
 return code,bool(w&0x8000),tuple(map(int,p[bank*16:bank*16+16]))
def key_fg(code,attr,p):
 return code|((attr&224)<<3),tuple(map(int,p[768+(attr&31)*4:772+(attr&31)*4]))
def pixels(kind,key):
 if kind==0:
  code,flip,p=key;a=bg_gfx[code];a=a[:,::-1] if flip else a
  return np.array(p,dtype=np.uint16)[a],np.ones((16,16),bool)
 code,p=key;a=fg_gfx[code];return np.array(p,dtype=np.uint16)[a],a!=3
for f in allframes:
 p=palette(f)
 if not f[5]&2:
  for (w,) in struct.iter_unpack('<H',f[8:518]):keys[0][key_bg(w,p)]=None
 if not f[4]&128:
  for code,attr in zip(f[582:1478],f[1606:2502]):keys[1][key_fg(code,attr,p)]=None
# Include dynamic scores/initials in the same source text palettes.
for f in (frames[149],credit):
 p=palette(f)
 for a in (0,7,24):
  for c in list(range(10))+list(range(32,91)):keys[1][key_fg(c,a,p)]=None
for kind in (0,1):
 for key in keys[kind]:
  pix,mask=pixels(kind,key)
  counts=Counter(map(int,pix[mask].flat))
  for w,n in counts.items():hists[kind][colid(w)]+=n
centers=[quant(hist) for hist in hists]
colors=[[0]+[int(c[0]*2+c[1]*32+c[2]*512) for c in cc] for cc in centers]
patterns=[bytes(32)];lookup={bytes(32):0};quads=[(0,0,0,0)];qlookup={quads[0]:0}
def tile(pix,mask,preferred):
 source=np.stack([((pix>>1)&7),((pix>>5)&7),((pix>>9)&7)],axis=2).astype(np.int32)
 candidates=[]
 for bank in (0,1):
  d=((source[:,:,None,:]-centers[bank])**2).sum(3)
  ix=d.argmin(2);error=d.min(2)[mask].sum()
  candidates.append((error,bank!=preferred,bank,ix))
 _,_,bank,ix=min(candidates,key=lambda a:a[:2]);indices=np.where(mask,ix+1,0).astype(np.uint8)
 b=pack(indices)
 if b not in lookup:lookup[b]=len(patterns);patterns.append(b)
 return 16+lookup[b]|(bank<<13)
for kind in (0,1):
 for key in keys[kind]:
  pix,mask=pixels(kind,key)
  if kind==0:
   q=tuple(tile(pix[y:y+8,x:x+8],mask[y:y+8,x:x+8],0) for y in (0,8) for x in (0,8))
   if q not in qlookup:qlookup[q]=len(quads);quads.append(q)
   keys[kind][key]=qlookup[q]
  else:keys[kind][key]=tile(pix,mask,1)|0x8000
print('patterns',len(patterns),'quads',len(quads),flush=True)
assert len(patterns)+16<=1280,('attract exceeds terrain VRAM',len(patterns))
# State: scroll x/y, rank flag, sprite enable, 512 background metatiles,
# 896 text words, 512 sprite bytes. Display pixels retain arcade positions.
SIZE=6+1024+1792+512
BG=6;FG=1030;SP=2822
state=bytearray(SIZE);streams=[];sizes=[];initials=[]
def word(buf,at,v):buf[at:at+2]=struct.pack('>H',v)
def frame_state(f,previous):
 st=bytearray(previous);sx,sy=struct.unpack('<HH',f[:4]);p=palette(f)
 word(st,0,sx&511);word(st,2,(sy+16)&255)
 st[4]=int(f[582+14*32+9:582+14*32+16]==b'RANKING');st[5]=not bool(f[5]&4)
 if f[5]&2:st[BG:FG]=bytes(1024)
 else:
  for y in range(15):
   for x in range(17):
    w=int.from_bytes(f[8+(y*17+x)*2:10+(y*17+x)*2],'little')
    cell=(((sy+16)//16+y)&15)*32+((sx//16+x)&31)
    word(st,BG+cell*2,keys[0][key_bg(w,p)])
 for i,(code,attr) in enumerate(zip(f[582:1478],f[1606:2502])):
  word(st,FG+i*2,0 if f[4]&128 else keys[1][key_fg(code,attr,p)])
 st[SP:]=f[4614:5126] if st[5] else bytes(512)
 return st
for sequence in (frames,[credit]):
 prev=bytearray(SIZE);events=bytearray()
 for index,f in enumerate(sequence):
  st=frame_state(f,prev)
  if index==0:initials.append(bytes(st));prev=st;continue
  delta=bytes((a-b)&255 for a,b in zip(st,prev));i=0
  while i<SIZE:
   if not delta[i]:i+=1;continue
   start=i;i+=1
   while i<SIZE and i-start<255 and delta[i]:i+=1
   events+=struct.pack('>HB',start,i-start)+delta[start:i]
  events+=b'\xff\xff';prev=st
 packed=compress(events);assert unpack(packed,len(events))==events
 streams.append(packed);sizes.append(len(events))
 print('stream',len(sequence),len(events),len(packed),flush=True)
def arr(name,typ,values):return f'static const {typ} {name}[]={{'+','.join(map(str,values))+'};\n'
def binary(name,data):return arr(name,'u8',data)
out='/* Generated from owner-supplied original-ROM attract observation. */\n'
out+=arr('attract_patterns','u32',[int.from_bytes(p[i:i+4],'big') for p in patterns for i in range(0,32,4)])
out+=arr('attract_palette','u16',[w for p in colors for w in p])
out+=arr('attract_quads','u16',[w for q in quads for w in q])
out+=binary('attract_stream',streams[0])+binary('attract_initial',initials[0])+binary('attract_credit_state',initials[1])
# Source palette 0 red/white header and ranking color 7; reusable name/digit glyphs.
f=frames[149];p=palette(f)
for a in (0,7,24):out+=arr('attract_chars'+str(a),'u16',[keys[1][key_fg(c-48 if 48<=c<=57 else c,a,p)] for c in range(32,91)])
out+=f'#define ATTRACT_PATTERN_COUNT {len(patterns)}\n#define ATTRACT_FRAMES {len(frames)}\n#define ATTRACT_STATE_SIZE {SIZE}\n'
(ROOT/'src/attract_data.inc').write_text(out)
report=dict(frames=len(frames),source_frames=[151,4185],credit_frame=4900,source_set=s.lock['aggregate_sha256'],trace_sha256=hashlib.sha256(raw).hexdigest(),patterns=len(patterns),quads=len(quads),packed_bytes=sum(map(len,streams)),event_bytes=sizes,scope='Original display-state replay: source timing, scroll, title/ranking/insert-coin writes and sprite movement. Native tiles/sprites with Mega Drive palette and sprite-limit adaptations. Saved records overlay source score cells; no simulated game state or score writes.')
(ROOT/'reference/attract_graphics.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
