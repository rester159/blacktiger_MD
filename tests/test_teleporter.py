#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/teleporter_oracle.json').read_text())
for key,path in [('trace_sha256','reference/teleporter_oracle_events.txt'),('lua_sha256','tools/teleporter_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definition=next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(1,0x92e6))
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/teleporter.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''u8 terrain(s16 x,s16 y){return 0;}
 void setup(int px,int sample) {
 game=(Game){0};game.p.x=px*256;game.p.y=120*256;game.mode=PLAY;game.spawned[0]=1;
 loot_random=sample*256;game.actors[0]=(Actor){.active=1,.x=128*256,.y=96*256,.def='''+str(definition)+'''};
 teleporter_spawn(0);}
 void tick(int damage,int *out) {
 Actor *a=&game.actors[0];TeleporterState *s=&teleporters[0];
 if(damage && a->active)teleporter_hit(0,damage);if(a->active)teleporter_step(0);
 const AnimFrame *f=teleporter_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),a->life,s->left,s->phase,s->cycles,s->mode,s->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,game.score,game.spawned[0]};
 for(int i=0;i<14;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','loot.c','progress.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*14)();current=-1;count=0
 for line in (ROOT/'reference/teleporter_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['px'],c['random']);current=case
  lib.tick(c['damage'] if tick>=80 and tick%100==80 else 0,out)
  assert out[0]==bool(a[0]),(case,tick,'active')
  if a[0]:
   flip=(a[5]>>3)&1;code=(display[0]-flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),a[21],a[20],a[32],a[33],a[12],a[10],code,a[5]&7,flip]
   assert list(out)[:12]==expected,(case,tick,list(out),expected)
  assert out[12]==(100 if task=='0540' else 0),(case,tick,'score',task)
  assert out[13]==int(persist,16)
  count+=1
 report={'passed':True,'source_body_ticks':count,'cases':len(ref['cases']),'scope':'Teleporter body phases, facing, relocation, attack-cycle retirement, custom damage reduction and 100-point defeat reward. Recurring constructor and six-part attack integration remain pending.'}
 (ROOT/'reports/teleporter-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
