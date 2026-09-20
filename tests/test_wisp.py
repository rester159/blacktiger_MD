#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reports/wisp-oracle.json').read_text())
for name,path in [('trace_sha256','reference/wisp_oracle_events.txt'),('lua_sha256','tools/wisp_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[name]
definition=next(d['id'] for d in json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions'] if d['bank']==2 and d['address']==0xa6f8)
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','#include "loot.h"','#include "'+str(ROOT/'src/wisp.c')+'"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int random){game=(Game){0};loot_new();loot_random=random*256;game.actors[0]=(Actor){.active=1,.def=%d,.x=128*256,.y=96*256};wisp_spawn(0);}
 void tick(int y,int hit){game.p.y=y*256;if(hit)wisp_hit(0);wisp_step(0);}
 int x(void){return PX(game.actors[0].x);}int y(void){return PX(game.actors[0].y);}
 int vx(void){return wisps[0].animation.vx;}int vy(void){return wisps[0].animation.vy;}
 int remaining(void){return wisps[0].animation.remaining;}int health(void){return game.actors[0].hp;}
 int state(void){return game.actors[0].state;}int score(void){return game.score;}int kills(void){return game.kills;}
 int graphic(void){const AnimFrame *f=wisp_frame(0);return f?f->code:-1;}
'''%definition);(tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/s) for s in ('loot.c','animation.c','data.c')],str(tmp/'stubs.c'),'-o',str(tmp/'wisp.dylib')],check=True)
 lib=C.CDLL(str(tmp/'wisp.dylib'));ticks=0
 for line in (ROOT/'reference/wisp_oracle_events.txt').read_text().splitlines():
  v=line.split('|')
  if v[0]!='TICK':continue
  case,tick=map(int,v[1:3]);c=ref['cases'][case];a=bytes.fromhex(v[3]);display=bytes.fromhex(v[4])
  if tick==1:lib.setup(c['random'])
  lib.tick(96 if c['switch'] and tick>120 else c['y'],c['hit'] and tick in (90,170))
  assert a[0] in (64,128),(case,tick,'source actor left viewport')
  assert (lib.x(),lib.y())==(int.from_bytes(a[1:3],'big'),int.from_bytes(a[3:5],'big')),(case,tick,'position',lib.x(),lib.y(),a.hex())
  signed=lambda n:n if n<128 else n-256
  assert (lib.vx(),lib.vy(),lib.remaining())==(signed(a[6]),signed(a[7]),a[10]),(case,tick,'velocity/countdown')
  assert lib.graphic()==display[0]|((display[1]&224)<<3),(case,tick,'graphic')
  assert lib.health()==a[14]==1 and bool(lib.state())==(a[0]==64)
  assert lib.kills()==lib.score()==0 and int(v[5])==1
  ticks+=1
report={'passed':True,'source_actor_ticks':ticks,'scope':'Eight controlled cases: both random movement branches, vertical proximity/transition, repeated hits, animation/velocity/position, health and no death reward. Generic player damage and viewport retirement remain separate.'}
(ROOT/'reports/wisp-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
