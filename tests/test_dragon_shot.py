#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/dragon_shot_oracle.json').read_text())
for key,path in [('trace_sha256','reference/dragon_shot_oracle_events.txt'),('lua_sha256','tools/dragon_shot_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/dragon_shot.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''int wall;u8 terrain(s16 x,s16 y){u16 sx=(u16)x&2047;return wall && (sx>=160 || sx<96)?3:0;}
 void setup(int kind,int direction,int x,int obstacle,int full,int profile,int left){
 game=(Game){0};game.p.y=120*256;wall=obstacle;dragon_shots_reset();container_actor_reset();
 if(full){for(int i=16;i<24;i++){dragon_shots[i]=(DragonShot){0};dragon_shots[i].active=1;dragon_shots[i].kind=2;dragon_shots[i].mode=25;dragon_shots[i].animation.remaining=65535;}for(int i=0;i<24;i++)container_traps[i].active=1;}
 spawn(kind,direction,x,96,profile,left);}
 void snapshot(int slot,int *out){DragonShot *p=&dragon_shots[slot];const AnimFrame *f=dragon_shot_frame(slot);
 int v[]={p->active,p->x,p->y,p->animation.vx,p->animation.vy,p->animation.remaining&255,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,p->mode};for(int i=0;i<10;i++)out[i]=v[i];}
 void wave_snapshot(int *out){for(int i=0;i<6;i++){ContainerTrap *p=&container_traps[i];out[3*i]=p->active;out[3*i+1]=p->x;out[3*i+2]=p->y;}}
 void tick(int slot,int damage){if(damage)dragon_shot_hit_slot(slot,damage);dragon_shots_step();}
 ''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','container_actor.c','container.c','hazard.c','player_death.c','armor_break.c','loot.c','progress.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*10)();current=-1;count=0;waves=0;explosions=0;zero_frames=0
 def check(slot,a,display,medium):
  lib.snapshot(slot,out);assert out[0]==bool(a[0]),(case,tick,'active',slot,list(out),a.hex())
  if not a[0]:return
  flip=(a[5]>>3)&1;code=(int(display)-(flip if medium else 0))|((a[5]&224)<<3)
  expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),C.c_int8(a[6]).value,C.c_int8(a[7]).value,a[10],code,a[5]&7,flip,a[12]]
  assert list(out)==expected,(case,tick,slot,list(out),expected,a.hex())
 for line in (ROOT/'reference/dragon_shot_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,b,bd,w=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);b=bytes.fromhex(b);w=bytes.fromhex(w);c=ref['cases'][case];slot=16 if c['kind']==2 else 0
  if case!=current:lib.setup(c['kind'],c['direction'],c['x'],c['wall'],c['full'],c['profile'],c['left']);current=case
  lib.tick(slot,int(c['hit'] and tick==12));check(slot,a,display,c['kind']==2)
  zero_frames+=bool(a[0] and a[10]==0)
  if c['kind']!=2 and not c['full']:
   check(16,b,bd,True);explosions+=bool(b[0])
   actual=(C.c_int*18)();lib.wave_snapshot(actual)
   for i in range(6):
    raw=w[i*32:i*32+32];assert actual[i*3]==bool(raw[0]),(case,tick,'wave active',i,list(actual),w.hex())
    if raw[0]:assert list(actual)[i*3+1:i*3+3]==[int.from_bytes(raw[1:3],'big',signed=True),int.from_bytes(raw[3:5],'big',signed=True)],(case,tick,'wave position',i,list(actual),w.hex())
   waves+=bool(w[0])
  count+=1
 assert waves and explosions and zero_frames,(waves,explosions,zero_frames)
 report=dict(passed=True,source_projectile_ticks=count,cases=len(ref['cases']),explosion_ticks=explosions,wave_ticks=waves,zero_duration_frames=zero_frames,scope='Sixteen orb directions, seeds, medium explosions, terrain, fatal hits, available/full pools, edge retirement and ground-wave launch coordinates. Native projectile family integrated; source global pool contention remains separate.')
 (ROOT/'reports/dragon-shot-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
