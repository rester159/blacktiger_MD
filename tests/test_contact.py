#!/usr/bin/env python3
"""Compiled shared contact geometry against source routine boundary observations."""
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reports/contact-oracle.json').read_text())
for name,path in [('trace_sha256','reference/contact_oracle_events.txt'),('lua_sha256','tools/contact_oracle.lua')]:
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[name]
defs=json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions']
shapes={}
for d in defs:
 c=d['constructor_evidence']['contact']
 if c and c['pool'] in (32,48):shapes[(c['pool'],c['half_width'],c['half_height'])]=d['id']
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','#include "hazard.h"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''int check(int def,int dx,int dy,int low,int jumping) {
 game=(Game){0};game.player_low=low && !jumping;game.p.x=(128+dx)*256;game.p.y=(96+dy)*256;
 game.actors[0]=(Actor){.active=1,.def=def,.x=128*256,.y=96*256};
 return actor_contact(0);}
''');(tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/hazard.c'),str(ROOT/'src/data.c'),str(tmp/'stubs.c'),'-o',str(tmp/'contact.dylib')],check=True)
 lib=C.CDLL(str(tmp/'contact.dylib'));count=0
 for line in (ROOT/'reference/contact_oracle_events.txt').read_text().splitlines():
  v=line.split('|')
  if v[0]!='CONTACT':continue
  case,player=map(int,v[1:]);c=ref['cases'][case]
  result=lib.check(shapes[(c['pool'],c['width'],c['height'])],c['dx'],c['dy'],c['low'],c['jumping'])
  assert bool(result)==(player==64),(case,c,player,result)
  count+=1
 report={'passed':True,'source_boundary_cases':count,'constructor_shapes':len(shapes),'scope':'Small/medium normal and crouched source contact bounds, including the jump override of low posture. Global scan cadence and screen wrapping remain separate.'}
 (ROOT/'reports/contact-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
