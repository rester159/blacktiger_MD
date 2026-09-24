"""Home Debug level selection through controller input, with fresh-run state."""
import hashlib,json,struct
from test_runtime import ROOT,Runner,state,put
checks=[]
for level in range(8):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100)
 def tap(key):r.run(8,key);r.run(8)
 tap(32);tap(8)
 for key in (16,16,32,32,64,128,64,128):tap(key)
 tap(8)
 assert r.read('frontend',2)==bytes([1,4])
 assert r.read('frontend',5)[4]==3
 if level==0:
  tap(1);assert r.read('frontend',3)==bytes([1,1,3]);tap(2)
  tap(16);assert r.read('frontend',14)[13]==12
  tap(32);assert r.read('frontend',14)[13]==0
 tap(32);tap(32)
 if level>=4:tap(128)
 for _ in range(level%4):tap(32)
 assert r.read('frontend',14)[13]==level+4
 if level==3:r.capture('home-level-select.png')
 tap(2 if level%2 else 8);s=state(r)
 assert s.mode==1 and s.round==level,(level,s.mode,s.round)
 assert r.read('frontend',5)[4]==2
 assert s.p.lives==3 and s.p.weapon==1 and not r.read('boss_rush',1)[0]
 assert s.p.exploration==1
 # A selected-level session must restore protection if player state loses it.
 s.p.exploration=0;put(r,s);r.run(4);s=state(r)
 assert s.p.exploration==1,(level,'exploration was not restored')
 timer=(s.time,s.clock);health=(s.p.hp,s.p.armor,s.p.lives)
 r.run(240);s=state(r)
 assert s.mode==1 and (s.time,s.clock)==timer,(level,'exploration timer advanced')
 assert (s.p.hp,s.p.armor,s.p.lives)==health,(level,'exploration damage')
 assert int.from_bytes(r.read('video_cache_faults'),'big')==0
 checks.append(dict(level=level+1,starts_directly=True,credits=2,exploration=True,frozen_timer=True));r.close()
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(exploration=True);r.run(20)
s=state(r);s.mode=2;put(r,s);r.run(20)
s=state(r);s.mode=1;s.cam_x=0;s.cam_y=688;s.p.x=128*256;s.p.y=896*256
s.p.vx=s.p.vy=0;s.p.hp=4;s.p.armor=2;s.p.invincible=0;s.p.exploration=0
for a in s.actors:a.active=0
for i in range(160):s.spawned[i]=2
for q in s.shots:q.active=0
q=s.shots[0];q.active=q.enemy=1;q.life=20;q.damage=20
q.x=s.p.x+16*256;q.y=s.p.y+16*256;q.vx=q.vy=0
put(r,s);r.run(12);s=state(r)
assert not s.shots[0].active and (s.p.hp,s.p.armor,s.mode)==(4,2,1),'exploration projectile immunity'
meta=json.loads((ROOT/'reports/assets.json').read_text())
hazard=next(d['id'] for d in meta['actor_definitions'] if d['bank']==1 and d['address']==0xb2a9)
s.mode=2;put(r,s);r.run(20);s=state(r)
s.mode=1;s.p.invincible=0;a=s.actors[0];a.active=1;a.definition=hazard;a.source=159
# Hazard center matches the normal player contact center.
a.x=s.p.x+8*256;a.y=s.p.y+8*256
put(r,s);r.run(12);s=state(r)
assert (s.p.hp,s.p.armor,s.mode)==(4,2,1),'exploration hazard immunity'
s.mode=2;put(r,s);r.run(20);s=state(r)
s.mode=1;s.p.y=(meta['rounds'][0]['height']+64)*256;s.p.vy=0;lives=s.p.lives
put(r,s);r.run(30);s=state(r)
assert s.mode==1 and s.p.lives==lives and s.p.y//256<meta['rounds'][0]['height'],'pit recovery'
# Contacts that bypass ordinary damage must also respect exploration.
for effect_kind in ('poison','reverse'):
 s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
 s.cam_x=0;s.cam_y=688;s.p.x=128*256;s.p.y=896*256
 s.p.vx=s.p.vy=0;s.p.invincible=0;s.mode=1
 for a in s.actors:a.active=0
 for i in range(160):s.spawned[i]=2
 for name in ('status_gate','status_reverse','shop_poison'):r.write(name,0,b'\0')
 r.write('shop_antidotes',0,b'\x01')
 r.write('flailer_weapons',0,bytes(18*24));r.write('container_traps',0,bytes(18*24))
 if effect_kind=='poison':
  root=json.loads((ROOT/'reference/flailer.json').read_text())['roots'][0][9]
  effect=struct.pack('>HHbbBxHhhBBBB',0,100,0,0,0,root,136,904,1,0,0,0)
  r.write('flailer_weapons',0,effect)
 else:
  root=json.loads((ROOT/'reference/container.json').read_text())['wave_roots'][1]
  effect=struct.pack('>HHbbBxHhhBBBB',0,100,0,0,0,root,136,904,1,0,1,4)
  r.write('container_traps',0,effect)
 put(r,s);r.run(20)
 assert r.read('shop_poison',1)==r.read('status_reverse',1)==r.read('status_gate',1)==b'\0',effect_kind
 assert r.read('shop_antidotes',1)==b'\x01',(effect_kind,'consumed antidote')
s=state(r)
# Return to the actual Arcade menu and start a new run: exploration must reset.
s.mode=0;put(r,s);r.write('frontend',0,bytes([0,1,0]));r.run(30)
r.run(8,4);r.run(8);r.run(8,8);r.run(30)
assert not state(r).p.exploration,'exploration leaked into Arcade'
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),checks=checks,session_protection_restored=True,status_immunity=True,damage_immunity=True,hazard_immunity=True,pit_recovery=True,arcade_reset=True,cancel_without_spending=True,wrap_and_column_navigation=True)
(ROOT/'reports/level-select-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
