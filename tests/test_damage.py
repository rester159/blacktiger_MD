#!/usr/bin/env python3
"""Native ordinary damage dispatch versus original armor/health routine."""
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reports/damage-oracle.json').read_text())
for key,path in [('trace_sha256','reference/damage_oracle_events.txt'),('lua_sha256','tools/damage_oracle.lua')]:
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder)
 (tmp/'stub.c').write_text('''#include "damage.h"
 Game game;
 void check(int hp,int armor,int damage,int invincible) {
 game=(Game){0};game.mode=PLAY;game.p.hp=hp;game.p.armor=armor;game.p.invincible=invincible;
 game.p.vy=123;game.p.climb=1;player_hurt(damage);}
 int hp(void){return game.p.hp;} int armor(void){return game.p.armor;}
 int timer(void){return game.p.invincible;} int dead(void){return game.mode==DEAD;}
 int motion(void){return game.p.vy==123 && game.p.climb==1;}
''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/damage.c'),str(tmp/'stub.c'),'-o',str(tmp/'damage.dylib')],check=True)
 lib=C.CDLL(str(tmp/'damage.dylib'));count=0
 for line in (ROOT/'reference/damage_oracle_events.txt').read_text().splitlines():
  v=line.split('|')
  if v[0]!='DAMAGE':continue
  case,hp,armor,timer,active=map(int,v[1:]);c=ref['cases'][case]
  lib.check(c['hp'],c['armor'],c['damage'],c['invincible'])
  assert (lib.hp(),lib.armor(),lib.timer(),lib.dead())==(hp,armor,timer,int(active==64)),(c,v,lib.hp(),lib.armor(),lib.timer())
  assert lib.motion();count+=1
 report={'passed':True,'source_damage_cases':count,'scope':'Ordinary armor absorption, overflow into health, zero/exact/lethal damage, invulnerability gate and 60-tick duration. Special contact effects, hurt visuals, armor break graphics and death presentation remain separate.'}
 (ROOT/'reports/damage-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
