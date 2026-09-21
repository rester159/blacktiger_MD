"""Shared source small/medium edge integration and ordered retirement."""
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/actor_motion_oracle.json').read_text())
for key,path in [('trace_sha256','reference/actor_motion_oracle_events.txt'),('lua_sha256','tools/actor_motion_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder);(p/'stub.c').write_text('''#include "animation.h"
Game game;
void move(int x,int y,int vx,int vy,int mode,int persistence,int camera,int *out){
 game=(Game){0};game.cam_x=camera;game.cam_y=camera;game.spawned[0]=persistence;
 Actor *a=&game.actors[0];a->active=1;a->x=(x+camera)*256;a->y=(y+camera)*256;
 actor_motion(a,vx*256,vy*256,mode);
 out[0]=a->active?128:0;out[1]=(u16)(PX(a->x)-camera);out[2]=(u16)(PX(a->y)-camera);out[3]=game.spawned[0];
}
''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/animation.c'),str(p/'stub.c'),'-o',str(p/'motion.dylib')],check=True)
 lib=C.CDLL(str(p/'motion.dylib'));out=(C.c_int*4)();count=0
 for l in (ROOT/'reference/actor_motion_oracle_events.txt').read_text().splitlines():
  if l=='COMPLETE':break
  _,case,*expected=l.split('|');c=ref['cases'][int(case)]
  for camera in (0,256,752,1664):
   lib.move(*[c[k] for k in ('x','y','vx','vy','mode','persistence')],camera,out)
   assert list(out)==list(map(int,expected)),(c,camera,list(out),expected)
   count+=1
 report=dict(passed=True,source_cases=len(ref['cases']),native_cases=count,scope='Original fixed 3351 medium integration across signed/wrapped boundary positions, three velocities, retirement suppression, both persistence states, and native camera translation. X retirement precedes Y movement. Does not establish all family mode transitions or global camera/scanner fidelity.')
 (ROOT/'reports/actor-motion-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
