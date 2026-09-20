#!/usr/bin/env python3
"""Production sentry and reusable aiming code versus original ROM observations."""
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reports/sentry-oracle.json').read_text())
assert hashlib.sha256((ROOT/'reference/sentry_oracle_events.txt').read_bytes()).hexdigest()==ref['trace_sha256']
assert hashlib.sha256((ROOT/'tools/sentry_oracle.lua').read_bytes()).hexdigest()==ref['lua_sha256']
definition=next(d['id'] for d in json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions'] if d['bank']==2 and d['address']==0xb67f)
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','#include "loot.h"','#include "sentry.h"','#include "'+str(ROOT/'src/sentry.c')+'"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int x,int y,int random) {game=(Game){0};loot_new();loot_random=random*256;game.p.x=x*256;game.p.y=y*256;game.actors[0]=(Actor){.active=1,.def=%d,.x=128*256,.y=96*256};sentry_spawn(0);}
 int remaining(void){return sentries[0].animation.remaining;} int direction(void){return sentries[0].direction;}
 int active(void){return game.actors[0].active;} int hp(void){return game.actors[0].hp;}
 int persistent(void){return game.spawned[0];} int score(void){return game.score;}
 int graphic(void){const AnimFrame *f=sentry_frame(0);return f?f->code:-1;}
'''%definition);(tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/s) for s in ('loot.c','animation.c','data.c')],str(ROOT/'src/progress.c'),str(tmp/'stubs.c'),'-o',str(tmp/'sentry.dylib')],check=True)
 lib=C.CDLL(str(tmp/'sentry.dylib'));counts={}
 for line in (ROOT/'reference/sentry_oracle_events.txt').read_text().splitlines():
  v=line.split('|');counts[v[0]]=counts.get(v[0],0)+1
  if v[0]=='AIM':assert lib.aim_direction(*map(int,v[1:5]))==int(v[5]),v
  if v[0]=='TICK':
   case,tick=map(int,v[1:3]);a=bytes.fromhex(v[3]);display=bytes.fromhex(v[4])
   if tick==1:
    c=ref['cases'][case];lib.setup(c['x'],c['y'],c['random'])
   if tick in (65,75):lib.sentry_hit(0,1)
   if lib.active():lib.sentry_step(0)
   assert bool(lib.active())==bool(a[0]),(case,tick,'active')
   assert lib.hp()==a[14],(case,tick,'hp',lib.hp(),a[14])
   assert bool(lib.persistent())==bool(int(v[5],16)&2),(case,tick,'persistence')
   if a[0]:
    assert lib.remaining()==a[10],(case,tick,'countdown')
    assert lib.direction()==a[22],(case,tick,'direction')
   if a[0]:assert lib.graphic()==display[0]|((display[1]&224)<<3),(case,tick,'graphic',lib.graphic(),display.hex())
 report={'passed':True,'aim_observations':counts['AIM'],'actor_ticks':counts['TICK'],'cases':len(ref['cases']),'scope':'Original aiming, stationary facing/blink cycles, nonfatal/fatal damage, persistent death and retirement. Exact contact bounds remain provisional.'}
 (ROOT/'reports/sentry-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
