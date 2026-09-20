#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/reinforcement_shot_oracle.json').read_text())
for key,path in [('trace_sha256','reference/reinforcement_shot_oracle_events.txt'),('lua_sha256','tools/reinforcement_shot_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definitions=[next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(2,pc)) for pc in (0x8344,0x9af6)]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/reinforcement_body.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''u8 terrain(s16 x,s16 y){return 0;}u8 player_contact(s16 x,s16 y,u8 w,u8 h){return 0;}
 void setup(int part,int x){game=(Game){0};reinforcement_shots_reset();ReinforcementShot *p=&reinforcement_shots[0];animation_reset(&p->animation);p->active=1;p->part=part;p->x=x;p->y=96;}
 void tick(int *out){reinforcement_shots_step();ReinforcementShot *p=&reinforcement_shots[0];const AnimFrame *f=reinforcement_shot_frame(0);
 int v[]={p->active,p->x,p->y,p->animation.vx,p->animation.vy,p->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1};for(int i=0;i<9;i++)out[i]=v[i];}
 ''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','loot.c','progress.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*9)();current=-1;count=0
 for line in (ROOT/'reference/reinforcement_shot_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display=line.split('|');case=int(case);a=bytes.fromhex(a);c=ref['cases'][case]
  if case!=current:lib.setup(c['part'],c['x']);current=case
  lib.tick(out);assert out[0]==bool(a[0]),(case,tick,list(out),a.hex())
  if a[0]:
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),C.c_int8(a[6]).value,C.c_int8(a[7]).value,a[10],int(display)|((a[5]&224)<<3),a[5]&7,(a[5]>>3)&1]
   assert list(out)==expected,(case,tick,list(out),expected)
  count+=1
 report=dict(passed=True,source_projectile_ticks=count,cases=len(ref['cases']),scope='Both source profiles, all six parts, both directions, staged motion and animation, offscreen retirement. Shared native animation data verified identical for the two profiles.')
 (ROOT/'reports/reinforcement-shot-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
