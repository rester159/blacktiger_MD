"""Split source cave/sky/window artwork without modifying terrain or collision."""
import json
import numpy as np
from PIL import Image
from arcade_source import ROOT
from extract import pack

def array(name,typ,v):return f'static const {typ} {name}[]={{'+','.join(map(str,v))+'};\n'
def patterns(name,data):return array(name,'u32',[hex(int.from_bytes(b[i:i+4],'big')) for b in data for i in range(0,32,4)])
output='/* Generated from original level artwork by tools/build_backdrops.py. */\n';reports=[]
for level in (3,5,6):
 raw=(ROOT/f'res/generated/bg{level}.bin').read_bytes();rawtiles=[raw[i:i+32] for i in range(0,len(raw),32)];n=len(rawtiles)
 a=np.frombuffer(raw,dtype=np.uint8);tiles=np.stack((a>>4,a&15),1).reshape(-1,8,8)
 wm=np.fromfile(ROOT/f'res/generated/map{level}.bin',dtype='>u2').reshape(128,256)
 palette=np.fromfile(ROOT/f'res/generated/pal{level}.bin',dtype='>u2')
 rgb=np.array([[(int(c)>>s)&7 for s in (1,5,9)] for c in palette],dtype=np.int32)
 canvas=np.zeros((1024,2048),np.uint8)
 for y in range(128):
  for x in range(256):
   word=int(wm[y,x]);t=tiles[(word&2047)-16]
   if word&0x800:t=t[:,::-1]
   if word&0x1000:t=t[::-1]
   canvas[y*8:y*8+8,x*8:x*8+8]=t+((word>>13)&1)*16
 window_words=set()
 if level==6:
  for x,y,w,h in [(96,384,64,112),(192,384,64,112),(288,384,64,112),(400,384,64,112),(912,352,64,112),(1008,352,64,112),(1696,256,64,112),(1840,256,64,112),(1616,0,64,112),(1152,520,64,200),(96,768,64,112),(272,768,64,112),(896,768,64,192),(992,832,64,48)]:
   for word in wm[y//8:(y+h)//8,x//8:(x+w)//8].flat:
    bank=(int(word)>>13)&1;tile=tiles[(int(word)&2047)-16];used=set((tile+bank*16).flat)
    window_words.add((bank,int(word)&2047))
 extra=[];lookup={b:i for i,b in enumerate(rawtiles)};remaps=[]
 for bank in range(2):
  remap=list(range(16))
  for i,tile in enumerate(tiles):
   indexed=tile+bank*16;changed=tile.copy()
   if level==3:
    changed[np.isin(indexed,[4,7,10,14,20])]=0
    if not rgb[indexed].any():changed[:]=1 # retain black in the other cave chambers
   elif level==5:
    changed[np.isin(indexed,[3,19])]=0
    # Blue scenery is distinct from warm terrain. Keep white spike strokes.
    used=set(indexed.flat)
    if used<={0,1,3,6,12,15,16,17,19,21,23,26}:
     changed[:]=0
   else:
    if (bank,i+16) in window_words or not rgb[indexed].any():changed[:]=0
   b=pack(changed)
   if b not in lookup:lookup[b]=n+len(extra);extra.append(b)
   remap.append(16+lookup[b])
  remaps.append(remap)
 assert n+len(extra)<=1800,(level,n,len(extra))
 # Repeatable, independent background constructed exclusively from source art.
 far=np.zeros((160,512),np.uint8)
 if level==3:
  patch=canvas[784:912,160:288].copy();patch=np.concatenate((patch,patch[:,::-1]),1);patch=np.concatenate((patch,patch[::-1]),0)
  far=np.tile(patch[:160],(1,2))
 elif level==5:
  far[:]=3
  for dx,dy,sx,sy,w,h in [(24,16,520,256,64,32),(152,96,144,272,48,24),(280,48,792,224,64,32),(408,120,160,352,32,16)]:
   a=canvas[sy:sy+h,sx:sx+w].copy();a[~np.isin(a,[3,6,12,15,19,21,23,26])]=3
   far[dy:dy+h,dx:dx+w]=a
 else:
  for x in (16,144,272,400):far[48:160,x:x+64]=canvas[384:496,96:160]
 far_tiles=[];far_lookup={};far_map=[]
 for y in range(0,160,8):
  for x in range(0,512,8):
   block=far[y:y+8,x:x+8];choices=[]
   for bank in range(2):
    d=((rgb[block][:,:,None,:]-rgb[bank*16:(bank+1)*16][None,None,:,:])**2).sum(3)
    pens=d.argmin(2);choices.append((int(np.take_along_axis(d,pens[:,:,None],2).sum()),bank,pens))
   _,bank,pens=min(choices,key=lambda c:c[0]);b=pack(pens.astype(np.uint8))
   if b not in far_lookup:far_lookup[b]=len(far_tiles);far_tiles.append(b)
   far_map.append((656 if level==3 else 700)+far_lookup[b]+(bank<<13))
 assert len(far_tiles)<=312,(level,len(far_tiles))
 output+=patterns(f'backdrop_{level}_extra',extra)+patterns(f'backdrop_{level}_far',far_tiles)
 for bank in range(2):output+=array(f'backdrop_{level}_remap{bank}','u16',remaps[bank])
 output+=array(f'backdrop_{level}_map','u16',far_map)
 hud_tiles=[]
 if level==3:
  # Continue exactly the same repeating texture through screen rows 0..4 and 25..27.
  for sy,h in [(0,32),(32,8),(200,24)]:
   for sx in range(0,256,32):
    for tx in range(0,32,8):
     for ty in range(0,h,8):
      block=patch[np.arange(sy+ty-40,sy+ty-32)%256][:,np.arange(sx+tx,sx+tx+8)%256]
      d=((rgb[block][:,:,None,:]-rgb[:16][None,None,:,:])**2).sum(3)
      hud_tiles.append(pack(d.argmin(2).astype(np.uint8)))
  assert len(far_tiles)<=92 and len(hud_tiles)==256
  output+=patterns('backdrop_hud',hud_tiles)
  output+='#define BACKDROP_HUD_TILES '+str(len(hud_tiles))+'\n'
 output+=f'static const Backdrop backdrop_{level}={{backdrop_{level}_extra,backdrop_{level}_far,backdrop_{level}_remap0,backdrop_{level}_remap1,backdrop_{level}_map,{n},{len(far_tiles)}}};\n'
 (ROOT/f'res/generated/backdrop_bg{level}.bin').write_bytes(raw+b''.join(extra))
 (ROOT/f'res/generated/backdrop_remap{level}.bin').write_bytes(np.array(remaps,dtype='>u2').tobytes())
 reports.append(dict(level=level+1,original_tiles=n,masked_tiles=len(extra),far_tiles=len(far_tiles),foreground_speed=1,background_speed=.5))
(ROOT/'src/backdrop_data.inc').write_text(output)
(ROOT/'reference/backdrops.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
