"""Production last-life path, timed free continues, expiry and music in cartridge."""
import json,hashlib
from test_runtime import ROOT,Runner,state,put
cases=[]
for accept in (False,True):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(30)
 s=state(r);s.mode=2;put(r,s);r.run(60)
 s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=1;s.coins=444;s.score=12345;s.p.weapon=5;put(r,s)
 for _ in range(120):
  r.run(1)
  if state(r).mode==7:break
 assert state(r).mode==7 and state(r).p.lives==0
 digits=set();notice=False;offer=False;commands=set()
 for _ in range(2000):
  r.run(1,8 if accept else 0);s=state(r);raw=r.read('game_over',4);remaining=int.from_bytes(raw[:2],'big');phase,digit=raw[2:]
  commands.add(r.read('music_command',1)[0])
  if s.mode!=7:break
  if phase==1:
   notice=True;assert s.p.lives==0 and s.score==12345 and s.coins==444
  if phase==2:
   offer=True;digits.add(digit)
   if not accept and remaining==740:
    sat=r.read('vdpSpriteCache',8);assert sat[:2]==b'\x00\x60' and sat[3]==0
    r.capture('continue-offer.png')
 assert notice and offer and 0x31 in commands
 if accept:
  assert s.mode==1 and (s.p.lives,s.score,s.coins,s.p.weapon)==(3,0,444,5)
  r.run(15,8);assert state(r).mode==1,'Held continue input must not immediately pause'
 else:
  assert s.mode==0 and digits==set(range(10)) and 0x34 in commands
  r.run(5);assert not r.read('music_active',1)[0]
  r.run(5,8);s=state(r);assert s.mode==1 and s.coins==200 and s.score==0 and s.p.weapon==1
 cases.append(dict(accept=accept,notice_blocks_start=True,continue_offer=True,expiry_to_title=not accept,held_start_safe=accept));r.close()
report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Last-life entry, all countdown digits, notice/continue FM cues, offer expiry to title, new-game reset, free continuation retaining inventory and held-Start edge. Exact task-relative durations checked by host test; original UI artwork/fades and high-score initials excluded.')
(ROOT/'reports/game-over-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
