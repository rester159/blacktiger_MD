#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
upper='--upper' in sys.argv
oracle_name='boss_upper_motion' if upper else 'boss_motion'
ref=json.loads((ROOT/('reference/'+oracle_name+'_oracle.json')).read_text())
for key,path in [('trace_sha256','reference/'+oracle_name+'_oracle_events.txt'),('lua_sha256','tools/'+oracle_name+'_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','static int wall;','u8 terrain(s16 x,s16 y){return y>=160 || (wall && x>=160 && x<176 && y>=wall)?3:0;}','#include "'+str(ROOT/'src/boss.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int variant,int root,int px,int y,int obstacle,int sample) {
 game=(Game){0};game.mode=PLAY;wall=obstacle;loot_random=sample*256;
 game.p.x=px*256;game.p.y=16*256;game.actors[0]=(Actor){.active=1,.x=128*256,.y=y*256};
 for(int i=0;i<66;i++)if(layered_boss_kinds[i]==variant+1)game.actors[0].def=i;
 game.actors[0].hp=variant?24:16;boss_spawn(0);bosses[0].segment=boss_roots[root];}
 void tick(int damage,int *out) {
 if(damage)boss_hit(0,damage);if(game.actors[0].active)boss_step(0);
 Actor *a=&game.actors[0];BossState *s=&bosses[0];const AnimFrame *f=boss_frame(0);
 int v[]={a->active,PX(a->x),PX(a->y),s->animation.vx,s->animation.vy,s->fraction,s->animation.remaining,s->left,a->life,s->vulnerable,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,s->worn,a->hp,game.mode==CLEAR};
 for(int i=0;i<16;i++)out[i]=v[i];}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 if upper:
  content=(tmp/'stub.c').read_text().replace('bosses[0].segment=boss_roots[root];','init(0,1,0);bosses[0].segment=boss_upper_roots[root];')
  (tmp/'stub.c').write_text(content)
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/animation.c'),str(ROOT/'src/loot.c'),str(ROOT/'src/data.c'),str(tmp/'stub.c'),'-o',str(tmp/'b.dylib')],check=True)
 lib=C.CDLL(str(tmp/'b.dylib'));out=(C.c_int*16)();current=-1;count=0;clear_ticks=[]
 for line in (ROOT/('reference/'+oracle_name+'_oracle_events.txt')).read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist=line.split('|');case=int(case);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=ref['cases'][case]
  if current!=case:lib.setup(c['variant'],c['root_index'],c['px'],c['y'],c['wall'],c['random']);current=case
  lib.tick(c['damage'] if c['hit_tick']==tick else c['damage2'] if tick in (c['hit2_tick'],c.get('hit3_tick',0),c.get('hit4_tick',0)) else 0,out)
  def signed(v):return v if v<128 else v-256
  assert out[15]==int(clear),(c['name'],tick,'clear',out[15],clear)
  if upper and not a[0]:
   assert out[0]==0,(c['name'],tick,'retire')
  elif not int(clear):
   flip=(a[5]>>3)&1;code=(display[0]-flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),signed(a[6]),signed(a[7]),a[18],a[10],a[20],a[21],int(not(a[12]&1)),code,a[5]&7,flip,a[33],a[14]]
   assert list(out)[:15]==expected,(c['variant'],c['name'],tick,list(out),expected)
  elif tick==1 or not any(v['case']==case for v in clear_ticks):clear_ticks.append(dict(case=case,tick=tick))
  count+=1
 report={'passed':True,'source_body_ticks':count,'clear_events':clear_ticks,'scope':('Upper components: proximity, weighted movement, fractional jumps/falls, wall/ground response, four damage layers and independent death/retirement.' if upper else 'Main controllers: proximity, weighted movement, wall/ground response, fractional jumps/falls, damage phase and death animation/clear callback. Complete clear presentation remains separate.')}
 (ROOT/('reports/'+oracle_name.replace('_','-')+'-tests.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
