#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/edge_actor_oracle.json').read_text())
for key,path in [('trace_sha256','reference/edge_actor_oracle_events.txt'),('lua_sha256','tools/edge_actor_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definitions=[next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(4,pc)) for pc in (0xa4d0,)]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/edge_actor.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''int full;int wall;u8 terrain(s16 x,s16 y){return y>=128 || (wall && x>=160 && x<176 && y>=wall)?3:0;}
 u8 player_contact(s16 x,s16 y,u8 w,u8 h){return 0;}
 void game_boss_clear(void){game.actors[0].active=0;}
 void setup(int px,int py,int w,int definition,int random,int face,int pool_full) {
 game=(Game){0};game.p.x=px*256;game.p.y=py*256;wall=w;full=pool_full;game.p.face=face;game.mode=PLAY;game.spawned[0]=1;
 edge_shots_reset();loot_random=random<<8;game.actors[0]=(Actor){.active=1,.x=128*256,.y=96*256,.def=definition};
 edge_actor_spawn(0);}
 int contact_frame_kept(void){EdgeState *s=&edge_actors[0];s->mode=8;s->contact=37;s->segment=edge_roots[12];animation_reset(&s->animation);edge_actor_step(0);
 const AnimFrame *before=edge_actor_frame(0);if(!before)return 0;edge_actor_contact(0);if(edge_actor_frame(0)!=before)return 0;edge_actor_step(0);return !s->contact && edge_actor_frame(0)!=0;}
 void tick(int damage,int *out) {
 Actor *a=&game.actors[0];EdgeState *s=&edge_actors[0];
 edge_shots_reset();if(full)for(int i=0;i<24;i++)edge_shots[i].active=1;if(damage && a->active)edge_actor_hit(0,damage);if(a->active)edge_actor_step(0);
 const AnimFrame *f=edge_actor_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),a->hp,a->life,s->mode,s->left,s->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,game.score,game.spawned[0],s->fraction,s->variant,s->fired,s->contact};
 for(int i=0;i<17;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','loot.c','progress.c','sentry.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*17)();current=-1;count=0
 for line in (ROOT/'reference/edge_actor_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist,task=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['px'],c['py'],c['wall'],definitions[0],c['random'],c['face'],c['full']);current=case
  lib.tick(c['damage'] if tick>=80 and tick%80==0 else 0,out)
  assert out[0]==(bool(a[0]) and clear=='0'),(case,tick,'active',list(out),a.hex(),clear)
  if out[0]:
   flip=(a[5]>>3)&1;code=(display[0]-flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),a[14],a[21],a[12],a[20],a[10],code,a[5]&7,flip]
   assert list(out)[:11]==expected,(case,tick,list(out),expected)
  assert out[11]==(100 if task=='REWARD' else 0),(case,tick,'score',task)
  if out[0]:assert list(out)[13:17]==[a[18],a[33],a[32],a[13]],(case,tick,'fraction/weapon-link',list(out),a.hex())
  if clear=='0':assert out[12]==int(persist,16),(case,tick,'persistence')
  count+=1
 lib.setup(128,96,0,definitions[0],0,0,0);assert lib.contact_frame_kept(), 'Contact must preserve the displayed frame until the next update'
 report={'contact_frame_retained':True,'passed':True,'source_body_ticks':count,'cases':len(ref['cases']),'scope':'Edge-entry caster: weighted jumps, dash/strike transitions, fractional gravity, attack phases, layers, relocation, recoil and rewards. Available/full projectile allocation.'}
 (ROOT/'reports/edge-actor-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
