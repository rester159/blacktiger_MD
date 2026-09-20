#!/usr/bin/env python3
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/player_dagger_oracle.json').read_text())
for key,path in [('trace_sha256','reference/player_dagger_oracle_events.txt'),('lua_sha256','tools/player_dagger_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'stub.c').write_text('''#include "player_dagger.h"
 Game game;int wall;
 u8 terrain(s16 x,s16 y){x=(u16)x&2032;return wall && (x==416 || x==320)?3:0;}
 int setup(int left,int low,int w){game=(Game){0};game.cam_x=game.cam_y=256;wall=w;player_daggers_reset();int n=0;for(int i=0;i<4;i++)n+=player_daggers_launch(368,352,left,low);return n;}
 void tick(int drift,int hit){game.cam_x+=drift;if(hit)for(int i=0;i<9;i++)player_dagger_hit(i,0);player_daggers_step();}
 void snapshot(int slot,int *out){PlayerDagger *p=&player_daggers[slot];const AnimFrame *f=player_dagger_frame(slot);int v[]={p->active,p->x-game.cam_x,p->y-game.cam_y,p->animation.remaining,p->animation.vx,p->animation.vy,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,p->hidden};for(int i=0;i<10;i++)out[i]=v[i];}
 ''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/player_dagger.c'),str(ROOT/'src/animation.c'),str(tmp/'stub.c'),'-o',str(tmp/'dagger.dylib')],check=True)
 lib=C.CDLL(str(tmp/'dagger.dylib'));out=(C.c_int*10)();count=0;spawns=0
 for line in (ROOT/'reference/player_dagger_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  parts=line.split('|');case=int(parts[1]);c=ref['cases'][case]
  if parts[0]=='SPAWN':
   assert lib.setup(c['left'],c['low'],c['wall'])==3
   raw=bytes.fromhex(parts[2]);assert sum(raw[i*32]==128 for i in range(9))==9;spawns+=1;continue
  _,_,tick,raw,display=parts;tick=int(tick);raw=bytes.fromhex(raw);display=bytes.fromhex(display)
  lib.tick(c['drift'],tick==c['hit'])
  for i in range(9):
   a=raw[i*32:i*32+32];d=display[i*4:i*4+4];lib.snapshot(i,out)
   assert out[0]==({128:1,64:2,0:0}[a[0]]),(case,tick,i,'active',list(out),a.hex())
   if out[0]:
    y=int.from_bytes(a[3:5],'big',signed=True);hidden=bool(a[3]);code=d[0]|((a[5]&224)<<3)
    expected=[out[0],int.from_bytes(a[1:3],'big',signed=True),y,a[10],int.from_bytes(a[6:7],signed=True),int.from_bytes(a[7:8],signed=True),-1 if hidden else code,-1 if hidden else a[5]&7,-1 if hidden else (a[5]>>3)&1,hidden]
    assert list(out)==expected,(case,tick,i,list(out),expected)
   count+=1
 report=dict(passed=True,source_ticks=count,cases=len(ref['cases']),full_volley_pool_cases=spawns,scope='All three dagger trajectories and nine-slot allocation, both facings, crouch launch offset, terrain impacts, hit explosions, camera displacement and retirement.')
 (ROOT/'reports/player-dagger-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
