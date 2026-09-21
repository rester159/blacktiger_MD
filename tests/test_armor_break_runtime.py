#!/usr/bin/env python3
"""Armor fragments arise through real cartridge damage and timeout paths."""
import json,hashlib
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);cases=[]
for armor,damage,protected,timeout in ((4,2,0,0),(2,2,0,0),(1,3,0,0),(0,1,0,0),(2,3,1,0),(4,0,1,1)):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.mode=1;s.cam_x=0;s.cam_y=688;s.p.x=128*256;s.p.y=832*256;s.p.vx=s.p.vy=0;s.p.hp=4;s.p.armor=armor;s.p.invincible=100 if protected else 0;s.p.climb=0;s.time=0 if timeout else 100;s.clock=59 if timeout else 0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(len(s.spawned)):s.spawned[i]=2
 r.write('armor_fragments',0,bytes(56));r.write('player_death',0,bytes(9))
 if not timeout:
  q=s.shots[0];q.active=1;q.enemy=1;q.life=20;q.damage=damage;q.x=s.p.x+16*256;q.y=s.p.y+16*256;q.vx=q.vy=0
 put(r,s)
 for _ in range(60):
  r.run(1);s=state(r)
  if s.mode==4 or (not timeout and not s.shots[0].active):break
 expected=bool(armor and (timeout or (not protected and damage>=armor)))
 raw=r.read('armor_fragments',56);active=[raw[i*14+12] for i in range(4)]
 assert active==[int(expected)]*4,(armor,damage,protected,timeout,active)
 if timeout:assert s.mode==4 and s.p.armor==0
 if expected and not timeout:
  r.run(60);r.capture('armor-break.png')
  raw=r.read('armor_fragments',56);positions=[raw[i*14+8:i*14+12].hex() for i in range(4)]
  assert len(set(positions))==4,(positions,state(r).mode,r.read("armor_fragments",56).hex())
 cases.append(dict(armor=armor,damage=damage,protected=protected,timeout=timeout,fragments=expected))
r.close();report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual projectile contact triggers four moving armor sprites on exact depletion and overflow; partial/protected/unarmored hits do not. Timeout breaks armor despite invulnerability.')
(ROOT/'reports/armor-break-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
