#!/usr/bin/env python3
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/edge_spawn_oracle.json').read_text())
for key,path in [('trace_sha256','reference/edge_spawn_oracle_events.txt'),('lua_sha256','tools/edge_spawn_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 (tmp/'stub.c').write_text('#include "'+str(ROOT/'src/edge_spawn.c')+'"\n'+'''Game game;static int floor_y;
 u8 terrain(s16 x,s16 y){return y>=floor_y?3:0;}
 void run(int x,int y,int px,int py,int face,int primary,int floor,int full,int *out){
 game=(Game){0};game.p.x=px*256;game.p.y=py*256;game.p.face=face;game.spawned[0]=primary;floor_y=floor;
 if(full)for(int i=0;i<MAX_ACTORS;i++)game.actors[i].active=1;
 s16 sx=x,sy=y;out[0]=edge_spawn_prepare(0,&sx,&sy);out[1]=game.spawned[0];out[2]=sx;out[3]=sy;}
 ''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(tmp/'stub.c'),'-o',str(tmp/'e.dylib')],check=True)
 lib=C.CDLL(str(tmp/'e.dylib'));out=(C.c_int*4)();count=0
 for line in (ROOT/'reference/edge_spawn_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  tag,case,*values=line.split('|');c=ref['cases'][int(case)];expected=list(map(int,values));expected[0]=bool(expected[0])
  lib.run(*[c[k] for k in ('x','y','px','py','face','primary','ground','full')],out)
  assert list(out)[:2]==expected[:2],(case,list(out),expected)
  if out[0] or out[1]!=c['primary']:assert list(out)[2:]==expected[2:4],(case,list(out),expected)
  assert expected[4]==out[0]
  count+=1
report=dict(passed=True,constructor_cases=count,scope='Screen bounds, byte-wrapped proximity, both edge directions, six floor-search heights, full-pool refusal, persistent row suppression, and consumed active flag on failed ground search. Body behavior is checked separately.')
(ROOT/'reports/edge-spawn-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
