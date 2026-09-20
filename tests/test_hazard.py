#!/usr/bin/env python3
"""Normal player contact edges and armor/invulnerability bypass versus source ROM."""
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reports/hazard-oracle.json').read_text())
for name,path in [('trace_sha256','reference/hazard_oracle_events.txt'),('lua_sha256','tools/hazard_oracle.lua')]:
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[name]
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','#include "hazard.h"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''int check(int dx,int dy,int armor,int invincible) {
 game=(Game){0}; game.mode=PLAY; game.p.hp=4;game.p.lives=3;game.p.armor=armor;game.p.invincible=invincible;
 game.p.x=(120+dx)*256;game.p.y=(88+dy)*256;game.actors[0]=(Actor){.active=1,.x=128*256,.y=96*256};
 hazard_step(0);return game.mode==DEAD;}
 int armor(void){return game.p.armor;} int active(void){return game.actors[0].active;}
 int lives(void){return game.p.lives;} int health(void){return game.p.hp;}
''');(tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/hazard.c'),str(ROOT/'src/player_death.c'),str(ROOT/'src/data.c'),str(tmp/'stubs.c'),'-o',str(tmp/'hazard.dylib')],check=True)
 lib=C.CDLL(str(tmp/'hazard.dylib'));count=0;deaths=0
 for line in (ROOT/'reference/hazard_oracle_events.txt').read_text().splitlines():
  v=line.split('|')
  if v[0]!='CONTACT':continue
  case,player,phase,armor,active,persist=map(int,v[1:]);c=ref['cases'][case]
  dead=lib.check(c['dx'],c['dy'],c['armor'],c['invincible'])
  assert bool(dead)==(player==64),(case,c,player)
  assert (lib.armor(),bool(lib.active()),lib.lives())==(armor,bool(active),3)
  assert phase==dead and lib.health()==(0 if dead else 4)
  count+=1;deaths+=dead
 report={'passed':True,'source_contact_cases':count,'lethal_cases':deaths,'scope':'Normal player bounds, inclusive edges, armor/invulnerability bypass, no immediate life decrement, persistent stationary hazard. Alternate player contact posture and death presentation remain unverified.'}
 (ROOT/'reports/hazard-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
