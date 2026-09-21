"""Public mode menus, coin edges, bounded Home credits and original intro."""
import json,hashlib
from test_runtime import ROOT,Runner,state,put
checks=[]
def check(name,condition):assert condition,name;checks.append(name)
def tap(r,key):r.run(8,key);r.run(8)
def front(r):return list(r.read('frontend',9))
def boot():r=Runner(ROOT/'out/release/rom.bin');r.run(100);return r
def exhaust(r):
 s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=1;s.previous_input=0;put(r,s)
 r.write('player_death',0,bytes(len(r.read('player_death',12))))
 r.run(160)
r=boot();check('arcade is default',front(r)[:5]==[0,0,0,0,0]);tap(r,8);tap(r,8)
check('arcade refuses free start',state(r).mode==0 and front(r)[6]>0)
tap(r,256);check('C does not insert coins',front(r)[4]==0)
r.run(30,4);check('held Select inserts one coin',front(r)[4]==1);r.run(8);tap(r,4)
check('separate Select press inserts second coin',front(r)[4]==2)
tap(r,2);check('attack cannot start Play',state(r).mode==0)
tap(r,8);check('Start spends one credit and enters arcade intro',state(r).mode==9 and front(r)[4]==1)
r.run(70);r.capture('arcade-intro.png');r.run(900);check('arcade intro reaches play',state(r).mode==1)
r.close()
r=boot();tap(r,32);tap(r,8);check('Home defaults to three credits',front(r)[0]==1 and front(r)[4]==3)
tap(r,4);check('Home ignores Select coins',front(r)[4]==3)
tap(r,8);check('Home Play opens level selector without spending credits',front(r)[1]==3 and front(r)[4]==3)
tap(r,8);check('Home selected level starts without intro',state(r).mode==1 and state(r).round==0 and front(r)[4]==2)
for remaining in (1,0):
 exhaust(r);check('continue offered with credits '+str(remaining),state(r).mode==7)
 # Hold Start through offer: ordinary game-over handler consumes it once.
 r.run(300,8);r.run(8);check('continue consumes exactly one credit '+str(remaining),state(r).mode==1 and front(r)[4]==remaining)
exhaust(r);r.run(300,8);check('three-credit Home run ends without another continue',state(r).mode==0 and front(r)[4]==0)
r.run(8);tap(r,1);tap(r,16);tap(r,8)
check('Home credits do not become arcade coins',front(r)[0]==0 and front(r)[4]==0)
r.close()
r=boot();tap(r,32);tap(r,8);tap(r,32);tap(r,32);tap(r,8)
check('Home Options opens',front(r)[1]==2)
for _ in range(6):tap(r,32)
tap(r,128);check('Home credit limit is adjustable',r.read('settings',14)[13]==4)
tap(r,1);tap(r,16);tap(r,16);tap(r,8)
tap(r,8)
check('new Home run uses selected credit limit',state(r).mode==1 and front(r)[4]==3)
r.close()
report=dict(passed=True,checks=checks,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Real six-button controller input through both mode menus, coin edges, three total Home credits, option adjustment and unskipped Arcade intro and direct Home level selection.')
(ROOT/'reports/frontend-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
