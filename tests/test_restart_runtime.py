#!/usr/bin/env python3
import json,struct,hashlib
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
from test_hidden_runtime import place,fire,metadata,contract
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
rom=(ROOT/'out/release/rom.bin').read_bytes()
def die():
 s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;s.p.hp=0;s.p.armor=0;s.p.weapon=5;s.score=34000;s.coins=444
 s.spawned[158]=2;s.spawned[159]=1;put(r,s)
 r.write('progress_max_hp',0,b'\x05');r.write('container_keys',0,b'\x07');r.write('shop_antidotes',0,b'\x09');r.write('shop_poison',0,b'\x01')
 for _ in range(100):
  r.run(1);s=state(r)
  if s.mode==1:break
 assert (s.p.lives,s.p.hp,s.p.armor,s.p.weapon,s.score,s.coins)==(2,5,2,5,34000,444)
 assert s.spawned[158]==2 and s.spawned[159]==0
 assert r.read('container_keys',1)==b'\x07' and r.read('shop_antidotes',1)==b'\x09' and r.read('shop_poison',1)==b'\0'
 s.mode=2;put(r,s);r.run(10)
slot,row,level=fixture(r,0,1,0xacd3);s=state(r);a=s.actors[slot];a.life=1;xy=(a.x,a.y);put(r,s)
persistent=struct.unpack_from('>4H',rom,r.symbols['spawn'+str(level)]+8*row)[3]-33
r.write('container_contents',persistent,b'\x11');r.write('container_keys',0,b'\x01')
for _ in range(100):
 s=state(r);s.mode=1;s.p.x=xy[0];s.p.y=xy[1];s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
 if r.read('container_collected',8)[persistent]:break
assert r.read('container_collected',8)[persistent]==1
die();assert r.read('container_opened',8)[persistent]==1 and r.read('container_collected',8)[persistent]==1
# Return to the real placement after a life loss; its collected state remains empty.
s=state(r);s.mode=1;s.p.x=xy[0];s.p.y=xy[1];s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(30)
assert state(r).coins==444 and r.read('container_keys',1)==b'\x07'
# Break and collect a real hidden wall, then retain its terrain and reward flags.
patch=contract['rounds'][level][0];count=metadata['rounds'][level]['spawns'];rows=[struct.unpack_from('>4H',rom,r.symbols['spawn'+str(level)]+i*8) for i in range(count)]
row=next(i for i,v in enumerate(rows) if v[3]==patch['persistent'] and metadata['actor_definitions'][v[2]]['kind']==9)
x,y,definition,_=rows[row];slot=place(r,level,row,x,y)
for _ in range(5):fire(r,slot)
assert r.read('world_opened',1)[0]&1
for _ in range(30):
 s=state(r);a=s.actors[slot];s.mode=1;s.p.x=a.x;s.p.y=a.y;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
 if state(r).spawned[row]==2:break
assert state(r).spawned[row]==2 and r.read('taken',1)[0]&1
die();assert state(r).spawned[row]==2 and r.read('world_opened',1)[0]&1 and r.read('taken',1)[0]&1
# Exhaustion consumes the final life as well.
s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=1;put(r,s)
for _ in range(120):
 r.run(1)
 if state(r).mode==7:break
assert state(r).mode==7 and state(r).p.lives==0
# Continue preserves the round, inventory, health progression and world; only score/lives reset.
old_round=state(r).round;old_opened=r.read('world_opened',1)
for _ in range(1000):
 r.run(1)
 if r.read('game_over',4)[2]==2:break
assert r.read('game_over',4)[2]==2
r.run(10,8);s=state(r)
assert (s.mode,s.round,s.p.lives,s.score,s.coins,s.p.weapon,s.p.armor,s.p.hp)==(1,old_round,3,0,444,5,2,5)
assert r.read('progress_max_hp',1)==b'\x05' and r.read('container_keys',1)==b'\x07' and r.read('shop_antidotes',1)==b'\x09'
assert r.read('world_opened',1)==old_opened and r.read('container_collected',8)[persistent]==1
# A separate new game from the title clears persistent objects and resources.
r.run(3);s=state(r);s.mode=0;s.previous_input=0;put(r,s);r.run(10,8);r.run(900);s=state(r)
assert s.mode==1 and s.p.lives==3 and s.coins==200 and r.read('world_opened',1)==b'\0',(s.mode,s.p.lives,s.coins,r.read('world_opened',1))
assert r.read('container_opened',8)==bytes(8) and r.read('container_collected',8)==bytes(8)
r.close();report={'passed':True,'equipment_and_inventory_retained':True,'armor_restored_and_poison_cleared':True,'consumed_rows_retained_active_rows_released':True,'collected_chest_and_hidden_wall_retained':True,'last_life_consumed':True,'continue_retains_progress_and_resets_score':True,'held_start_does_not_pause':True,'new_game_clears_persistence':True,'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':'Native life-loss integration with actual chest and hidden-wall rows, backed by source death resource writes and four-byte persistence-copy loop. Native continue timing checked separately; continues consume a configured credit. Complete arcade presentation remains unfinished.'}
(ROOT/'reports/restart-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
