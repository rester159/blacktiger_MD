"""Split existing palace artwork into masked walls and a distant window layer."""
import json
import numpy as np
from arcade_source import ROOT
from extract import pack
raw=np.fromfile(ROOT/'res/generated/bg7.bin',dtype=np.uint8)
pixels=np.stack((raw>>4,raw&15),1).reshape(-1,8,8)
wm=np.fromfile(ROOT/'res/generated/map7.bin',dtype='>u2').reshape(128,256)
pal=np.fromfile(ROOT/'res/generated/pal7.bin',dtype='>u2')
rgb=np.array([[(int(c)>>1)&7,(int(c)>>5)&7,(int(c)>>9)&7]for c in pal])
canvas=np.zeros((320,2048),np.uint8)
for y in range(40):
 for x in range(256):
  w=int(wm[y,x]);t=pixels[(w&2047)-16]
  if w&0x800:t=t[:,::-1]
  if w&0x1000:t=t[::-1]
  canvas[y*8:y*8+8,x*8:x*8+8]=t+((w>>13)&3)*16
mask=np.zeros(canvas.shape,bool)
for x in (720,1008,1280):
 c=rgb[canvas[144:256,x:x+96]]
 cold=(c[:,:,2]>c[:,:,0]) | ((c[:,:,0]==c[:,:,1]) & (c[:,:,1]==c[:,:,2]) & (c[:,:,0]>0))
 for y,row in enumerate(cold):
  at=np.flatnonzero(row)
  if len(at):
   inside=np.zeros(96,bool);inside[at[0]:at[-1]+1]=True
   cut=row | (inside & (c[y].sum(1)==0))
   # Tiny warm-colored rock highlights belong to the scenery. Preserve the
   # wide gold mullions while filling these one-to-three-pixel interior gaps.
   for left,right in zip(at[:-1],at[1:]):
    if right-left<=4:cut[left:right+1]=True
   mask[144+y,x:x+96]=cut
# Complete the sky behind the curved arch, using its existing blue pen.
land=canvas[144:256,752:816].copy();land[~mask[144:256,752:816]]=int(canvas[160,768])
land=np.concatenate((land,land[:,::-1]),axis=1)
unique={bytes(32):0};patterns=[bytes(32)]
def tile(indexed,opaque=False):
 used=set((indexed[indexed!=255]//16).tolist());assert len(used)<=1,used
 bank=next(iter(used),0);p=np.where(indexed==255,0,indexed%16).astype(np.uint8)
 b=pack(p)
 if b not in unique:unique[b]=len(patterns);patterns.append(b)
 return (16+unique[b])|(bank<<13)|(0x8000 if opaque else 0)
fg=[]
for y in range(8,37):
 for x in range(72,169):
  a=canvas[y*8:y*8+8,x*8:x*8+8].copy();a[mask[y*8:y*8+8,x*8:x*8+8]]=255
  fg.append(tile(a,True))
far=[]
# Screen rows 5..24. Only the original window openings expose this plane.
for row in range(5,25):
 sy=row*8+64-144
 for col in range(16):
  a=land[max(0,min(104,sy)):max(0,min(104,sy))+8,col*8:col*8+8]
  # Every tile must use a single original palette. Nearest RGB333 maps the few
  # mixed palette tiles into the existing scenery bank without changing CRAM.
  values=np.array([16+int(np.argmin(((rgb[16:]-rgb[int(v)])**2).sum(1))) for v in range(32)],np.uint8)
  far.append(tile(values[a]))
assert len(patterns)<=996
arr=lambda name,typ,v:'static const '+typ+' '+name+'[]={'+','.join(map(str,v))+'};\n'
out='/* Original palace art split for native two-plane parallax. */\n'
out+=arr('arena_patterns','u32',[hex(int.from_bytes(b[i:i+4],'big'))for b in patterns for i in range(0,32,4)])
out+=arr('arena_walls','u16',fg)+arr('arena_far','u16',far)
out+='#define ARENA_TILES '+str(len(patterns))+'\n'
(ROOT/'src/arena_parallax_data.inc').write_text(out)
(ROOT/'reference/arena_parallax.json').write_text(json.dumps(dict(tiles=len(patterns),window_rects=[[x,144,96,112]for x in (720,1008,1280)],foreground_speed=1,background_speed=0.5,scope='Existing palace colors and scenery; curved window masks, mirrored landscape strip, hardware half-speed scrolling.'),indent=2)+'\n')
print('Arena tiles:',len(patterns))
