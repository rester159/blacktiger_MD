#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);checks=[]
data=json.loads((ROOT/'reference/shop.json').read_text());rom=(ROOT/'out/release/rom.bin').read_bytes()
def tap(mask):r.run(3);r.run(3,mask);r.run(3)
for index,item in enumerate(data['grid']):
 if item not in range(1,11):continue
 s=state(r);s.mode=3;s.shop_item=index;s.coins=20000;s.p.weapon=1;s.p.armor=0;s.previous_input=0;put(r,s)
 r.write('container_keys',0,b'\0');r.write('shop_antidotes',0,b'\0');r.write('shop_poison',0,b'\0');r.write('shop_difficulty',0,bytes([data['default_difficulty']]))
 r.run(20);tap(1<<1);s=state(r)
 price=data['prices'][(item-1)//4][4][(item-1)%4] if item<=8 else 30 if item==9 else 150
 assert s.coins==20000-price,(item,s.coins,price)
 assert r.read('shop_result',1)==b'\x01'
 assert r.read('sfx_slots',22)[8]==0x12 and state(r).sound_count==0,(item,'purchase cue')
 if item<=4:assert s.p.weapon==item+1
 elif item<=8:assert s.p.armor==(item-4)*2
 elif item==9:assert r.read('container_keys',1)==b'\x01'
 else:assert r.read('shop_antidotes',1)==b'\x01'
 if item<=8:
  tap(1<<1);assert state(r).coins==s.coins,'owned equipment charged again'
  assert r.read('shop_result',1)==bytes([2 if s.coins<price else 3])
 s=state(r);s.coins=price-1;put(r,s);tap(1<<1);assert state(r).coins==price-1
 assert r.read('shop_result',1)==b'\x02'
 checks.append(dict(item=item,price=price,purchase_and_refusal=True))
# The visible arcade layout has two horizontal rows, with no blank top-right cell.
s=state(r);s.mode=3;s.shop_item=0;put(r,s)
tap(32);assert state(r).shop_item==6
tap(128);assert state(r).shop_item==7
tap(16);assert state(r).shop_item==1
tap(64);assert state(r).shop_item==0
# A key bought with the native shop controls opens a real container row.
r.write('container_keys',0,b'\0');slot,row,level=fixture(r,0,1,0xacd3)
s=state(r);s.mode=3;s.shop_item=0;s.coins=30;s.previous_input=0;put(r,s)
for _ in range(4):tap(1<<7) # Genesis right
assert state(r).shop_item==4,state(r).shop_item
tap(1<<1);assert r.read('container_keys',1)==b'\x01' and state(r).coins==0
r.capture('shop-key-purchased.png');tap(1<<0);assert state(r).mode==1
persistent=struct.unpack_from('>4H',rom,r.symbols['spawn'+str(level)]+8*row)[3]-33
for _ in range(20):
 s=state(r);a=s.actors[slot];s.mode=1;s.p.x=a.x;s.p.y=a.y;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s);r.run(1)
 if r.read('container_opened',8)[persistent]:break
assert r.read('container_opened',8)[persistent]==1 and r.read('container_keys',1)==b'\0'
r.run(3);r.capture('shop-key-container.png')
# Both quantity caps and the explicit exit cell.
for index,symbol in ((4,'container_keys'),(10,'shop_antidotes')):
 s=state(r);s.mode=3;s.shop_item=index;s.coins=1000;put(r,s);r.write(symbol,0,b'\x63');tap(1<<1);assert state(r).coins==1000
s=state(r);s.mode=3;s.shop_item=11;put(r,s);tap(1<<1);assert state(r).mode==1
r.close();report={'passed':True,'cases':checks,'purchased_key_opens_source_container':True,'quantity_caps':True,'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':'Linked purchases for ten goods, refusal rules, HUD/menu capture and shop-purchased key opening an actual source container. NPC rescue entry has its own test; no natural full route is claimed.'}
(ROOT/'reports/shop-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
