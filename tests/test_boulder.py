#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/boulder_oracle.json').read_text())
for key,path in [('trace_sha256','reference/boulder_oracle_events.txt'),('lua_sha256','tools/boulder_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','u8 terrain(s16 x,s16 y){return y>=160?3:0;}','#include "'+str(ROOT/'src/boulder.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int root,int px,int y) {
 game=(Game){0};game.mode=PLAY;game.spawned[0]=1;
 game.p.x=px*256;game.p.y=16*256;game.actors[0]=(Actor){.active=1,.x=128*256,.y=y*256,.hp=255};
 for(int i=0;i<66;i++)if(boulder_kinds[i])game.actors[0].def=i;
 boulder_spawn(0);boulders[0].segment=boulder_roots[root];}
 void tick(int damage,int *out) {
 if(damage)boulder_hit(0,damage);if(game.actors[0].active)boulder_step(0);
 Actor *a=&game.actors[0];BoulderState *s=&boulders[0];const AnimFrame *f=boulder_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),s->animation.vx,s->animation.vy,s->fraction,s->animation.remaining,s->bounced,s->damage,a->state,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,a->hp,game.spawned[0],game.score};
 for(int i=0;i<16;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/animation.c'),str(ROOT/'src/data.c'),str(ROOT/'src/progress.c'),str(tmp/'stub.c'),'-o',str(tmp/'b.dylib')],check=True)
 lib=C.CDLL(str(tmp/'b.dylib'));out=(C.c_int*16)();current=-1;count=0;retired=[]
 for line in (ROOT/'reference/boulder_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['root_index'],c['px'],c['y']);current=case
  lib.tick(c['damage'] if c['hit_tick']==tick else 0,out)
  assert task in ('0000','0558'),task
  assert out[15]==(300 if task=='0558' else 0),(c['name'],tick,'score',out[15],task)
  assert out[0]==bool(a[0]),(c['name'],tick,'active',out[0],a[0])
  assert out[14]==(2 if int(persist,16)&2 else int(persist,16)),(c['name'],tick,'persist',out[14],persist)
  if a[0]:
   def signed(v):return v if v<128 else v-256
   flip=(a[5]>>3)&1;code=(display[0]-flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),signed(a[6]),signed(a[7]),a[18],a[10],a[32],a[15],int(bool(a[12]&1)),code,a[5]&7,flip,a[14]]
   assert list(out)[:14]==expected,(c['name'],tick,list(out),expected)
  elif not any(v['case']==case for v in retired):retired.append(dict(case=case,tick=tick))
  count+=1
 report={'passed':True,'source_body_ticks':count,'retire_events':retired,'scope':'Proximity edges, fall acceleration, three impacts, byte-based first-bounce direction, damage change, nonfatal/fatal weapons, animation, persistence and the shared hit-handler score task.'}
 (ROOT/'reports/boulder-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
