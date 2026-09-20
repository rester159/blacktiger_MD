#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/dragon_oracle.json').read_text())
for key,path in [('trace_sha256','reference/dragon_oracle_events.txt'),('lua_sha256','tools/dragon_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definitions=[next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(3,pc)) for pc in (0x8000,0x991d,0x9b24)]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/dragon.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''u8 terrain(s16 x,s16 y){return 0;}
 u8 shop_poison;
 void container_wave_spawn(s16 x,u8 left){}
 void container_ground_spawn(s16 x,u8 left){}
 void game_boss_clear(void){game.actors[0].active=0;}
 int shot[6],full;
 void launch(u8 kind,u8 direction,s16 x,s16 y,u8 profile,u8 left){if(!full){shot[0]=1;shot[1]=kind;shot[2]=direction;shot[3]=x;shot[4]=y;shot[5]=left;}}
 void snapshot(int *out){for(int i=0;i<6;i++)out[i]=shot[i];}
 void setup(int px,int sample,int definition,int profile,int pool_full) {
 game=(Game){0};game.p.x=px*256;game.p.y=120*256;game.mode=PLAY;game.spawned[0]=1;
 full=pool_full;loot_random=sample*256;game.actors[0]=(Actor){.active=1,.x=128*256,.y=96*256,.def=definition};
 dragon_spawn(0,profile);}
 void tick(int damage,int *out) {
 Actor *a=&game.actors[0];DragonState *s=&dragons[0];
 for(int i=0;i<6;i++)shot[i]=0;if(damage && a->active)dragon_hit(0,damage);if(a->active)dragon_step(0,launch);
 const AnimFrame *f=dragon_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),a->hp,a->life,s->mode,s->left,s->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,game.score,game.spawned[0],s->engaged,s->alternate,s->direction,s->recovery,s->weak_x};
 for(int i=0;i<18;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','large_contact.c','sentry.c','loot.c','progress.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*18)();current=-1;count=0;launches=0;cleared=set();rewarded=set();pending_launch=None
 for line in (ROOT/'reference/dragon_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  if line.startswith('LAUNCH|'):
   _,case,tick,raw=line.split('|');raw=bytes.fromhex(raw);actual=(C.c_int*6)();lib.snapshot(actual)
   assert actual[0]==1,(case,tick,'missing launch')
   assert list(actual)[3:5]==[int.from_bytes(raw[1:3],'big',signed=True),int.from_bytes(raw[3:5],'big',signed=True)],(case,tick,'launch position',list(actual),raw.hex())
   assert actual[1]==(raw[12]==11),(case,tick,'launch type',list(actual),raw.hex())
   pending_launch=None;launches+=1;continue
  assert pending_launch is None,('unexpected native launch',pending_launch)
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['px'],c['random'],definitions[c['profile']],c['profile'],c['full']);current=case
  lib.tick(c['damage'] if tick>=80 and tick%40==0 else 0,out)
  shot=(C.c_int*6)();lib.snapshot(shot)
  if shot[0]:pending_launch=(case,tick,list(shot))
  if clear=='1':cleared.add(c['profile'])
  if task=='REWARD':rewarded.add(c['profile'])
  assert out[0]==(bool(a[0]) and clear=='0'),(case,tick,'active',list(out),a.hex(),clear)
  if out[0]:
   flip=(a[5]>>3)&1;code=(display[0]-7*flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),a[14],a[21],a[12],a[20],a[10],code,a[5]&7,flip]
   assert list(out)[:11]==expected,(case,tick,list(out),expected)
  assert out[11]==(1000 if task=='REWARD' else 0),(case,tick,'score',task)
  if out[0]:assert list(out)[13:18]==[a[36],a[37],a[22],a[39],int.from_bytes(a[32:33],'big',signed=True)],(case,tick,'body state',list(out),a.hex())
  if clear=='0':assert out[12]==int(persist,16),(case,tick,'persistence')
  count+=1
 assert cleared==rewarded=={0,1,2},(cleared,rewarded)
 report=dict(passed=True,cleared_profiles=sorted(cleared),source_body_ticks=count,cases=len(ref['cases']),source_launches=launches,scope='Three dragon body profiles: movement, aiming, animation, layers, reward, retirement and projectile launch coordinates with available/full pools. Projectile behavior, collision, presentation and cartridge integration remain separate.')
 (ROOT/'reports/dragon-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
