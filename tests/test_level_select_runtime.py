"""Home level selection through controller input, with fresh-run state."""
import hashlib,json
from test_runtime import ROOT,Runner,state
checks=[]
for level in range(8):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100)
 def tap(key):r.run(8,key);r.run(8)
 tap(32);tap(8);tap(8)
 assert r.read('frontend',2)==bytes([1,3])
 assert r.read('frontend',5)[4]==3
 if level==0:
  tap(1);assert r.read('frontend',3)==bytes([1,1,0]);tap(2)
  tap(16);assert r.read('frontend',10)[9]==7
  tap(32);assert r.read('frontend',10)[9]==0
 if level>=4:tap(128)
 for _ in range(level%4):tap(32)
 assert r.read('frontend',10)[9]==level
 if level==3:r.capture('home-level-select.png')
 tap(8);s=state(r)
 assert s.mode==1 and s.round==level,(level,s.mode,s.round)
 assert r.read('frontend',5)[4]==2
 assert s.p.lives==3 and s.p.weapon==1 and not r.read('boss_rush',1)[0]
 assert int.from_bytes(r.read('video_cache_faults'),'big')==0
 checks.append(dict(level=level+1,starts_directly=True,credits=2));r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),checks=checks,cancel_without_spending=True,wrap_and_column_navigation=True)
(ROOT/'reports/level-select-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
