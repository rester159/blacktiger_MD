"""Palace walls/window masks, distant scenery, and resident foreground columns."""
import json
import numpy as np
from arcade_source import ROOT
from extract import pack
raw=np.fromfile(ROOT/'res/generated/bg7.bin',dtype=np.uint8)
pixels=np.stack((raw>>4,raw&15),1).reshape(-1,8,8)
wm=np.fromfile(ROOT/'res/generated/map7.bin',dtype='>u2').reshape(128,256)
pal=np.fromfile(ROOT/'res/generated/pal7.bin',dtype='>u2')
rgb=np.array([[(int(c)>>1)&7,(int(c)>>5)&7,(int(c)>>9)&7]for c in pal])
canvas=np.zeros((1024,2048),np.uint8)
for y in range(128):
 for x in range(256):
  w=int(wm[y,x]);t=pixels[(w&2047)-16]
  if w&0x800:t=t[:,::-1]
  if w&0x1000:t=t[::-1]
  canvas[y*8:y*8+8,x*8:x*8+8]=t+((w>>13)&3)*16
mask=np.zeros(canvas.shape,bool)
for x in (720,1008,1280,1520,1744):
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
# Separate the exposed blue sky/landscape as well as the palace windows.
# Gold architecture and collision data stay in the world layer.
colors=rgb[canvas]
exterior=np.indices(canvas.shape)[0]>=640
exterior |= np.indices(canvas.shape)[1]<552
exterior |= np.indices(canvas.shape)[1]>=1920
mask |= exterior & (colors[:,:,2]>colors[:,:,0]) & (colors[:,:,2]>=colors[:,:,1])
patterns=[bytes(raw[i:i+32]) for i in range(0,len(raw),32)]
unique={b:i for i,b in enumerate(patterns)}
def tile(indexed,opaque=False):
 used=set((indexed[indexed!=255]//16).tolist());assert len(used)<=1,used
 bank=next(iter(used),0);p=np.where(indexed==255,0,indexed%16).astype(np.uint8)
 b=pack(p)
 if b not in unique:unique[b]=len(patterns);patterns.append(b)
 return (16+unique[b])|(bank<<13)|(0x8000 if opaque else 0)
# Move every full-height palace column off the wall layer. Preserve arches,
# torches and window openings; patch the former shafts using original wall art.
wall_canvas=canvas.copy()
for top,left,right in [(64,568,1896),(448,632,1256)]:
 for x in range(left,right,80):
  for dy in range(192):
   half=16 if dy<48 or dy>=160 else 8
   center=x+16
   for xx in range(center-half,center+half):
    # Repeating unadorned masonry, sampled away from torches and pillars.
    wall_canvas[top+dy,xx]=canvas[112+((dy-48)%32),680+((xx-center+16)%32)]
  # Window scenery must extend through the old column position.
  if top==64:
   for y in range(144,256):
    for wx in (720,1008,1280,1520,1744):
     at=np.flatnonzero(mask[y,wx:wx+96])
     if len(at):mask[y,wx+at[0]:wx+at[-1]+1]=True
fg=[]
for y in range(128):
 for x in range(256):
  cut=mask[y*8:y*8+8,x*8:x*8+8]
  if not cut.any() and np.array_equal(wall_canvas[y*8:y*8+8,x*8:x*8+8],canvas[y*8:y*8+8,x*8:x*8+8]):fg.append(int(wm[y,x])|0x8000);continue
  a=wall_canvas[y*8:y*8+8,x*8:x*8+8].copy();a[cut]=255
  fg.append(tile(a,True))
far=[]
# One resident landscape for both windows and open exterior: no streaming or
# extra per-frame sprites. Mirror tile attributes instead of duplicate pixels.
land=canvas[768:880,784:848].copy()
values=np.array([16+int(np.argmin(((rgb[16:]-rgb[int(v)])**2).sum(1))) for v in range(32)],np.uint8)
sky=int(values[int(canvas[700,400])])
for row in range(20):
 sy=row*8-24
 for col in range(16):
  tx=col if col<8 else 15-col
  a=land[sy:sy+8,tx*8:tx*8+8] if 0<=sy<112 else np.full((8,8),sky,np.uint8)
  far.append(tile(values[a])^(0x800 if col>=8 else 0))
assert len(patterns)<=1700
arr=lambda name,typ,v:'static const '+typ+' '+name+'[]={'+','.join(map(str,v))+'};\n'
out='/* Original palace art: two background planes plus foreground column sprites. */\n'
out+=arr('arena_patterns','u32',[hex(int.from_bytes(b[i:i+4],'big'))for b in patterns for i in range(0,32,4)])
far_ids=list(dict.fromkeys(w&2047 for w in far))
far_patterns=[patterns[i-16] for i in far_ids]
far=[(w&0xf800)|(884+far_ids.index(w&2047)) for w in far]
out+=arr('arena_walls','u16',fg)+arr('arena_far','u16',far)
near=[fg[y*256+x] for y in range(8,37) for x in range(72,169)]
near_ids=list(dict.fromkeys(w&2047 for w in near))
assert len(near_ids)<=828
out+=arr('arena_near','u16',[(w&0xf800)|(16+near_ids.index(w&2047)) for w in near])
out+=arr('arena_near_patterns','u32',[hex(int.from_bytes(patterns[t-16][i:i+4],'big')) for t in near_ids for i in range(0,32,4)])
out+='#define ARENA_NEAR_TILES '+str(len(near_ids))+'\n'
out+=arr('arena_far_patterns','u32',[hex(int.from_bytes(b[i:i+4],'big'))for b in far_patterns for i in range(0,32,4)])
out+='#define ARENA_FAR_TILES '+str(len(far_patterns))+'\n'
assert len(far_patterns)<=128
columns=[]
# Each block is in VDP sprite column-major tile order.
for y,h,w,left,clip in [(64,32,32,648,False),(112,32,16,656,False),(224,32,32,648,True)]:
 a=canvas[y:y+h,left:left+w].copy()
 if w==32:
  # Keep the column silhouette, without importing the adjoining wall/arch.
  for row in range(h):
   half=8 if y==64 else (8 if row<16 else 12)
   a[row,:16-half]=255;a[row,16+half:]=255
 for tx in range(w//8):
  for ty in range(h//8):
   b=a[ty*8:ty*8+8,tx*8:tx*8+8]
   remap=np.array([1+int(np.argmin(((rgb[1:16]-rgb[v])**2).sum(1))) for v in range(32)],np.uint8)
   columns.append(pack(np.where(b==255,0,remap[np.minimum(b,31)]).astype(np.uint8)))
out+=arr('arena_columns','u32',[hex(int.from_bytes(b[i:i+4],'big'))for b in columns for i in range(0,32,4)])
out+='#define ARENA_COLUMN_TILES '+str(len(columns))+'\n'
out+='#define ARENA_TILES '+str(len(patterns))+'\n'
(ROOT/'src/arena_parallax_data.inc').write_text(out)
(ROOT/'reference/arena_parallax.json').write_text(json.dumps(dict(tiles=len(patterns),window_rects=[[x,144,96,112]for x in (720,1008,1280,1520,1744)],column_speed=1.25,foreground_speed=1,background_speed=0.5,scope='Existing palace colors and scenery; curved window masks, mirrored landscape strip, hardware half-speed scrolling; separate sprite columns at 1.25 camera speed.'),indent=2)+'\n')
(ROOT/'res/generated/palace_patterns.bin').write_bytes(b''.join(patterns))
(ROOT/'res/generated/palace_map.bin').write_bytes(np.array(fg,dtype='>u2').tobytes())
print('Arena tiles:',len(patterns))
