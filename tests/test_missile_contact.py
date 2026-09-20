#!/usr/bin/env python3
"""Normal small projectile contact through the original loader, including frame gating."""
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/missile_contact_oracle.json').read_text())
for key,path in [('trace_sha256','reference/missile_contact_oracle_events.txt'),('lua_sha256','tools/missile_contact_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text();stubs=['#include "assets.h"','#include "missile.h"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''int check(int kind,int parity,int dx,int dy) {
 game=(Game){0};game.frame=parity;game.p.x=(120+dx)*256;game.p.y=(88+dy)*256;
 missile_reset();missile_spawn(128,96,0,0,1,8,4);
 return kind?missile_hit_at(128+dx,96+dy,1,1):missile_player_contact(0);}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/animation.c'),str(ROOT/'src/missile.c'),str(ROOT/'src/data.c'),str(tmp/'stub.c'),'-o',str(tmp/'m.dylib')],check=True)
 lib=C.CDLL(str(tmp/'m.dylib'));count=0
 for line in (ROOT/'reference/missile_contact_oracle_events.txt').read_text().splitlines():
  if not line.startswith('CONTACT|'):continue
  _,case,hp,active,knife=line.split('|');c=ref['cases'][int(case)]
  result=bool(lib.check(c['kind'],c['parity'],c['dx'],c['dy']))
  assert result==(int(active)==64 if c['kind'] else int(hp)==3),(c,line,result)
  if c['kind'] and result:assert int(knife)!=128
  count+=1
 report={'passed':True,'source_pipeline_cases':count,'scope':'Normal small-projectile player contact and dagger contact: inclusive edges, source dimensions, and even-frame gate. Chain-hit/E906 shortcut, alternate player posture and complete player weapon scheduling remain separate.'}
 (ROOT/'reports/missile-contact-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
