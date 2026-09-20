#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/crawler_oracle.json').read_text())
for key,path in [('trace_sha256','reference/crawler_oracle_events.txt'),('lua_sha256','tools/crawler_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definitions=[next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==key) for key in ((3,0xaab3),(3,0xb153),(7,0xa3b6),(3,0xb7f3))]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;volatile u16 loot_random;','#include "'+str(ROOT/'src/crawler.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''static int wall;
 u8 terrain(s16 x,s16 y){return y>=160 || (wall && x>=160 && x<176 && y>=wall)?3:0;}
 void setup(int px,int y,int part,int obstacle,int definition,int random) {
 game=(Game){0};wall=obstacle;loot_random=random<<8;game.p.x=px*256;game.p.y=120*256;game.mode=PLAY;game.spawned[0]=1;
 game.actors[0]=(Actor){.active=1,.x=128*256,.y=y*256,.def=definition};crawler_spawn(0,part);}
 void pow_hit(void){crawler_screen_attack(0);}
 void children(int *out) {for(int i=0;i<2;i++){Actor *a=&game.actors[i+1];out[i*3]=a->active;out[i*3+1]=PX(a->x);out[i*3+2]=PX(a->y);}}
 void tick(int damage,int *out) {
 Actor *a=&game.actors[0];CrawlerState *s=&crawlers[0];
 if(damage && a->active)crawler_hit(0,damage);if(a->active)crawler_step(0);
 const AnimFrame *f=crawler_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),s->animation.vx,s->animation.vy,s->fraction,s->left,s->mode,a->life,s->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,game.score,game.spawned[0]};
 for(int i=0;i<15;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','progress.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*15)();current=-1;count=0;splits=0
 for line in (ROOT/'reference/crawler_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  if line.startswith('SPLIT|'):
   v=line.split('|');children=(C.c_int*6)();lib.children(children)
   expected=[]
   for raw in v[3:]:
    actor=bytes.fromhex(raw);expected.extend([bool(actor[0]),int.from_bytes(actor[1:3],'big'),int.from_bytes(actor[3:5],'big')])
   assert list(children)==expected,('split',v[:3],list(children),expected)
   splits+=1
   continue
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['px'],c['y'],c['part'],c['wall'],definitions[c['profile']],c['random']);current=case
  if tick==c.get('pow_tick'):lib.pow_hit()
  lib.tick(c['damage'] if tick in (c['hit_tick'],c['hit2_tick']) else 0,out)
  assert out[0]==bool(a[0]),(case,tick,'active',list(out),a.hex())
  if a[0]:
   flip=(a[5]>>3)&1;code=display[0]|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),C.c_int8(a[6]).value,C.c_int8(a[7]).value,a[18],a[20],a[12],a[21],a[10],code,a[5]&7,flip]
   assert list(out)[:13]==expected,(case,tick,list(out),expected)
  assert out[13]==((10,15,15,15)[c['profile']] if task!='0000' else 0),(case,tick,'score',task)
  assert out[14]==int(persist,16),(case,tick,'persistence',out[14],persist)
  count+=1
 report={'passed':True,'source_actor_ticks':count,'cases':len(ref['cases']),'source_splits':splits,'scope':'Four falling-seed families with two child body profiles each: proximity, gravity, terrain, facing, damage and death. Also checks source child construction. Native family integrated; shared global pool contention and full routes remain unverified.'}
 (ROOT/'reports/crawler-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
