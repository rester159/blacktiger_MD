#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
source=Source()
ref=json.loads((ROOT/'reference/thrower_oracle.json').read_text())
for key,path in [('trace_sha256','reference/thrower_oracle_events.txt'),('lua_sha256','tools/thrower_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','static int wall;','u8 terrain(s16 x,s16 y){return y>=160 || (wall && x>=160 && x<176 && y>=wall)?3:0;}','#include "'+str(ROOT/'src/zombie.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int root,int px,int y,int obstacle,int sample) {
 game=(Game){0};wall=obstacle;missile_reset();loot_random=sample*256;game.p.x=px*256;game.p.y=16*256;
 game.actors[0]=(Actor){.active=1,.x=128*256,.y=y*256};
 for(int i=0;i<66;i++)if(zombie_kinds[i]==2)game.actors[0].def=i;
 zombie_spawn(0);zombies[0].segment=thrower_roots[root];}
 void spawn_setup(int cap,int sample) {
 game=(Game){0};wall=0;zombie_reset();loot_random=sample*512;
 for(int i=0;i<cap;i++){game.actors[i].active=1;for(int d=0;d<66;d++)if(zombie_kinds[d]==2)game.actors[i].def=d;}
 }
 void spawn_attempt(int *out) {s16 x=0,y=0;out[0]=zombie_prepare_variant(0,1,&x,&y);out[1]=x;out[2]=y;out[3]=spawn_delay[0];}
 void projectile(int *out) {
 Missile *m=&missiles[0];const AnimFrame *f=missile_frame(0);
 int v[]={m->active,m->x,m->y,m->animation.vx,m->animation.vy,m->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1};
 for(int i=0;i<9;i++)out[i]=v[i];
 }
 void tick(int damage,int shot_hit,int *out) {
 if(damage)zombie_hit(0,damage);if(shot_hit)missile_hit(0,1);missile_tick();if(game.actors[0].active)zombie_step(0);
 Actor *a=&game.actors[0];ZombieState *s=&zombies[0];const AnimFrame *f=zombie_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),s->animation.vx,s->animation.vy,s->fraction,s->animation.remaining,s->left,s->cycles,s->vulnerable,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,game.spawned[0],s->thrown,a->hp};
 for(int i=0;i<16;i++)out[i]=v[i];}
''')
 (tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/sentry.c'),str(ROOT/'src/animation.c'),str(ROOT/'src/loot.c'),str(ROOT/'src/missile.c'),str(ROOT/'src/data.c'),str(ROOT/'src/progress.c'),str(tmp/'stub.c'),'-o',str(tmp/'z.dylib')],check=True)
 lib=C.CDLL(str(tmp/'z.dylib'));out=(C.c_int*32)();current=-1;count=0
 for line in (ROOT/'reference/thrower_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE' or line.startswith('SPAWN|'):break
  _,case,tick,a,display,small,persist=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['root_index'],c['px'],c['y'],c['wall'],c['random']);current=case
  lib.tick(c['damage'] if c['hit_tick']==tick else c['damage2'] if c['hit2_tick']==tick else 0,int(tick==c['shot_hit']),out)
  def signed(v):return v if v<128 else v-256
  if a[0]:
   flip=(a[5]>>3)&1;code=(display[0]-flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),signed(a[6]),signed(a[7]),a[18],a[10],a[20],a[32],int(not(a[12]&2)),code,a[5]&7,flip]
   assert list(out)[:13]==expected,(c['name'],tick,list(out),expected)
  else:assert not out[0],(c['name'],tick,'retirement')
  assert out[13]!=2 and not(int(persist,16)&2),(c['name'],tick,'recurring persistence',out[13],persist)
  assert out[14]==a[33] and out[15]==a[14],(c['name'],tick,'throw/health',out[14],out[15],a[33],a[14])
  shot=next((bytes.fromhex(e.split(':')[1]) for e in filter(None,small.split(',')) if bytes.fromhex(e.split(':')[1])[13]&127==0),None)
  lib.projectile(out)
  if shot:
   expect=[1,int.from_bytes(shot[1:3],'big',signed=True),int.from_bytes(shot[3:5],'big',signed=True),signed(shot[6]),signed(shot[7]),shot[10]]
   actual=list(out)[:6];actual[5]=actual[5] or 1
   assert actual==expect,(c['name'],tick,'projectile',actual,expect)
   if out[5]:
    f=source.read(0,int.from_bytes(shot[30:32],'little'),5)
    assert list(out)[6:9]==[f[1]|((f[2]&224)<<3),f[2]&7,(f[2]>>3)&1],(c['name'],tick,'projectile graphics')
  else:assert not out[0],(c['name'],tick,'unexpected projectile')
  count+=1
 spawn_ref=json.loads((ROOT/'reference/thrower_spawn_oracle.json').read_text())
 for key,path in [('trace_sha256','reference/thrower_spawn_oracle_events.txt'),('lua_sha256','tools/thrower_spawn_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==spawn_ref[key]
 attempts=0
 for line in (ROOT/'reference/thrower_spawn_oracle_events.txt').read_text().splitlines():
  v=line.split('|')
  if v[0]!='SPAWN':continue
  sample,cap,attempt,active,x,y,delay=map(int,v[1:])
  if attempt==1:lib.spawn_setup(cap,sample)
  lib.spawn_attempt(out)
  assert (bool(out[0]),out[3])==(bool(active),delay),(sample,cap,attempt,list(out))
  if active:assert list(out)[1:3]==[x,y],(sample,cap,attempt,list(out),x,y)
  attempts+=1
 report={'constructor_attempts':attempts,'passed':True,'source_actor_ticks':count,'scope':'Second recurring walker: emergence, walking, throw selection, post-throw jumps, falling, nonfatal/fatal damage and independently damageable projectile trajectories/lifetimes. Native pool capacity and player projectile hitbox remain adaptations.'}
 (ROOT/'reports/thrower-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
