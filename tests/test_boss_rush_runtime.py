"""Eight native bosses in one arena; actual POW contacts drive death sequences."""
import json,hashlib
from test_runtime import ROOT,Runner,state,put
meta=json.loads((ROOT/'reports/assets.json').read_text())
pickup=next(d['id'] for d in meta['actor_definitions'] if d['bank']==4 and d['address']==0xb515)
roster=[(4,0x9eb1),(4,0x9f16),(3,0x8000),(1,0x9fc4),(1,0x98a3),(3,0x991d),(1,0x98e8),(3,0x9b24)]
r=Runner(ROOT/'out/release/rom.bin');r.run(100);cases=[]
def tap(mask):r.run(12,mask);r.run(12)
def walk(mask,travel=512):
 previous=state(r).cam_x;previous_tick=state(r).frame;scrolled=0
 for _ in range(640):
  r.run(1,mask);s=state(r);delta=abs(s.cam_x-previous)
  ticks=(s.frame-previous_tick)&65535
  # Catch-up retains the original two pixels per simulation tick. Sampling
  # RAM can straddle an in-flight tick: game.frame changes at entry,
  # while cam_x changes at exit. Allow that one additional completed step.
  assert ticks<=3 and delta<=2*(ticks+1),('camera jump',previous,s.cam_x,ticks)
  previous_tick=s.frame
  scrolled+=delta;previous=s.cam_x
  if (mask==128 and s.p.x//256>=1312) or (mask==64 and s.p.x//256<=576):break
  for a in s.actors:
   if a.active and a.definition in (49,62) and a.state!=2:
    assert a.y==192*256 and a.vy==0,('walking boss above floor',a.definition,a.y//256)
 assert scrolled==travel,('incomplete scroll',scrolled,travel)
 assert int.from_bytes(r.read('vblank_flush_overruns'),'big')==0,'arena DMA exceeded VBlank'
tap(32);tap(8);tap(32);tap(8)
for stage in range(8):
 s=state(r);assert s.mode==1 and r.read('boss_rush',4)==bytes([1,stage,0,0]),(stage,s.mode,list(r.read('boss_rush',6)))
 assert (s.round,s.cam_x,s.cam_y)==(7,832,64)
 assert 944<=s.p.x//256<=946,('center spawn',s.p.x//256)
 if stage in (0,3):
  coins=s.coins;keys=r.read('container_keys',1);credits=r.read('frontend',9)[4]
  s.mode=4;s.mode_timer=0;s.p.lives=2 if stage==0 else 1;put(r,s);r.run(180)
  if stage==3:
   assert state(r).mode==7;r.run(300,8);r.run(12)
  s=state(r);assert s.mode==1 and (s.round,s.cam_x,s.cam_y)==(7,832,64)
  assert r.read('boss_rush',4)==bytes([1,stage,0,0]) and s.coins==coins and r.read('container_keys',1)==keys
  assert r.read('frontend',9)[4]==credits-(stage==3)
 active=[a for a in s.actors if a.active];d=meta['actor_definitions'][active[0].definition]
 assert (d['bank'],d['address'])==roster[stage]
 assert all(a.definition==active[0].definition for a in active)
 # Traverse all three screens in both directions with the real controller.
 coins=s.coins;s.p.invincible=10000;put(r,s);before=bytes(s.actors)
 if stage&1:walk(64,256)
 walk(128,512 if stage&1 else 256);s=state(r)
 assert s.mode==1 and s.cam_x==1088 and s.p.x//256>=1300,(stage,'right extent',s.mode,s.cam_x,s.p.x//256)
 assert any(a.active and (meta['actor_definitions'][a.definition]['bank'],meta['actor_definitions'][a.definition]['address'])==roster[stage] for a in s.actors),(stage,'boss retired while scrolling')
 assert all(576<=a.x//256<1344 for a in s.actors if a.active),(stage,'boss escaped right traversal')
 r.capture('boss-rush-right-'+str(stage+1)+'.png')
 walk(64);s=state(r)
 assert s.mode==1 and s.cam_x==576 and s.p.x//256<=584,(stage,'left extent',s.mode,s.cam_x,s.p.x//256)
 assert int.from_bytes(r.read('video_cache_faults'),'big')==0
 r.capture('boss-rush-left-'+str(stage+1)+'.png')
 r.run(55,128);r.run(240)
 s=state(r);assert bytes(s.actors)!=before,'Boss AI must run before the forced combat fixture'
 assert all(576<=a.x//256<1344 for a in s.actors if a.active),(stage,'boss escaped arena')
 # Avoid an invincibility-flash frame in the review captures.
 while not state(r).frame&4:r.run(1)
 r.capture('boss-rush-'+str(stage+1)+'.png')
 for frame in range(1800):
  s=state(r)
  if s.mode==3:break
  assert s.round==7 and 576<=s.cam_x<=1088 and s.cam_y==64
  if frame%60==0:
   q=s.actors[23];q.active=1;q.definition=pickup;q.source=159;q.state=q.hit=0;q.hp=0
   q.x=s.p.x+8*256;q.y=s.p.y+8*256;q.vx=q.vy=0;s.p.invincible=10000;put(r,s)
  r.run(1)
 else:raise AssertionError(('Boss did not reach shop',stage,s.mode))
 reward=1000+stage*500;assert s.coins==coins+reward,(stage,s.coins,coins,reward)
 r.run(90);assert state(r).coins==coins+reward,'Reward must be paid exactly once'
 # Buy a key after every victory through the ordinary shop inventory.
 s=state(r);s.shop_item=4;s.previous_input=0;put(r,s)
 # item-grid slot 4 is KEY (confirmed from the native shop table).
 oldkeys=r.read('container_keys',1)[0];tap(2)
 assert r.read('container_keys',1)[0]==oldkeys+1,(stage,'key purchase',state(r).shop_item)
 purchased=state(r).coins;tap(8);s=state(r)
 assert s.coins==purchased and r.read('container_keys',1)[0]==oldkeys+1
 cases.append(dict(boss=stage+1,reward=reward,shop=True,inventory_carried=True,death_updates=frame))
assert state(r).mode==6 and r.read('boss_rush',4)==bytes([0,8,1,1])
r.close();report=dict(passed=True,cases=cases,arena={'x':576,'width':768,'camera_y':64,'floor_y':256,'scroll_range':[576,1088],'start_x':944,'start_camera_x':832,'walking_boss_floor_checked':True},rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='All eight native AI routines, three-screen horizontal traversal in both directions, persistent bosses, fixed round, original pickup-triggered fatal combat and delayed death callbacks, reward once, shop purchase after every boss including final, carried inventory and ending. POW fixtures do not prove weapon-only balance or natural completion.')
(ROOT/'reports/boss-rush-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
