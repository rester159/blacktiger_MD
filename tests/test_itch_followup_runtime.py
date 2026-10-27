"""Linked snake poison and falling-rock sound regressions; injected native contacts."""
import hashlib,json,struct,sys
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
source=Source()
# The snake's contact selector is 0x26; it routes to poison, not immediate HP loss.
assert source.read(2,0xb732+13,3)==bytes([0x26,2,0])
assert source.word(None,0x4751+0x26*2)==0x481c
source.expect(None,0x4837,'3e263215e93e3c3219e9cdfb26')
source.expect(4,0xb39f,'3e3bcde203')
source.expect(4,0xb3e9,'3e1fcde2033e42cde203')
cases=[]
if len(sys.argv)==1 or sys.argv[1]=='snake':
 for antidotes,exploration in ((0,0),(1,0),(0,1)):
  r=Runner(ROOT/'out/release/rom.bin')
  try:
   r.run(100);r.start_game();r.run(20)
   slot,row,level=fixture(r,0,2,0xb67f)
   s=state(r);s.mode=2;put(r,s);r.run(30)
   s=state(r);a=s.actors[slot];x=a.x//256;y=a.y//256
   s.mode=1;s.p.x=a.x;s.p.y=a.y;s.p.vx=s.p.vy=0;s.p.armor=2;s.p.hp=4;s.p.invincible=0;s.p.exploration=exploration
   s.p.climb=1;s.time=100;s.clock=0
   for i,b in enumerate(s.actors):
    if i!=slot:b.active=0
   for q in s.shots:q.active=0
   put(r,s)
   motion=bytearray(struct.pack('>5H20B',(x-128)&65535,(y-144)&65535,128,144,0,*([0]*20)));motion[22]=1
   r.write('player_motion',0,motion);r.write('status_gate',0,b'\0');r.write('shop_antidotes',0,bytes([antidotes]));r.write('shop_poison',0,b'\0')
   start=s.frame
   for _ in range(40):
    r.run(1);s=state(r)
    if r.read('status_gate',1)[0] or ((s.frame-start)&65535)>=8:break
   poison=r.read('shop_poison',1)[0];left=r.read('shop_antidotes',1)[0]
   assert poison==(0x26 if not antidotes and not exploration else 0),('snake poison',poison,antidotes,exploration)
   assert left==0 and s.p.hp==4 and s.p.armor==2
   if not exploration:assert r.read('status_gate',1)[0]>0
   cases.append(dict(kind='snake',antidotes=antidotes,exploration=exploration,poison=poison))
  finally:r.close()
if len(sys.argv)==1 or sys.argv[1]=='rock':
 r=Runner(ROOT/'out/release/rom.bin')
 try:
  r.run(100);r.start_game();r.run(20)
  slot,row,level=fixture(r,0,4,0xb338)
  s=state(r);a=s.actors[slot];s.mode=1;s.p.x=a.x-32*256;s.p.y=a.y+128*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;s.p.exploration=1;put(r,s)
  # Hold player motion to exclude its own falling/landing sounds.
  motion=bytearray(struct.pack('>5H20B',(s.p.x//256-128)&65535,(s.p.y//256-144)&65535,128,144,0,*([0]*20)));motion[22]=1
  r.write('player_motion',0,motion)
  observed=set()
  for _ in range(500):
   r.run(1);s=state(r)
   assert r.read('player_motion_sound_count',1)[0]==0
   raw=r.read('sfx_slots',88)
   observed.update((raw[8],raw[52]))
   if not s.actors[slot].active:break
  assert 0x3b in observed,('rock source sounds',sorted(observed))
  cases.append(dict(kind='rock',commands=sorted(observed)))
 finally:r.close()
report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope=__doc__)
(ROOT/'reports/itch-followup-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
