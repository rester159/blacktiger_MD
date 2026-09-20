#!/usr/bin/env python3
"""Compare the native layer transition with original boss damage callbacks."""
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/boss_layers_oracle.json').read_text())
for key,path in [('trace_sha256','reference/boss_layers_oracle_events.txt'),('lua_sha256','tools/boss_layers_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
defs=json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions']
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text();stubs=['#include "assets.h"','#include "boss.h"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int def,int hp){game=(Game){0};game.actors[0].def=def;game.actors[0].hp=hp;game.actors[0].active=1;boss_spawn(0);}
 int hit(int damage){Actor *a=&game.actors[0];if(a->hp>damage){a->hp-=damage;return 0;}return !boss_break_layer(a);}
 int hp(void){return game.actors[0].hp;} int layers(void){return game.actors[0].life;}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/boss.c'),str(ROOT/'src/data.c'),str(tmp/'stub.c'),'-o',str(tmp/'b.dylib')],check=True)
 lib=C.CDLL(str(tmp/'b.dylib'));current=-1;count=0
 for line in (ROOT/'reference/boss_layers_oracle_events.txt').read_text().splitlines():
  if not line.startswith('HIT|'):continue
  _,case,hit,hp,layers,active,clear=line.split('|');case=int(case);hit=int(hit);c=ref['cases'][case]
  if current!=case:
   variant=c['template']==0xa28b;d=next(d for d in defs if d['bank']==4 and d['address']==(0x9f16 if variant else 0x9eb1));lib.setup(d['id'],24 if variant else 16);current=case
  dead=lib.hit(c['damage'][hit-1])
  assert (lib.hp(),lib.layers(),dead)==(int(hp),int(layers),int(clear)),(c,hit,hp,layers,clear,lib.hp(),lib.layers(),dead)
  assert (int(active)==64)==bool(dead)
  count+=1
 report={'passed':True,'source_hit_callbacks':count,'scope':'Two boss damage layers, nonfatal hits, exact breaks and discarded excess damage. This does not validate multi-part actors, movement, vulnerability timing or round-clear presentation.'}
 (ROOT/'reports/boss-layer-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
