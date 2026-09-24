"""Controller-driven Debug switches, independent effects, and normal Play reset."""
import hashlib,json,ctypes as C
from test_runtime import ROOT,Runner,state,put
checks=[]
for flags in range(8):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100)
 def tap(mask):r.run(8,mask);r.run(8)
 tap(32);tap(8)
 if flags==7:r.capture('home-menu-v18.png')
 tap(128);assert r.read('frontend',3)[2]==2
 if flags==7:
  tap(8);r.capture('options-menu-v18.png');tap(1)
 for key in (16,16,32,32,64,128,64,128):tap(key)
 assert r.read('frontend',3)[2]==3
 tap(8);assert r.read('frontend',2)[1]==4
 assert r.read('frontend',16)[15]==1,'Framerate must default ON'
 # Framerate occupies the second row of the right column.
 tap(128);tap(32);assert r.read('frontend',14)[13]==3
 tap(2);assert r.read('frontend',16)[15]==0
 if flags!=0:tap(2)
 tap(64);tap(16);assert r.read('frontend',14)[13]==0
 if not flags&1:tap(2)
 tap(32)
 if not flags&2:tap(2)
 tap(128);tap(16)
 if not flags&4:tap(2)
 if flags==7:r.capture('debug-menu-v18.png')
 assert list(r.read('frontend',13)[10:13])==[bool(flags&1),bool(flags&2),bool(flags&4)]
 tap(64);tap(32);tap(32);assert r.read('frontend',14)[13]==4
 if flags==7:r.capture('debug-level-select-v18.png')
 tap(8);r.run(20);s=state(r)
 assert s.mode==1 and r.read('frontend',15)[14]==1 and s.p.exploration==bool(flags&1)
 start=s.time*60-s.clock;r.run(120);s=state(r);elapsed=start-(s.time*60-s.clock)
 assert elapsed==(0 if flags&4 else 120),(flags,'timer',elapsed)
 vram=(C.c_uint8*65536).in_dll(r.lib,'vram')
 def tile(x,y):
  a=0xc000+y*128+x*2
  return (vram[a^1]*256+vram[(a+1)^1])&2047
 # BG_A begins at 0xc000, leaving 1536 tiles minus 96 font tiles.
 expected_f=(0xc000//32-96)+ord('F')-32
 if flags:
  fps=int.from_bytes(r.read('debug_fps',2),'big')
  assert 0<fps<=60,('rendered FPS',fps)
  assert tile(25,0)==expected_f,('FPS overlay absent',tile(25,0))
  if flags==7:r.capture('debug-framerate-v18.png')
 else:assert tile(25,0)!=expected_f,'FPS OFF still draws overlay' 
 # Known projectile contact with the temporary spawn shield removed.
 s.mode=2;put(r,s);r.run(20);s=state(r)
 s.mode=1;s.cam_x=0;s.cam_y=688;s.p.x=128*256;s.p.y=896*256
 s.p.vx=s.p.vy=0;s.p.invincible=0;s.p.hp=1;s.p.armor=2
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 q=s.shots[0];q.active=q.enemy=1;q.life=30;q.damage=20;q.x=s.p.x+4096;q.y=s.p.y+4096;q.vx=q.vy=0
 lives=s.p.lives;put(r,s);r.run(20);s=state(r)
 if flags&1:assert (s.mode,s.p.hp,s.p.armor)==(1,1,2),(flags,'invincibility')
 else:
  assert s.mode==4,(flags,'debug off still protects')
  for _ in range(500):
   r.run(1);s=state(r)
   if s.mode==1:break
  assert s.mode==1 and s.p.lives==lives-(not bool(flags&2)),(flags,'infinite lives',s.p.lives)
 # Invincibility also prevents the timeout path from stripping armor when
 # Infinite Time is OFF; the two switches must not depend on one another.
 if flags==1:
  s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
  s.mode=1;s.time=0;s.clock=59;s.p.invincible=0;put(r,s);r.run(30);s=state(r)
  assert (s.mode,s.p.hp,s.p.armor)==(1,1,2),'timeout bypassed invincibility'
 # Even with Debug switches ON, ordinary Play clears the active debug session.
 s=state(r);s.mode=0;s.previous_input=0;put(r,s)
 r.write('frontend',0,bytes([1,1,0]));r.run(20);tap(8);r.skip_intro();r.run(20);s=state(r)
 assert s.mode==1 and not s.p.exploration and not r.read('frontend',15)[14]
 start=s.time*60-s.clock;r.run(120);s=state(r)
 assert start-(s.time*60-s.clock)==120
 checks.append(dict(flags=flags,invincibility=bool(flags&1),infinite_lives=bool(flags&2),infinite_time=bool(flags&4),normal_play_reset=True));r.close()
report=dict(passed=True,checks=checks,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope=__doc__)
(ROOT/'reports/debug-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
