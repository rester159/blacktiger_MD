"""Extract source slices; certify paths with the unchanged native controller.

This initial library uses screen-wide horizontal walk sockets. It deliberately
excludes pits at seams; vertical sockets/branches belong to a later expansion.
No graphics or collision blocks are invented or recolored.
"""
from pathlib import Path
import ctypes as C, hashlib, json, random, subprocess, tempfile
from collections import deque
ROOT=Path(__file__).resolve().parents[1]
class Motion(C.Structure):
 _fields_=[(n,C.c_uint16) for n in ('scroll_x','scroll_y','screen_x','screen_y','jump_origin')]+[(n,C.c_int8) for n in ('vx','vy')]+[(n,C.c_uint8) for n in ('fraction','subtick','pose','jumping','jump_request','direction','redirected','camera_return','below_origin','falling','ladder','low','frame','selector','previous','idle','jump_history','screen_motion')]
STUB='''#include "player_motion.h"
static u8 cells[14][32];static u16 span;
void load(const u8 *c){span=256;for(int y=0;y<14;y++)for(int x=0;x<16;x++)cells[y][x]=c[y*16+x];}
void pair_load(const u8 *a,const u8 *b){load(a);span=512;for(int y=0;y<14;y++)for(int x=0;x<16;x++)cells[y][x+16]=b[y*16+x];}
u8 terrain(s16 x,s16 y){x-=256;y-=512;if(y<0)return 3;if(y>=224)return 3;if(x<0 || x>=span)return y>=192?3:0;return cells[y>>4][x>>4];}
void init(PlayerMotion *p){*p=(PlayerMotion){.scroll_x=128,.scroll_y=528,.screen_x=128,.screen_y=144};}
void step(PlayerMotion *p,int input){player_motion_step(p,input,0);}
'''
def position(p):return p.scroll_x+p.screen_x-256,p.scroll_y+p.screen_y-512
# Animation counters do not affect collision or velocities. Keep every motion flag.
def key(p):return (position(p),p.vx,p.vy,p.fraction,p.jumping,p.jump_request,p.direction,p.redirected,p.camera_return,p.below_origin,p.falling,p.ladder,p.selector,p.previous,p.jump_history,p.screen_motion,p.jump_origin,p.screen_y)
def certify(lib,cells):
 lib.load(cells);p=Motion();lib.init(C.byref(p));q=deque([(bytes(p),[])]);seen={key(p)}
 while q and len(seen)<12000:
  raw,path=q.popleft()
  for inp in (1,33,0,32,8):
   p=Motion.from_buffer_copy(raw);steps=[]
   for _ in range(8):
    lib.step(C.byref(p),inp);steps.append(inp);x,y=position(p)
    if x<0 or x>272 or y<16 or y>176:break
    if x>=256 and y==160 and not(p.jumping or p.falling or p.ladder):return path+steps+[0]*8
   else:
    k=key(p)
    if k not in seen:seen.add(k);q.append((bytes(p),path+steps))
 return None

def main():
 chunks=[]
 with tempfile.TemporaryDirectory() as t:
  t=Path(t);(t/'stub.c').write_text(STUB)
  subprocess.run(['cc','-O2','-shared','-fPIC','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/player_motion.c'),str(t/'stub.c'),'-o',str(t/'motion.dylib')],check=True)
  lib=C.CDLL(str(t/'motion.dylib'));lib.load.argtypes=[C.c_char_p];lib.pair_load.argtypes=[C.c_char_p,C.c_char_p]
  geometry=[]
  for r in range(8):
   w=64 if r==2 else 128;data=(ROOT/f'res/generated/collision{r}.bin').read_bytes();h=len(data)//w;candidates=[]
   for y in range(h-13):
    for x in range(w-15):
     c=b''.join(data[(y+j)*w+x:(y+j)*w+x+16] for j in range(14))
     if not all(c[12*16+k]>=2 for k in (0,1,14,15)):continue
     # Four columns around each seam have walk clearance, even for a jumping hero.
     if not all(c[j*16+k]<2 for j in (8,9,10,11) for k in (0,1,14,15)):continue
     candidates.append((x,y,c))
   random.Random(871+r).shuffle(candidates)
   candidates.sort(key=lambda t: not any(v>=2 for v in t[2][11*16:12*16]))
   chosen=[];seen=set()
   # Prefer geometry diversity, then distinct source art when geometry repeats.
   for unique in (True,False):
    for x,y,c in candidates:
     if len(chosen)==15:break
     if any(a['x']==x and a['y']==y for a in chosen) or (unique and c in seen):continue
     path=certify(lib,c)
     if path is None:continue
     lib.pair_load(c,c);p=Motion();lib.init(C.byref(p))
     for inp in path+path:lib.step(C.byref(p),inp)
     if position(p)!=(512,160) or p.jumping or p.falling or p.ladder:continue
     anchors=[k*16 for k in range(2,14) if all(c[j*16+k]<2 and c[j*16+k+1]<2 for j in (10,11))]
     anchors=[a for a in anchors if c[12*16+(a>>4)]>=2 and c[12*16+(a>>4)+1]>=2]
     if not anchors:continue
     anchors=anchors[::max(1,len(anchors)//4)][:4]
     chosen.append(dict(round=r,x=x,y=y,path=path,anchors=anchors,collision_sha256=hashlib.sha256(c).hexdigest()))
     seen.add(c)
    if len(chosen)==15:break
   assert len(chosen)>=8,(r,len(chosen))
   print('source',r,'certified',len(chosen),flush=True);chunks+=chosen
   geometry += [b''.join(data[(a['y']+j)*w+a['x']:(a['y']+j)*w+a['x']+16] for j in range(14)) for a in chosen]
  # Actually replay the two witnesses without resetting controller state at
  # the seam. This checks every permitted ordered pair, including self-pairs.
  pair=[];pair_checks=0
  for i,a in enumerate(chunks):
   for j,b in enumerate(chunks):
    if a['round']!=b['round']:pair.append(0);continue
    lib.pair_load(geometry[i],geometry[j]);p=Motion();lib.init(C.byref(p))
    for inp in a['path']+b['path']:lib.step(C.byref(p),inp)
    ok=position(p)==(512,160) and not(p.jumping or p.falling or p.ladder)
    pair.append(int(ok));pair_checks+=1
 packed=[sum(pair[i+j]<<j for j in range(min(8,len(pair)-i))) for i in range(0,len(pair),8)]
 out='/* Generated from source maps and player_motion.c; do not edit. */\n'
 out+='static const DungeonChunk dungeon_chunks[]={\n'+',\n'.join('{'+','.join(map(str,[c['x'],c['y'],len(c['anchors'])]))+', {'+','.join(map(str,c['anchors']+[0]*(4-len(c['anchors']))))+'}}' for c in chunks)+'};\n'
 out+='static const u8 dungeon_chunk_start[9]={'+','.join(str(sum(c['round']<r for c in chunks)) for r in range(9))+'};\n'
 out+='static const u8 dungeon_pair_ok[]={'+','.join(map(str,packed))+'};\n'
 (ROOT/'src/dungeon_chunks.inc').write_text(out)
 report=dict(pair_checks=pair_checks,controller_sha256=hashlib.sha256((ROOT/'src/player_motion.c').read_bytes()).hexdigest(),chunks=chunks,pair_ok=packed,scope=__doc__)
 (ROOT/'reference/dungeon_chunks.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
