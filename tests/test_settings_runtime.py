"""Shared difficulty selects source damage/prices; HUD exposes live inventory."""
import json,hashlib,ctypes as C
from test_runtime import ROOT,Runner,state,put
from arcade_source import Source
source=Source();cases=[]
for difficulty in range(8):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100)
 # Select Home/Options, then adjust the same difficulty row used by Arcade.
 def tap(mask):r.run(8,mask);r.run(8)
 tap(32);tap(8);tap(128);tap(8);tap(32)
 for _ in range((difficulty-4)%8):tap(128)
 assert r.read('settings',14)[8]==difficulty
 tap(1);tap(64);tap(8);r.skip_intro();r.run(30)
 assert r.read('combat_difficulty',1)[0]==difficulty and r.read('shop_difficulty',1)[0]==difficulty
 expected=list(source.read(6,0xb6f0+difficulty*5,5));actual=[]
 for tier in range(5):
  s=state(r);s.mode=1;s.p.weapon=tier+1;s.p.invincible=10000;s.previous_input=0
  for a in s.actors:a.active=0
  for i in range(160):s.spawned[i]=2
  put(r,s);r.write('player_attack',0,bytes(12));r.run(4);r.run(6,2)
  actual.append(r.read('player_attack',12)[6])
 assert actual==expected,(difficulty,actual,expected)
 cases.append(dict(difficulty=difficulty+1,weapon_damage=actual));r.close()
report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Public Home Options navigation for all eight settings, start-time binding to shared combat/shop difficulty, native attack damage for all five weapon tiers against source bank 6 B6F0. Other arcade difficulty effects remain outside this check.')
(ROOT/'reports/settings-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
