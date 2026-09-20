#!/usr/bin/env python3
"""Compare native shared locomotion to the original bank-seven routine."""
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/player_motion_oracle.json').read_text())
for key,path in [('trace_sha256','reference/player_motion_oracle_events.txt'),('lua_sha256','tools/player_motion_oracle.lua')]:
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder)
 (tmp/'stub.c').write_text('''#include "player_motion.h"
 static PlayerMotion p;static PlayerAttack a;static int attacking,tier;static int geometry,reversed;
 u8 terrain(s16 x,s16 y) {
 x=(u16)x&2032;y=(u16)y&1008;
 if ((geometry==5 || geometry==6) && x==400 && y>=320 && y<432) return 1;
 if (geometry==2 && x==416 && y>=384) return 3;
 if (geometry==3 && x==416 && y>=400) return 2;
 if (geometry==4 && y==352) return 3;
 if (y>=432 && !(geometry==1 && x>=416) && !(geometry==6 && x==400)) return 3;
 return 0;
 }
 void setup(int g,int reverse,int x,int y,int ladder,int falling,int attack,int t) {
 attacking=attack;tier=t;a=(PlayerAttack){0};
 geometry=g;reversed=reverse;p=(PlayerMotion){.scroll_x=x-128,.scroll_y=y-144,.screen_x=128,.screen_y=144,.ladder=ladder,.falling=falling};
 }
 void tick(int input,int hit,int *out) {
 if(hit)player_attack_hit(&a);
 if(attacking)player_control_step(&p,&a,input,reversed,tier);else player_motion_step(&p,input,reversed);
 int v[]={p.scroll_x,p.scroll_y,p.screen_x,p.screen_y,p.jump_origin,p.vx,p.vy,p.fraction,p.subtick,p.pose,p.jumping,p.jump_request,p.direction,p.redirected,p.camera_return,p.below_origin,p.falling,p.ladder,p.low,p.frame,p.selector,p.previous,p.idle,p.jump_history,p.screen_motion};
 for(int i=0;i<25;i++)out[i]=v[i];
 }
 void attack_snapshot(int *out) {
 int v[]={a.active,a.request,a.launch,a.selector,a.reach,a.damage,a.counter,a.holding,a.hit,a.links,a.count};
 for(int i=0;i<11;i++)out[i]=v[i];
 }

 ''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/player_motion.c'),str(tmp/'stub.c'),'-o',str(tmp/'motion.dylib')],check=True)
 lib=C.CDLL(str(tmp/'motion.dylib'));out=(C.c_int*25)();current=-1;count=0
 names=['scroll_x','scroll_y','screen_x','screen_y','jump_origin','vx','vy','fraction','subtick','pose','jumping','jump_request','direction','redirected','camera_return','below_origin','falling','ladder','low','frame','selector','previous','idle','jump_history','screen_motion']
 for line in (ROOT/'reference/player_motion_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  if line.startswith('ATTACK|'):
   _,case,tick,raw,counters,slots=line.split('|');raw=bytes.fromhex(raw);counters=bytes.fromhex(counters);slots=bytes.fromhex(slots)
   actual=(C.c_int*11)();lib.attack_snapshot(actual)
   expected=[raw[0],raw[1],raw[7],raw[3],raw[2],a[13],counters[0],counters[3],int(extra[5]),counters[4],sum(bool(slots[i*5]) for i in range(6))]
   assert list(actual)==expected,(case,tick,'attack',list(actual),expected)
   for i in range(actual[10]):
    at=i*5;left=(actual[3]+1)&4
    assert int.from_bytes(slots[at+1:at+3],'big',signed=True)==(-16-16*i if left else 32+16*i),(case,tick,i,'chain X')
    assert slots[at+4]==(0x6f+ref['cases'][int(case)]['tier'] if i==actual[10]-1 else 1),(case,tick,i,'chain code')
    offset=6 if a[18] or a[25] or not (extra[0]&3) else 14
    assert slots[at+3]==(a[4]+offset)&255,(case,tick,i,'chain Y')
   continue
  _,case,tick,a,scroll,extra,screen=line.split('|');case=int(case);tick=int(tick)
  a=bytes.fromhex(a);scroll=bytes.fromhex(scroll);extra=bytes.fromhex(extra);c=ref['cases'][case]
  if current!=case:
   lib.setup(*[c[k] for k in ('geometry','reversed','x','y','ladder','falling')],c.get('attack',0),c.get('tier',0));current=case
  lib.tick(c['pattern'][min(tick-1,len(c['pattern'])-1)],int(tick==c.get('hit',0)),out)
  expected=[int.from_bytes(scroll[0:2],'big'),int.from_bytes(scroll[2:4],'big'),int.from_bytes(a[1:3],'big'),int.from_bytes(a[3:5],'big'),int.from_bytes(extra[18:20],'little'),int.from_bytes(a[6:7],signed=True),int.from_bytes(a[7:8],signed=True),a[10],a[15],a[17],*a[18:26],a[38],a[39],extra[0],extra[1],extra[6],extra[2],int(screen,16)]
  assert list(out)==expected,(case,tick,c,[(n,v,e) for n,v,e in zip(names,out,expected) if v!=e])
  count+=1
 report=dict(passed=True,source_ticks=count,cases=len(ref['cases']),scope='Source bank 7 input decode, walking, crouching, ladders, jump variants, air steering, falling, landing and logical camera integration. Includes attack windup, all five chain reaches, hold/release, impact shortening and jumping attacks; excludes damage dispatch, global camera clamps and sound dispatch.')
 (ROOT/'reports/player-motion-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
