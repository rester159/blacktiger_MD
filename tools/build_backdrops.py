"""Split source cave/sky/window artwork without modifying terrain or collision."""
import json
import numpy as np
from PIL import Image
from arcade_source import ROOT
from extract import pack

def array(name,typ,v):return f'static const {typ} {name}[]={{'+','.join(map(str,v))+'};\n'
def patterns(name,data):return array(name,'u32',[hex(int.from_bytes(b[i:i+4],'big')) for b in data for i in range(0,32,4)])
output='/* Generated from original level artwork by tools/build_backdrops.py. */\n';reports=[]
for level in (3,4,6):
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
 if level in (4,5,6):canvas=np.load(ROOT/f'res/generated/scenery{level}.npy')
 extra=[];lookup={b:i for i,b in enumerate(rawtiles)};remaps=[]
 for bank in range(2):
  remap=list(range(16))
  for i,tile in enumerate(tiles):
   indexed=tile+bank*16;changed=tile.copy()
   if level==3:
    changed[np.isin(indexed,[4,7,10,14,20])]=0
    if not rgb[indexed].any():changed[:]=1 # retain black in the other cave chambers
   b=pack(changed)
   if b not in lookup:lookup[b]=n+len(extra);extra.append(b)
   remap.append(16+lookup[b])
  remaps.append(remap)
 assert n+len(extra)<=1800,(level,n,len(extra))
 # Repeatable, independent background compiled into native patterns.
 far=np.zeros((160,512),np.uint8)
 if level==3:
  patch=canvas[784:912,160:288].copy();patch=np.concatenate((patch,patch[:,::-1]),1);patch=np.concatenate((patch,patch[::-1]),0)
  far=np.tile(patch[:160],(1,2))
 elif level==4:
  # Use the clean ascending half of the original blue ridge. Remove non-scenery
  # pens (a floating arrow marker), then mirror the native pixels into a ridge.
  # No wall/column crop and no invented or rescaled artwork.
  ridge=canvas[784:896,640:816].copy()
  ridge[~np.isin(ridge,[19,21,28])]=0
  ridge=np.concatenate((ridge,ridge[:,::-1]),axis=1)
  far[24:136,80:432]=ridge

 else:
  # Complete each pointed window with a reflected foot instead of cutting
  # its mullions at the bottom of the parallax plane. Leave sky on all edges.
  window=canvas[384:496,96:160].copy()
  window[-16:]=window[:16][::-1]
  for x in (16,144,272,400):far[24:136,x:x+64]=window
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
 assert len(far_tiles)<312,(level,len(far_tiles))
 Image.fromarray((rgb[far]*255//7).astype(np.uint8)).save(ROOT/f'reports/backdrop-level{level+1}-tiles.png')
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
  # All 256 horizontal positions of the eight-pixel right edge. Variable
  # 32-bit shifts for 64 rows were a substantial per-scroll 68000 cost.
  edges=[]
  for x in range(256):
   for row in range(8):
    band=0 if row<4 else 1 if row==4 else 2
    height=(4,1,3)[band];y=row if band==0 else 0 if band==1 else row-5
    base=(0,128,160)[band];a=base+(x//8)*height+y;b=base+((x//8+1)&31)*height+y
    shift=(x&7)*4
    edge=bytearray()
    for line in range(8):
     left=int.from_bytes(hud_tiles[a][line*4:line*4+4],'big')
     right=int.from_bytes(hud_tiles[b][line*4:line*4+4],'big')
     edge+=(((left<<shift)|(right>>(32-shift) if shift else 0))&0xffffffff).to_bytes(4,'big')
    edges.append(bytes(edge))
  edge_blocks=[];edge_lookup={};edge_indices=[]
  for x in range(256):
   block=b''.join(edges[x*8:x*8+8])
   if block not in edge_lookup:
    edge_lookup[block]=len(edge_blocks);edge_blocks.append(block)
   edge_indices.append(edge_lookup[block])
  assert len(edge_blocks)<=256
  edge_tiles=[];tile_lookup={};tile_indices=[]
  for block in edge_blocks:
   for i in range(0,256,32):
    tile=block[i:i+32]
    if tile not in tile_lookup:
     tile_lookup[tile]=len(edge_tiles);edge_tiles.append(tile)
    tile_indices.append(tile_lookup[tile])
  output+=patterns('backdrop_hud_edge_tiles',edge_tiles)
  output+=array('backdrop_hud_edges','u16',tile_indices)
  output+=array('backdrop_hud_edge_index','u8',edge_indices)
  output+='#define BACKDROP_HUD_TILES '+str(len(hud_tiles))+'\n'
 output+=f'static const Backdrop backdrop_{level}={{backdrop_{level}_extra,backdrop_{level}_far,backdrop_{level}_remap0,backdrop_{level}_remap1,backdrop_{level}_map,{n},{len(far_tiles)}}};\n'
 (ROOT/f'res/generated/backdrop_bg{level}.bin').write_bytes(raw+b''.join(extra))
 (ROOT/f'res/generated/backdrop_remap{level}.bin').write_bytes(np.array(remaps,dtype='>u2').tobytes())
 reports.append(dict(level=level+1,original_tiles=n,masked_tiles=len(extra),far_tiles=len(far_tiles),foreground_speed=1,background_speed=.5))
(ROOT/'src/backdrop_data.inc').write_text(output)
(ROOT/'reference/backdrops.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
