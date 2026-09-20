#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/waveboss_seed_oracle.json').read_text())
for key,path in [('trace_sha256','reference/waveboss_seed_oracle_events.txt'),('lua_sha256','tools/waveboss_seed_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;volatile u16 loot_random;','u8 shop_poison;int wall;u8 terrain(s16 x,s16 y){return y>=160 || (wall && x>=160 && x<176 && y>=wall)?3:0;} void game_boss_clear(void){} void container_wave_spawn(s16 x,u8 left){} void container_ground_spawn(s16 x,u8 left){}','#include "'+str(ROOT/'src/waveboss.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int profile,int left,int y,int w) {
 game=(Game){0};waveboss_reset();wall=w;WaveBossSeed *t=&waveboss_seeds[0];*t=(WaveBossSeed){0};
 t->active=1;t->segment=waveboss_roots[16+left];t->left=left;t->x=128;t->y=y;t->profile=profile;}
 void tick(int *out) {
 waveboss_seeds_tick();WaveBossSeed *t=&waveboss_seeds[0];const AnimFrame *f=waveboss_seed_frame(0);
 int v[]={t->active,t->x,t->y,t->animation.vx,t->animation.vy,t->animation.remaining,0,f?f->code:-1,f?f->palette:-1,f?f->flip:-1};
 for(int i=0;i<10;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','data.c')],str(ROOT/'src/progress.c'),str(tmp/'stub.c'),'-o',str(tmp/'b.dylib')],check=True)
 lib=C.CDLL(str(tmp/'b.dylib'));out=(C.c_int*10)();current=-1;count=0
 for line in (ROOT/'reference/waveboss_seed_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['profile'],c['left'],c['y'],c['wall']);current=case
  lib.tick(out);assert out[0]==bool(a[0]),(case,tick,'active')
  if a[0]:
   def signed(v):return v if v<128 else v-256
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),signed(a[6]),signed(a[7]),a[10],int(not(a[12]&2)),display[0]|((display[1]&224)<<3),display[1]&7,(display[1]>>3)&1]
   assert list(out)==expected,(case,tick,list(out),expected)
  count+=1
 report={'passed':True,'source_trap_ticks':count,'cases':len(ref['cases']),'scope':'Both seed directions and boss variants, source animation, motion, terrain branching and retirement. Shared wave construction and global pool contention are separate.'}
 (ROOT/'reports/waveboss-seed-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
