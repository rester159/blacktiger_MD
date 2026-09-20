#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/pair_oracle.json').read_text())
for key,path in [('trace_sha256','reference/pair_oracle_events.txt'),('lua_sha256','tools/pair_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','u8 terrain(s16 x,s16 y){return 0;}','#include "'+str(ROOT/'src/pair.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int part,int px,int py,int sample) {
 game=(Game){0};game.mode=PLAY;game.spawned[0]=2;loot_random=sample*256;
 game.p.x=px*256;game.p.y=py*256;game.actors[0]=(Actor){.active=1,.x=128*256,.y=96*256,.hp=1};
 for(int i=0;i<66;i++)if(pair_kinds[i])game.actors[0].def=i;
 init(0,part);}
 void tick(int damage,int *out) {
 if(damage)pair_hit(0,damage);if(game.actors[0].active)pair_step(0);
 Actor *a=&game.actors[0];PairState *s=&pairs[0];const AnimFrame *f=pair_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),s->animation.vx,s->animation.vy,s->animation.remaining,s->cycles,pair_vulnerable(0),f?f->code:-1,f?f->palette:-1,f?f->flip:-1,a->hp,game.score};
 for(int i=0;i<13;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','sentry.c','loot.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'b.dylib')],check=True)
 lib=C.CDLL(str(tmp/'b.dylib'));out=(C.c_int*13)();current=-1;count=0;maxcycles=0
 for line in (ROOT/'reference/pair_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['part'],c['px'],c['py'],c['random']);current=case
  lib.tick(c['damage'] if c['hit_tick']==tick else 0,out)
  assert task in ('0000','0510'),task
  assert out[12]==(10 if task=='0510' else 0),(case,tick,'score')
  assert out[0]==bool(a[0]),(case,tick,'active')
  if a[0]:
   def signed(v):return v if v<128 else v-256
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),signed(a[6]),signed(a[7]),a[10],a[8],int(not(a[12]&1)),display[0]|((display[1]&224)<<3),display[1]&7,(display[1]>>3)&1,a[14]]
   assert list(out)[:12]==expected,(case,tick,list(out),expected)
   maxcycles=max(maxcycles,a[8])
  count+=1
 assert maxcycles==16,maxcycles
 report={'passed':True,'source_body_ticks':count,'cases':len(ref['cases']),'maximum_cycles':maxcycles,'scope':'Both initial parts, all random choices, sixteen-direction aiming and drift, final escape cycle, vulnerability, weapon death, score and animation.'}
 (ROOT/'reports/pair-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
