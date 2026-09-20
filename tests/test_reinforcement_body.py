#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/reinforcement_body_oracle.json').read_text())
for key,path in [('trace_sha256','reference/reinforcement_body_oracle_events.txt'),('lua_sha256','tools/reinforcement_body_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definitions=[next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(2,pc)) for pc in (0x8344,0x9af6)]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/reinforcement_body.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''int full;int wall;u8 terrain(s16 x,s16 y){return y>=128 || (wall && x>=160 && x<176 && y>=wall)?3:0;}
 u8 player_contact(s16 x,s16 y,u8 w,u8 h){return 0;}
 void game_boss_clear(void){game.actors[0].active=0;}
 void setup(int px,int py,int w,int definition,int random,int face,int low,int pool_full) {
 game=(Game){0};game.p.x=px*256;game.p.y=py*256;wall=w;full=pool_full;game.mode=PLAY;game.spawned[0]=1;
 reinforcement_shots_reset();loot_random=random<<8;game.p.face=face;reinforcement_player_low=low;game.actors[0]=(Actor){.active=1,.x=128*256,.y=96*256,.def=definition};
 reinforcement_body_spawn(0);}
 void launch_snapshot(int *out){for(int i=0;i<6;i++){ReinforcementShot *p=&reinforcement_shots[i];out[i*3]=p->active;out[i*3+1]=p->x;out[i*3+2]=p->y;}}
 void tick(int damage,int *out) {
 Actor *a=&game.actors[0];ReinforcementState *s=&fighters[0];
 reinforcement_shots_reset();if(full)for(int i=0;i<24;i++)reinforcement_shots[i].active=1;if(damage && a->active)reinforcement_body_hit(0,damage);if(a->active)reinforcement_body_step(0);
 const AnimFrame *f=reinforcement_body_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),a->hp,a->life,s->mode,s->left,s->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,game.score,game.spawned[0],s->fraction,s->low};
 for(int i=0;i<15;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','loot.c','progress.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*15)();current=-1;count=0;launches=0
 for line in (ROOT/'reference/reinforcement_body_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  if line.startswith('LAUNCH|'):
   _,case,tick,raw=line.split('|');raw=bytes.fromhex(raw);actual=(C.c_int*18)();lib.launch_snapshot(actual);expected=[]
   for i in range(6):
    a=raw[i*32:i*32+32];expected.extend([bool(a[0]),int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True)])
   assert list(actual)==expected,(case,tick,'launch',list(actual),expected)
   launches+=1;continue
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['px'],c['py'],c['wall'],definitions[c['profile']],c['random'],c['face'],c['low'],c['full']);current=case
  lib.tick(c['damage'] if tick>=80 and tick%80==0 else 0,out)
  assert out[0]==(bool(a[0]) and clear=='0'),(case,tick,'active',list(out),a.hex(),clear)
  if out[0]:
   flip=(a[5]>>3)&1;code=(display[0]-flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),a[14],a[21],a[12],a[20],a[10],code,a[5]&7,flip]
   assert list(out)[:11]==expected,(case,tick,list(out),expected)
  assert out[11]==((20 if c['score']==0x20 else 80) if task=='REWARD' else 0),(case,tick,'score',task)
  if out[0]:assert list(out)[13:15]==[a[18],a[32]],(case,tick,'fraction/low-shot',list(out),a.hex())
  if clear=='0':assert out[12]==int(persist,16),(case,tick,'persistence')
  count+=1
 report={'passed':True,'source_body_ticks':count,'cases':len(ref['cases']),'six_part_launches':launches,'scope':'Both reinforcement fighter profiles: distance-weighted decisions, walking, jumps, gravity, attack phases, layered damage, recoil and rewards. Checks both available and full small-actor pools, plus all six projectile launch positions.'}
 (ROOT/'reports/reinforcement-body-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
