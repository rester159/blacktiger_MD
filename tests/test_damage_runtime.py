#!/usr/bin/env python3
"""Cartridge projectile path reaches shared damage without artificial knockback."""
import json,hashlib
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
cases=[]
for armor,damage,hp,invincible in ((4,2,4,0),(2,2,4,0),(1,3,4,0),(0,1,4,0),(1,5,4,0),(2,3,4,20)):
 s=state(r);s.mode=1;s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.hp=hp;s.p.armor=armor;s.p.invincible=invincible;s.p.climb=0;s.time=100;s.clock=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(len(s.spawned)):s.spawned[i]=2
 q=s.shots[0];q.active=1;q.enemy=1;q.life=20;q.damage=damage;q.x=s.p.x+16*256;q.y=s.p.y+16*256;q.vx=q.vy=0
 start=s.frame;put(r,s)
 for _ in range(12):
  r.run(1);s=state(r)
  if s.frame!=start:break
 assert not s.shots[0].active,'Projectile missed controlled contact'
 remaining=max(0,damage-armor);expected_armor=max(0,armor-damage);expected_hp=max(0,hp-remaining)
 if invincible:expected_armor,expected_hp=armor,hp
 assert (s.p.armor,s.p.hp)==(expected_armor,expected_hp),(armor,damage,hp,invincible,s.p.armor,s.p.hp)
 assert (s.mode==4)==(expected_hp==0)
 assert s.p.vy>=0,'Unrequested hurt jump remains'
 if expected_hp and not invincible:assert s.p.invincible==60,s.p.invincible
 cases.append(dict(armor=armor,damage=damage,hp=hp,invincible=invincible))
r.close()
report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Injected enemy projectile contacts on linked cartridge: absorption, exact armor break, overflow, lethal and protected hits.'}
(ROOT/'reports/damage-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
