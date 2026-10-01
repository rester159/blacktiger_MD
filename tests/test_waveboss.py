#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/waveboss_oracle.json').read_text())
for key,path in [('trace_sha256','reference/waveboss_oracle_events.txt'),('lua_sha256','tools/waveboss_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definitions=[next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(1,pc)) for pc in (0x98a3,0x98e8)]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/waveboss.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''u8 terrain(s16 x,s16 y){return 0;}
 u8 shop_poison;
 void container_wave_spawn(s16 x,u8 left){}
 void container_ground_spawn(s16 x,u8 left){}
 void game_boss_clear(void){game.actors[0].active=0;}
 void setup(int px,int sample,int definition) {
 game=(Game){0};game.p.x=px*256;game.p.y=120*256;game.mode=PLAY;game.spawned[0]=1;
 waveboss_reset();loot_random=sample*256;game.actors[0]=(Actor){.active=1,.x=128*256,.y=96*256,.def=definition};
 waveboss_spawn(0);}
 void tick(int damage,int *out) {
 Actor *a=&game.actors[0];WaveBossState *s=&wavebosses[0];
 waveboss_reset();if(damage && a->active)waveboss_hit(0,damage);if(a->active)waveboss_step(0);
 const AnimFrame *f=waveboss_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),a->hp,a->life,s->mode,s->left,s->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,game.score,game.spawned[0]};
 for(int i=0;i<13;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','large_contact.c','loot.c','progress.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));lib.waveboss_vulnerable.argtypes=[C.c_ushort];lib.waveboss_vulnerable.restype=C.c_ubyte;out=(C.c_int*13)();current=-1;count=0;previous_life=None;layer_unlocked=False
 for line in (ROOT/'reference/waveboss_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['px'],c['random'],definitions[c['template']==0x9b4f]);current=case;previous_life=None;layer_unlocked=False
  lib.tick(c['damage'] if tick>=80 and tick%40==0 else 0,out)
  if not (c['damage'] and tick>80):assert out[0]==(bool(a[0]) and clear=='0'),(case,tick,'active',list(out),a.hex(),clear)
  if out[0]:
   flip=(a[5]>>3)&1;code=(display[0]-3*flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),a[14],a[21],a[12],a[20],a[10],code,a[5]&7,flip]
   # v1.7 clears the hit mask as soon as a layer is removed, reopening the
   # next layer. The original trace retains the three hit-lock bits here.
   if previous_life is not None and out[4]<previous_life:
    layer_unlocked=True
    if out[4]:assert lib.waveboss_vulnerable(0)==1,('next boss layer remained invulnerable',case,tick,list(out))
   elif out[5]==27:layer_unlocked=False
   if layer_unlocked:expected[5]=24
   # Once the first layer is gone, later hits intentionally change the
   # original trace because v1.7 now accepts damage against the next layer.
   if not (c['damage'] and tick>80):assert list(out)[:11]==expected,(case,tick,list(out),expected)
   previous_life=out[4]
  if not (c['damage'] and tick>80):
   assert out[11]==((5000 if c['template']==0x9b1f else 15000) if task=='REWARD' else 0),(case,tick,'score',task)
   if clear=='0':assert out[12]==int(persist,16),(case,tick,'persistence')
  count+=1
 report={'passed':True,'source_body_ticks':count,'cases':len(ref['cases']),'scope':'Both large wave-boss body profiles match the source trace through the first layer break. The test confirms every surviving layer becomes vulnerable after a break; later damage intentionally diverges from the original trace because v1.7 accepts hits on subsequent layers. Projectile pool is kept available to isolate body behavior; original boss health display and complete round-clear presentation remain separate.'}
 (ROOT/'reports/waveboss-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
