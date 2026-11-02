#!/usr/bin/env python3
"""Real weapon collision against naturally reached undead emergence phases."""
import hashlib,json,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
checks=[]
for variant,constructor in enumerate((0x8000,0x8389,0x89c6)):
 for phase in (0,2,3):
  for weapon in ('full_strength_shot','dagger'):
   r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
   slot,row,level=fixture(r,0,0,constructor,wait_frames=600)
   for _ in range(300):
    raw=r.read('zombies',16*24)
    if raw[slot*16+13]==phase:break
    s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(1)
   else:raise AssertionError(('phase not reached',variant,phase))
   s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
   raw=bytearray(r.read('zombies',16*24));assert raw[slot*16+13]==phase
   struct.pack_into('>H',raw,slot*16+2,100);raw[slot*16+4]=raw[slot*16+5]=0;r.write('zombies',0,raw)
   a=s.actors[slot];a.hit=0;hp=a.hp;before=s.score
   for i,b in enumerate(s.actors):
    if i!=slot:b.active=0
   for q in s.shots:q.active=0
   for i in range(160):s.spawned[i]=2
   # Medium actors check daggers on odd gameplay ticks, before pots.
   s.frame=10;s.p.weapon=4;s.p.invincible=10000;s.p.vx=s.p.vy=0
   # Freeze a native dagger/full-strength shot sample at the visible body's hit rectangle.
   if weapon=='dagger':
    raw=bytearray(18*9);struct.pack_into('>H',raw,2,100)
    struct.pack_into('>hh',raw,10,a.x//256+8,a.y//256+8);raw[14]=1
    r.write('player_daggers',0,raw)
   else:
    # Diagnostic projectile exercises the full-strength actor damage path.
    q=s.shots[0];q.active=1;q.life=30;q.damage=8;q.kind=0
    q.x=a.x+16*256;q.y=a.y+16*256;q.vx=q.vy=0
   s.mode=1;put(r,s);r.run(4);after=state(r).actors[slot]
   hit=after.hp<hp or after.state==1 or not after.active
   assert hit==(phase!=0),(variant,phase,weapon,hp,after.hp,after.state,a.hit,after.hit,after.definition,state(r).score-before,a.x//256,a.y//256,state(r).cam_x,state(r).cam_y,r.read('player_daggers',18).hex())
   checks.append(dict(variant=variant,phase=phase,weapon=weapon,damaged=hit))
   r.close()
report=dict(passed=True,cases=checks,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Injected weapon positioning at naturally reached hidden/partial/full emergence. Native daggers and diagnostic full-strength shots; not a controller-driven playthrough.')
(ROOT/'reports/undead-emergence-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
