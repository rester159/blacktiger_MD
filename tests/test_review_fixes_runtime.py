"""Reported playability issues: real inputs plus controlled cartridge fixtures."""
import hashlib,json,struct,ctypes as C
from test_runtime import ROOT,Runner,state,put,check_video_cache
from test_skeleton_runtime import fixture
rom=ROOT/'out/release/rom.bin';checks=[]
def boot():
 r=Runner(rom);r.run(100);r.start_game();r.run(30);return r
def pause(r):
 s=state(r);s.mode=2;put(r,s);r.run(20);return state(r)
def check(name,ok):
 assert ok,name
 checks.append(name)
r=boot()
# The opening's two adjacent source walls can be revealed with normal attacks.
r.run(27,64);r.run(4)
for _ in range(8):r.run(3,2);r.run(24)
check('opening left walls reveal through normal attack input',r.read('world_opened',1)[0]&24==24)
s=state(r);check('opening wall rewards remain visible and collectible',any(a.active and a.state==1 and a.definition==19 for a in s.actors))
r.capture('review-opening-walls.png')
r.run(25,64);r.run(20)
check('opening wall rewards collect through movement',state(r).time>180)
r.close()
# Real Level 2 boss location; the checkpoint must wrap into map space.
r=boot();s=pause(r);s.round=1;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(50)
s=pause(r);s.mode=4;s.mode_timer=0;s.cam_x=848;s.cam_y=48;s.p.lives=3;put(r,s);r.run(1000);s=state(r)
check('level 2 boss respawn remains alive for 1000 refreshes',(s.mode,s.p.lives,s.p.y//256)==(1,2,128))
r.capture('review-level2-respawn.png');r.close()
# Both plant variants use the poison handler. Inventory antidotes prevent it.
for constructor in (0x8000,0x81a2):
 r=boot();slot,row,level=fixture(r,0,2,constructor,approach=32,wait_frames=240)
 for antidotes in (1,0):
  s=pause(r);r.write('shop_antidotes',0,bytes([antidotes]));r.write('shop_poison',0,b'\0');r.write('status_gate',0,b'\0')
  for _ in range(300):
   s=state(r);a=s.actors[slot];s.mode=1;s.p.exploration=0;s.p.x=a.x;s.p.y=a.y;s.p.vx=s.p.vy=0;s.p.invincible=1000;put(r,s);r.run(1)
   if r.read('status_gate',1)!=b'\0':break
  check('plant %x consumes protection %d'%(constructor,antidotes),r.read('shop_antidotes',1)==b'\0' and bool(r.read('shop_poison',1)[0])==(not antidotes))
 s=pause(r);s.p.invincible=0;s.p.x=128*256;s.p.y=896*256;s.cam_x=16;s.cam_y=752
 for a in s.actors:a.active=0
 for i in range(160):s.spawned[i]=2
 put(r,s);r.run(30);r.capture('review-poison-%x.png'%constructor)
 s=state(r);s.mode=1;put(r,s);r.write('player_daggers',0,bytes(162));r.run(3,2);r.run(5)
 check('poison suppresses dagger volley %x'%constructor,not any(r.read('player_daggers',162)[i*18+14] for i in range(9)))
 s=pause(r);s.mode=3;s.coins=1000;s.shop_item=10;s.previous_input=0;put(r,s);r.run(10);r.capture('review-shop.png');r.run(3,2);r.run(8)
 check('purchased antidote cures poison %x'%constructor,r.read('shop_poison',1)==b'\0')
 r.close()
# All three dragon colors, using the same public Boss Rush preparation path.
for stage,profile in ((2,1),(5,2),(7,3)):
 r=boot();s=pause(r);r.write('boss_rush',0,bytes([1,stage,0,0]));s.round=7;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(30)
 s=pause(r);s.p.invincible=0;s.actors[0].x=(s.cam_x+64)*256;s.actors[0].y=(s.cam_y+64)*256;put(r,s);r.run(20)
 check('dragon %d has full boss health bar'%profile,r.read('hud_boss_present',1)==b'\1' and r.read('hud_boss_fill',1)==bytes([(3,6,8)[profile-1]]))
 keys=struct.unpack('>20H',r.read('body_keys',40))
 check('dragon %d uses its own source palette texture'%profile,any(k!=65535 and k//2048==profile and k%2048>=1536 for k in keys))
 r.capture('review-dragon-%d.png'%profile)
 s=state(r);s.actors[0].life=1;s.actors[0].hp=1;put(r,s);r.run(12)
 check('dragon %d bar reflects all health layers'%profile,r.read('hud_boss_fill',1)==b'\1')
 s=state(r);s.actors[0].active=0;put(r,s);r.run(12)
 check('dragon %d bar clears with boss removal'%profile,r.read('hud_boss_present',1)==b'\0')
 r.close()
# Fixed camera, live palace flames: inspect the actual background VRAM.
r=boot();s=pause(r);s.round=7;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(40)
s=pause(r);s.cam_x=560;s.cam_y=112;put(r,s);r.run(40)
frames=[]
for phase in (0,1):
 r.write('bonus_phases',0,bytes([phase]*4));r.run(20);check_video_cache(r,state(r));frames.append(r.frame.copy());r.capture('review-torches-%d.png'%phase)
check('palace torches animate at a stationary camera',(frames[0]!=frames[1]).any())
check('palace animation has no cache faults',r.read('video_cache_faults')==b'\0\0')
r.close()
report=dict(passed=True,checks=checks,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),scope='Normal input opening-wall reveal/collection; controlled boss checkpoint, plant contacts, antidote purchase, dragon palettes and layered HUD, stationary-camera torch VRAM. Not a full natural playthrough.')
(ROOT/'reports/review-fixes-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
