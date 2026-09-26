#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/container_trap_oracle.json').read_text())
for key,path in [('trace_sha256','reference/container_trap_oracle_events.txt'),('lua_sha256','tools/container_trap_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;volatile u16 loot_random;','u8 terrain(s16 x,s16 y){return 0;}','#include "'+str(ROOT/'src/container_actor.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int part,int left,int y) {
 game=(Game){0};container_actor_reset();ContainerTrap *t=&container_traps[0];*t=(ContainerTrap){0};
 t->active=1;t->segment=container_trap_roots[part];t->left=left;t->x=128;t->y=y;t->part=part%3;}
 void tick(int *out) {
 container_traps_tick();ContainerTrap *t=&container_traps[0];const AnimFrame *f=container_trap_frame(0);
 int v[]={t->active,t->x,t->y,t->animation.vx,t->animation.vy,t->animation.remaining,t->contact,f?f->code:-1,f?f->palette:-1,f?f->flip:-1};
 for(int i=0;i<10;i++)out[i]=v[i];}
/* Exercise allocation and retirement across all four six-piece groups. */
 int pool_bounds(void) {
 container_actor_reset();game=(Game){0};
 for(int group=0;group<4;group++) {
  container_ground_spawn(120,0);
  if(container_traps_occupied!=(group+1)*6)return 1+group;
 }
 container_ground_spawn(120,0);
 if(container_traps_occupied!=MAX_CONTAINER_TRAPS)return 5;
 for(int group=3;group>=0;group--) {
  for(int i=group*6;i<MAX_CONTAINER_TRAPS;i++)container_traps[i].active=0;
  container_traps_tick();
  if(container_traps_occupied>group*6)return 6+group;
  for(int i=container_traps_occupied;i<MAX_CONTAINER_TRAPS;i++)if(container_traps[i].active)return 10+group;
 }
 container_ground_spawn(120,0);
 if(container_traps_occupied!=6)return 14;
 container_actor_restart();
 return container_traps_occupied?15:0;
 }
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','container.c','hazard.c','player_death.c','armor_break.c','data.c')],str(ROOT/'src/progress.c'),str(tmp/'stub.c'),'-o',str(tmp/'b.dylib')],check=True)
 lib=C.CDLL(str(tmp/'b.dylib'));out=(C.c_int*10)();current=-1;count=0
 for line in (ROOT/'reference/container_trap_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['part'],c['left'],c['y']);current=case
  lib.tick(out);assert out[0]==bool(a[0]),(case,tick,'active')
  if a[0]:
   def signed(v):return v if v<128 else v-256
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),signed(a[6]),signed(a[7]),a[10],int(not(a[12]&2)),display[0]|((display[1]&224)<<3),display[1]&7,(display[1]>>3)&1]
   assert list(out)==expected,(case,tick,list(out),expected)
  count+=1
 assert lib.pool_bounds()==0, 'Trap pool allocation/retirement bound'
 report={'passed':True,'pool_bounds_checked':True,'source_trap_ticks':count,'cases':len(ref['cases']),'scope':'All six parts in both directions, animation frames, displacement, contact enable timing and retirement. Constructor ground search and shared arcade pool contention are not covered.'}
 (ROOT/'reports/container-trap-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
