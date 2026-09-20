#!/usr/bin/env python3
"""Compare production native C state machines with original-ROM observations."""
import ctypes as C,json,subprocess,tempfile,re,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
source=Source()
reference=json.loads((ROOT/'reference/skeleton_oracle.json').read_text())
assert hashlib.sha256((ROOT/'reference/skeleton_oracle_events.txt').read_bytes()).hexdigest()==reference['trace_sha256']
assert hashlib.sha256((ROOT/'tools/skeleton_oracle.lua').read_bytes()).hexdigest()==reference['lua_sha256']
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp);(tmp/'genesis.h').write_text('/* Host-only types come from game.h. */\n')
 decl=(ROOT/'inc/assets.h').read_text();stubs=['#include "assets.h"','Game game;','static int wall;','u8 terrain(s16 x,s16 y) { return y>=160 || (wall && x>=160 && x<176 && y>=wall) ? 3 : 0; }','#include "'+str(ROOT/'src/skeleton.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int variant,int root,int px,int py,int y,int vy,int obstacle,int face) {
 unsigned char *b=(unsigned char*)&game;for(unsigned i=0;i<sizeof game;i++)b[i]=0;
 game.p.x=px*256;game.p.y=py*256;game.p.face=face;wall=obstacle;
 game.actors[0].active=1;game.actors[0].x=128*256;game.actors[0].y=y*256;
 for(unsigned i=0;i<66;i++)if(skeleton_kinds[i]==variant)game.actors[0].def=i;
 skeleton_reset();skeleton_spawn(0);skeletons[0].segment=skeleton_profiles[variant].roots[root];skeletons[0].body.vy=vy;
}
void tick(int damage,int *out) {
 if(damage)skeleton_hit(0,damage);
 skeleton_weapons_tick();if(game.actors[0].active)skeleton_step(0);
 Actor *a=&game.actors[0];SkeletonState *s=&skeletons[0];const AnimFrame *f=skeleton_frame(0);
 const AnimFrame *wf=animation_current(&s->weapon,skeleton_segments[s->weapon_segment].clip);
 int values[]={a->active,PX(a->x),PX(a->y),s->body.vx,s->body.vy,s->fraction,s->body.remaining,a->hp,s->left,s->attacking,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,s->weapon_active,s->wx,s->wy,s->weapon.vx,s->weapon.vy,s->weapon.remaining,wf?wf->code:-1,wf?wf->palette:-1,wf?wf->flip:-1,game.spawned[0]==2};
 for(unsigned i=0;i<23;i++)out[i]=values[i];
}
''')
 (tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/animation.c'),str(ROOT/'src/data.c'),str(tmp/'stubs.c'),'-o',str(tmp/'sk.dylib')],check=True)
 lib=C.CDLL(str(tmp/'sk.dylib'));out=(C.c_int*23)();current=-1;comparisons=0;weapon_frames=0
 for line in (ROOT/'reference/skeleton_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case_id,tick,a,display,weapon,persistence=line.split('|');case_id=int(case_id);tick=int(tick);a=bytes.fromhex(a);display=bytes.fromhex(display);c=reference['cases'][case_id]
  if current!=case_id:
   lib.setup(*[c[k] for k in ('variant','root_index','px','py','y','vy','wall','face')]);current=case_id
  damage=c['damage'] if tick==c['hit_tick'] else c['damage2'] if tick==c['hit2_tick'] else 0
  lib.tick(damage,out)
  def signed(v):return v if v<128 else v-256
  if a[0]:
   flip=(a[5]>>3)&1;code=(display[0]-flip)|((a[5]&224)<<3)
   expected=[1,int.from_bytes(a[1:3],'big',signed=True),int.from_bytes(a[3:5],'big',signed=True),signed(a[6]),signed(a[7]),a[18],a[10],a[21],a[20],a[36],code,a[5]&7,flip]
   assert list(out)[:13]==expected,(c['variant'],c['name'],tick,'body',list(out)[:13],expected,hex(int.from_bytes(a[30:32],'little')))
  else:assert out[0]==0,(c['variant'],c['name'],tick,'retirement')
  if weapon!='-':
   w=bytes.fromhex(weapon)
   if w[0]:
    expected=[1,int.from_bytes(w[1:3],'big',signed=True),int.from_bytes(w[3:5],'big',signed=True),signed(w[6]),signed(w[7]),w[10]]
    actual=list(out)[13:19];actual[-1]=actual[-1] or 1 # Native 0 is the source's initial one-tick load sentinel.
    assert actual==expected,(c['variant'],c['name'],tick,'weapon',list(out)[13:],expected)
    if out[18]:
     frame=source.read(0,int.from_bytes(w[30:32],'little'),5);expected_frame=[frame[1]|((frame[2]&224)<<3),frame[2]&7,(frame[2]>>3)&1]
     assert list(out)[19:22]==expected_frame,(c['name'],tick,'weapon graphics');weapon_frames+=1
   else:assert out[13]==0,(c['variant'],c['name'],tick,'weapon retirement')
  else:assert out[13]==0,(c['variant'],c['name'],tick,'unexpected weapon')
  assert out[22]==bool(int(persistence,16)&2),(c['variant'],c['name'],tick,'persistence')
  comparisons+=1
report={'passed':True,'cases':len(reference['cases']),'tick_comparisons':comparisons,'weapon_frame_comparisons':weapon_frames,'trace_sha256':reference['trace_sha256'],'scope':reference['scope']+' Excludes random loot and player hitbox geometry.'}
(ROOT/'reports/skeleton-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
