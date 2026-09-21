#!/usr/bin/env python3
"""All five source attack strengths through native input/projectile creation."""
import json,hashlib
from test_runtime import ROOT,Runner,state,put
ref=json.loads((ROOT/'reference/weapon_oracle.json').read_text())
for key,path in [('trace_sha256','reference/weapon_oracle_events.txt'),('lua_sha256','tools/weapon_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
rom=(ROOT/'out/release/rom.bin').read_bytes();r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);cases=[]
for line in (ROOT/'reference/weapon_oracle_events.txt').read_text().splitlines():
 if not line.startswith('WEAPON|'):continue
 _,tier,damage,reach=line.split('|');tier=int(tier)+1;damage=int(damage)
 s=state(r);s.mode=2;put(r,s);r.run(8)
 s=state(r);s.mode=1;s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.attack=0;s.p.weapon=tier;s.p.face=1;s.p.invincible=10000;s.previous_input=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 r.write('player_attack',0,bytes(12));r.write('player_daggers',0,bytes(18*9));put(r,s)
 for _ in range(12):
  r.run(1,1<<1);attack=r.read('player_attack',12)
  if attack[0]:break
 assert attack[5:7]==bytes((int(reach),damage)),(tier,attack.hex())
 assert sum(r.read('player_daggers',18*9)[i*18+14]==1 for i in range(9))==3
 # Held fire completes exactly one attack; it does not generate automatic volleys.
 r.run(90,1<<1);assert not r.read('player_attack',12)[0]
 cases.append(dict(tier=tier,damage=damage,reach=int(reach)))
# Poison suppresses dagger volleys while preserving the chain controller.
for poison in (38,0):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.mode=1;s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;s.previous_input=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 r.write('player_attack',0,bytes(12));r.write('player_daggers',0,bytes(18*9))
 r.write('shop_poison',0,bytes([poison]));put(r,s)
 for _ in range(20):
  r.run(1,1<<1)
  if r.read('player_attack',12)[0]:break
 assert r.read('player_attack',12)[0]
 assert any(r.read('player_daggers',18*9)[i*18+14] for i in range(9))==(not poison)
# Buy the fifth tier at the source default-difficulty price.
s=state(r);s.mode=3;s.shop_item=3;s.coins=12800;s.p.weapon=4;s.previous_input=0;put(r,s);r.run(2);r.run(3,1<<1)
assert state(r).p.weapon==5 and state(r).coins==0
r.close();report={'passed':True,'cases':cases,'fifth_tier_purchase':True,'poison_dagger_suppression':True,'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':'All five source damage/reach tiers through real input; three-dagger volleys, release-to-retrigger, poison suppression and fifth-tier purchase.'}
(ROOT/'reports/weapon-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
