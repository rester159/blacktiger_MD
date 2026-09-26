"""Linked cartridge: pot break/reward/trap and persistence fixtures."""
import json,struct,hashlib
from test_runtime import ROOT,Runner,state,put
DATA=json.loads((ROOT/'reference/pots.json').read_text())
def pot(r,i=0):
 b=r.read('pots',660)[20*i:20*i+20]
 return dict(x=int.from_bytes(b[8:10],'big',signed=True),y=int.from_bytes(b[10:12],'big',signed=True),segment=int.from_bytes(b[12:14],'big'),active=b[14],id=b[15],kind=b[16],phase=b[17],hits=b[18],pending=b[19])
def pause(r):
 s=state(r);s.mode=2;put(r,s);r.run(12)
def resume(r,ticks=1):
 s=state(r);s.mode=1;put(r,s);start=s.frame
 for _ in range(ticks*5+100):
  r.run(1)
  if (state(r).frame-start)&65535>=ticks:return
 raise AssertionError('tick timeout')
def fixture(kind):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(100);pause(r)
 s=state(r);s.p.invincible=10000;s.p.exploration=1;s.p.x=112*256;s.p.y=896*256;s.p.vx=s.p.vy=0
 for a in s.actors:a.active=0
 for i in range(160):s.spawned[i]=2
 put(r,s);r.write('pots',0,bytes(660));r.write('pots_end',0,b'\x01');r.write('pot_contents',31,bytes([kind]))
 b=bytearray(20);struct.pack_into('>hhH6B',b,8,176,896,DATA['roots'][kind-2][0],1,31,kind,0,2,0)
 r.write('pots',0,b);return r
def hit(r):
 pause(r);r.write('pots',19,b'\x01');resume(r,2)
def run():
 checks=[]
 for kind in (2,4,5,6,7,8,9,10,11,12,13,14,15):
  r=fixture(kind);before=state(r);keys=r.read('container_keys',1)[0]
  hit(r);p=pot(r);assert (p['active'],p['hits'],p['phase'])==(1,1,0),(kind,p)
  assert state(r).coins==before.coins
  hit(r);resume(r,45);p=pot(r)
  if 4<=kind<=11:
   assert p['active'] and p['phase']==2,(kind,p)
   pause(r);s=state(r);s.p.x=168*256;s.p.y=888*256;s.p.vx=s.p.vy=0;s.clock=0;collection_time=s.time;put(r,s);resume(r,4)
   s=state(r);assert not pot(r)['active'],(kind,pot(r))
   if kind<=9:assert s.coins-before.coins=={4:5,5:10,6:50,7:100,8:500,9:1000}[kind],(kind,s.coins,before.coins)
   if kind==10:assert r.read('container_keys',1)[0]==keys+1
   if kind==11:assert s.time==collection_time+30,(s.time,collection_time)
   checks.append(f'{kind}: collectible correct')
  elif kind>=12:
   ids=struct.unpack('>4H',(ROOT/'out/release/rom.bin').read_bytes()[r.symbols['pot_trap_defs']:r.symbols['pot_trap_defs']+8])
   assert any(a.active and a.definition==ids[kind-12] and a.source==159 for a in state(r).actors),(kind,[(a.active,a.definition,a.source) for a in state(r).actors])
   assert not p['active'];checks.append(f'{kind}: original enemy family released')
  else:assert not p['active'];checks.append('empty pot breaks')
  r.close()
 # An actual source placement, kept open across retirement and checkpoint death.
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(100);pause(r)
 raw=r.read('pots',660);slot=next(i for i in range(33) if raw[i*20+14]);initial=pot(r,slot);pid=initial['id']
 r.write('pot_contents',pid,b'\x0a');r.write('pots',slot*20+16,b'\x0a')
 for _ in range(2):
  pause(r);r.write('pots',slot*20+19,b'\x01');resume(r,3)
 resume(r,45);assert pot(r,slot)['phase']==2
 pause(r);r.write('pots',slot*20+8,struct.pack('>h',-64));resume(r,8)
 assert pot(r,slot)['phase']==2 and pot(r,slot)['active'] and pot(r,slot)['x']==initial['x'],pot(r,slot)
 contents=r.read('pot_contents',32)
 pause(r);s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(120)
 assert r.read('pot_contents',32)==contents
 assert pot(r,slot)['active'] and pot(r,slot)['phase']==2,pot(r,slot)
 pause(r);p=pot(r,slot);s=state(r);s.p.x=(p['x']-8)*256;s.p.y=(p['y']-8)*256;s.p.vx=s.p.vy=0;put(r,s);resume(r,4)
 assert not pot(r,slot)['active']
 pause(r);s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(120)
 assert not pot(r,slot)['active'],'collected pot respawned after death'
 checks.append('uncollected contents survive retirement/death; collected pot stays gone');r.close()
 # Real button input, without injecting a pot-hit flag.
 r=fixture(10);resume(r,2)
 for _ in range(4):r.run(14,2);r.run(30)
 assert pot(r)['phase']==2 or not pot(r)['active'],pot(r)
 checks.append('A-button chain/daggers break pot');r.capture('pots-opened.png');r.close()
 report=dict(passed=True,checks=checks,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest())
 (ROOT/'reports/pots-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
