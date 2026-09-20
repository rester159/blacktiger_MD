#!/usr/bin/env python3
"""All five source attack strengths through native input/projectile creation."""
import json,hashlib
from test_runtime import ROOT,Runner,state,put
ref=json.loads((ROOT/'reference/weapon_oracle.json').read_text())
for key,path in [('trace_sha256','reference/weapon_oracle_events.txt'),('lua_sha256','tools/weapon_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
rom=(ROOT/'out/release/rom.bin').read_bytes();r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);cases=[]
for line in (ROOT/'reference/weapon_oracle_events.txt').read_text().splitlines():
 if not line.startswith('WEAPON|'):continue
 _,tier,damage,reach=line.split('|');tier=int(tier)+1;damage=int(damage)
 assert rom[r.symbols['player_weapon_damage']+tier-1]==damage
 s=state(r);s.mode=2;put(r,s);r.run(8)
 s=state(r);s.mode=1;s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.attack=0;s.p.weapon=tier;s.p.face=1;s.p.invincible=10000;s.previous_input=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 put(r,s)
 for _ in range(10):
  r.run(1,1<<1);s=state(r);shots=[q for q in s.shots if q.active and not q.enemy]
  if shots:
   r.run(1,1<<1);s=state(r);shots=[q for q in s.shots if q.active and not q.enemy];break
 assert shots and all(q.damage==damage for q in shots),(tier,damage,[q.damage for q in shots])
 cases.append(dict(tier=tier,damage=damage))
# Buy the fifth tier at the source default-difficulty price.
s=state(r);s.mode=3;s.shop_item=3;s.coins=12800;s.p.weapon=4;s.previous_input=0;put(r,s);r.run(2);r.run(3,1<<1)
assert state(r).p.weapon==5 and state(r).coins==0
r.close();report={'passed':True,'cases':cases,'fifth_tier_purchase':True,'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':'Original attack-entry strength lookup and native projectile creation at all five tiers. Weapon reach/animation, projectile collision and source shop pricing remain separate.'}
(ROOT/'reports/weapon-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
