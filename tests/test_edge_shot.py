#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/edge_shot_oracle.json').read_text())
for key,path in [('trace_sha256','reference/edge_shot_oracle_events.txt'),('lua_sha256','tools/edge_shot_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definitions=[next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(2,pc)) for pc in (0x8344,0x9af6)]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/edge_actor.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''int wall;u8 terrain(s16 x,s16 y){return wall && ((u16)x&2047)>=160?3:0;}u8 player_contact(s16 x,s16 y,u8 w,u8 h){return 0;}
 void setup(int profile,int direction,int obstacle){game=(Game){0};wall=obstacle;edge_shots_reset();EdgeShot *p=&edge_shots[0];animation_reset(&p->animation);p->active=1;p->profile=profile;p->segment=edge_shot_roots[profile*17+direction];p->hp=profile?32:24;p->pending=p->dying=0;p->x=128;p->y=96;}
 void tick(int damage,int *out){if(damage)edge_shot_hit(edge_shots[0].x,edge_shots[0].y,damage,0);edge_shots_step();EdgeShot *p=&edge_shots[0];const AnimFrame *f=edge_shot_frame(0);
 int v[]={p->active,p->x,p->y,p->animation.vx,p->animation.vy,p->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,p->hp,p->dying};for(int i=0;i<11;i++)out[i]=v[i];}
 ''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','loot.c','progress.c','sentry.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*11)();current=-1;count=0
 for line in (ROOT/'reference/edge_shot_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display=line.split('|');case=int(case);a=bytes.fromhex(a);c=ref['cases'][case]
  if case!=current:lib.setup(c['profile'],c['direction'],c['wall']);current=case
  lib.tick((1 if int(tick)==12 else 255) if c['hit'] and int(tick) in (12,24) else 0,out);assert out[0]==bool(a[0]),(case,tick,list(out),a.hex())
  if a[0]:
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),C.c_int8(a[6]).value,C.c_int8(a[7]).value,a[10],int(display)|((a[5]&224)<<3),a[5]&7,(a[5]>>3)&1,a[14],int(a[0]==64)]
   assert list(out)==expected,(case,tick,list(out),expected)
  count+=1
 report=dict(passed=True,source_projectile_ticks=count,cases=len(ref['cases']),scope='Both edge-caster projectile profiles, seventeen directions, terrain impact, weak/fatal hits, animation and offscreen retirement.')
 (ROOT/'reports/edge-shot-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
