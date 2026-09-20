#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/projectile_edge_oracle.json').read_text())
for key,path in [('trace_sha256','reference/projectile_edge_oracle_events.txt'),('lua_sha256','tools/projectile_edge_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 (tmp/'stub.c').write_text('''#include "assets.h"
#include "missile.h"
Game game;
const u8 dagger_width=4,dagger_height=2,contact_player_width=3,contact_player_height=8;
static const AnimFrame frame={0,100,0,0,0,0,0};
static const AnimClip clip={&frame,1,65535};
void check(int x,int y,int vx,int vy,int cx,int cy,int *out) {
 game=(Game){0};game.cam_x=cx;game.cam_y=cy;missile_reset();
 missile_spawn(x+cx,y+cy,&clip,&clip,1,8,4,1);
 missiles[0].animation.remaining=100;missiles[0].animation.vx=vx;missiles[0].animation.vy=vy;
 missile_tick();out[0]=missiles[0].active;out[1]=missiles[0].x-cx;out[2]=missiles[0].y-cy;
}
''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/animation.c'),str(ROOT/'src/missile.c'),str(tmp/'stub.c'),'-o',str(tmp/'p.dylib')],check=True)
 lib=C.CDLL(str(tmp/'p.dylib'));out=(C.c_int*3)();count=0
 for line in (ROOT/'reference/projectile_edge_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,active,x,y=line.split('|');c=ref['cases'][int(case)]
  signed=lambda v:int.from_bytes(int(v).to_bytes(2,'little'),'big',signed=True)
  expected=[int(active)!=0,signed(x),signed(y)]
  for cx,cy in ((0,0),(320,640),(1024,1024)):
   lib.check(c['x'],c['y'],c['vx'],c['vy'],cx,cy,out)
   assert list(out)==expected,(case,c,cx,cy,list(out),expected)
   count+=1
 report={'passed':True,'source_boundary_cases':len(ref['cases']),'translated_world_checks':count,'scope':'Small actor loader edge removal, asymmetric horizontal/vertical thresholds, velocity crossings and x-before-y retirement, reused by native projectiles and paired flyers.'}
 (ROOT/'reports/projectile-edge-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
