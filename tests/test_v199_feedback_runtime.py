#!/usr/bin/env python3
"""v1.9.9 itch.io feedback: stone-boss wake-up, post-defeat control, Pow vs chest flames.

Arcade evidence (MAME, natural Round 1 game with an injected camera):
- wake check 9FA6 passes, body plays 352/354/356 for 8/8/68 updates and acts 84
  updates later; the head (9D04) acts 44 updates later.
- after the final layer (5A38) the hero walks and jumps until the death animation
  ends and 5A4F starts the clear (frames 4418..4528).
- Pow (bank 4 B5A6) retires small-pool actors with contact code 0/2A/34, which
  includes every chest flame piece (templates 831A, contact 80).
"""
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,meta
RIGHT,JUMP=1<<7,1<<0
TRAP=18
pickup=next(d['id'] for d in meta['actor_definitions'] if d['bank']==4 and d['address']==0xb515)
rom=(ROOT/'out/release/rom.bin').read_bytes()
report={'passed':True,'scope':__doc__}

def segment(r,slot):return struct.unpack_from('>H',r.read('bosses',18*24),slot*18+8)[0]

def wake(constructor):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
 try:
  main,row,level=fixture(r,0,4,constructor,approach=160,vertical=32)
  s=state(r);s.mode=1;put(r,s)
  heads=[i for i in range(main+1,24) if s.actors[i].active and s.actors[i].source==row]
  # Each part runs its own 9FA6/9A8D check; time each from its own wake.
  changes={main:[],heads[0]:[]};last={k:segment(r,k) for k in changes}
  for t in range(400):
   s=state(r);s.p.invincible=10000;s.p.vx=0;s.p.x=s.actors[main].x-60*256;put(r,s);r.run(1)
   for k in changes:
    n=segment(r,k)
    if n!=last[k]:changes[k].append((t,n));last[k]=n
   if all(len(v)>=3 for v in changes.values()):break
  # The first change leaves the idle loop for the wake clip; the second is the first action.
  def acts(k):return changes[k][1][0]-changes[k][0][0]
  body_left,head_left=acts(main),acts(heads[0])
  assert (body_left,head_left)==(84,44),(hex(constructor),body_left,head_left,changes)
  return dict(constructor=hex(constructor),body_acts_after=body_left,head_acts_after=head_left)
 finally:r.close()

def post_defeat():
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
 try:
  slot,row,level=fixture(r,0,4,0x9eb1,approach=96,vertical=32)
  s=state(r);hp=s.p.hp
  q=s.actors[23];q.active=1;q.definition=pickup;q.source=159;q.state=q.hit=0;q.hp=0
  q.x=s.p.x+8*256;q.y=s.p.y+8*256;q.vx=q.vy=0;s.mode=1;s.p.invincible=0;s.p.vx=s.p.vy=0;put(r,s)
  for _ in range(60):
   r.run(1);s=state(r)
   if s.boss_dead:break
  else:raise AssertionError('boss not defeated')
  x0=s.p.x;y0=s.p.y;jumps=0;airborne=False;frames=0;left_room=0
  for t in range(400):
   r.run(1,RIGHT|(JUMP if t%40<4 else 0));s=state(r)
   if s.mode!=1:break
   frames+=1
   if not s.p.grounded and not airborne:jumps+=1
   airborne=not s.p.grounded
  else:raise AssertionError('clear never started')
  assert s.p.x>x0,'hero frozen after boss defeat'
  assert jumps>=2,('hero could not jump during the death animation',jumps)
  assert 100<=frames<=120,('defeat window differs from arcade ~110 updates',frames)
  return dict(free_updates=frames,jumps=jumps,moved_px=(s.p.x-x0)//256)
 finally:r.close()

def pow_flames():
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);r.write('progress_max_hp',0,b'\x05')
 try:
  masks=[rom[r.symbols[n]] for n in ('container_trap_pow','container_wave_pow')]+list(rom[r.symbols['dragon_wave_pow']:r.symbols['dragon_wave_pow']+2])
  assert masks==[63,45,63,45],masks
  r.write('container_opened',0,bytes(8));r.write('container_collected',0,bytes(8));r.write('container_keys',0,b'\x02')
  slot,row,level=fixture(r,0,1,0xacbe)
  s=state(r);s.actors[slot].life=0;s.p.invincible=10000;put(r,s)
  persistent=struct.unpack_from('>4H',rom,r.symbols['spawn'+str(level)]+8*row)[3]-33
  r.write('container_contents',persistent,bytes([16]))
  for _ in range(40):
   s=state(r);a=s.actors[slot];s.mode=1;s.p.x=a.x;s.p.y=a.y;s.p.vx=s.p.vy=0;s.clock=0;put(r,s);r.run(1)
  for _ in range(40):
   s=state(r);s.p.x=s.actors[slot].x-96*256;s.p.vx=s.p.vy=0;put(r,s);r.run(1)
  raw=r.read('container_traps',TRAP*24)
  live=[i for i in range(24) if raw[i*TRAP+14]]
  assert len(live)==6 and all(raw[i*TRAP+17]&0x80 for i in live),raw.hex()
  s=state(r);q=s.actors[23];q.active=1;q.definition=pickup;q.source=159;q.state=q.hit=0;q.hp=0
  q.x=s.p.x+8*256;q.y=s.p.y+8*256;q.vx=q.vy=0;put(r,s)
  for _ in range(30):
   r.run(1)
   if state(r).spawned[159]==2:break
  else:raise AssertionError('Pow not collected')
  raw=r.read('container_traps',TRAP*24)
  assert not any(raw[i*TRAP+14] for i in range(24)),'chest flames survived Pow'
  return dict(flames_before=6,flames_after=0,masks=masks)
 finally:r.close()

report['wake']=[wake(c) for c in (0x9eb1,0x9f16)]
report['post_defeat']=post_defeat()
report['pow_flames']=pow_flames()
report['rom_sha256']=hashlib.sha256(rom).hexdigest()
(ROOT/'reports/v199-feedback-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
