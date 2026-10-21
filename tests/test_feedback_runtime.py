"""Regression fixtures for October itch.io feedback: delayed chest traps and idle weapon overlap."""
import hashlib,json,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
checks=[]
for height in (0,-96,-160):
 r.write('container_opened',0,bytes(8));r.write('container_collected',0,bytes(8));r.write('container_keys',0,b'\x02')
 slot,row,level=fixture(r,0,1,0xacd3)
 s=state(r);s.actors[slot].life=0;s.p.invincible=10000;put(r,s)
 r.write('container_traps',0,bytes(18*24));r.write('container_traps_occupied',0,b'\0')
 for _ in range(60):
  s=state(r);a=s.actors[slot];s.mode=1;s.p.x=a.x;s.p.y=a.y;s.p.vx=s.p.vy=0;put(r,s);r.run(1)
  if r.read('container_keys',1)==b'\x01':break
 else:raise AssertionError('chest did not open')
 chest_y=state(r).actors[slot].y//256
 for _ in range(100):
  s=state(r);a=s.actors[slot];s.p.x=a.x-64*256;s.p.y=a.y+height*256;s.p.vx=s.p.vy=0;put(r,s);r.run(1)
  raw=r.read('container_traps',18*24)
  active=[i for i in range(24) if raw[i*18+14]]
  if active:break
 else:raise AssertionError('no flames')
 ys=[struct.unpack_from('>h',raw,i*18+12)[0] for i in active]
 assert all(abs(y-(chest_y+16))<=4 for y in ys),(height,chest_y,ys)
 checks.append(dict(chest_departure_height=height,flame_y=ys,chest_y=chest_y))
# Verify actual SAT priority for every idle weapon tier and both facing directions.
s=state(r);s.mode=2;put(r,s);r.run(20)
rom=(ROOT/'out/release/rom.bin').read_bytes()
for face in (0,4):
 for tier in range(1,6):
  s=state(r);s.mode=2;s.p.x=128*256;s.p.y=896*256;s.cam_x=16;s.cam_y=752;s.p.weapon=tier;s.p.armor=2;s.p.invincible=0
  for a in s.actors:a.active=0
  for q in s.shots:q.active=0
  put(r,s);motion=bytearray(30);struct.pack_into('>5H',motion,0,16,752,112,144,0);motion[25]=motion[26]=face;motion[27]=1
  r.write('player_motion',0,motion);r.write('player_attack',0,bytes(12));r.run(25)
  h=struct.unpack_from('>5H2B2b',rom,r.symbols['hero_frames']+(480+face*8)*14)
  expected=h[4]+tier-1;sat=r.read('vdpSpriteCache',64*8)
  keys=struct.unpack('>80H',r.read('sprite_keys',160));y,size,link,attr,x=struct.unpack_from('>HBBHH',sat)
  assert size==5 and keys[((attr&2047)-1088)//4]&2047==expected,(face,tier,h,sat[:8].hex())
  if tier==1 and face==0:r.capture('feedback-idle-after.png')
  checks.append(dict(idle_weapon_tier=tier,facing=face,foreground_code=expected))
r.close()
report=dict(passed=True,checks=checks,rom_sha256=hashlib.sha256(rom).hexdigest())
(ROOT/'reports/feedback-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
