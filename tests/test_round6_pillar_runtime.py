"""v1.9.9: Round 6 pillar high jump must not wake the golden dragon from below its arena."""
import hashlib,json,struct
from test_runtime import ROOT,Runner,state,put
UP,JUMP,RIGHT=16,1,128
rom=ROOT/'out/release/rom.bin';data=rom.read_bytes();checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
def setup(x,y,dragon_row):
 r=Runner(rom);r.run(100);r.start_game(exploration=True);r.run(20)
 s=state(r);s.round=5;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
 s=state(r);s.mode=2;s.cam_x=(x-112)&65535;s.cam_y=max(0,y-144);s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0;s.p.invincible=5000;s.previous_input=0
 for a in s.actors:a.active=0
 # Isolate the dragon row; every other Round 6 row stays dormant.
 for i in range(160):s.spawned[i]=0 if i==dragon_row else 2
 put(r,s);r.run(30);s=state(r);s.mode=1;put(r,s);r.run(30)
 return r
def dragon_awake(r,kinds):return any(a.active and kinds[a.definition] for a in state(r).actors)
def scroll_y(r):return int.from_bytes(r.read('player_motion',4)[2:4],'big')
# Source row: Round 6 cell 8, (1849,64), bank 3 constructor 991D (the golden dragon).
r=Runner(rom);sym=r.symbols;r.close()
kinds=data[sym['dragon_kinds']:sym['dragon_kinds']+256]
for i in range(160):
 x,y,d,k=struct.unpack_from('>4H',data,sym['spawn5']+i*8)
 if (x,y)==(1849,64):dragon_row=i;break
else:raise AssertionError('Round 6 dragon row missing')
check('dragon row is the source 991D dragon',kinds[struct.unpack_from('>4H',data,sym['spawn5']+dragon_row*8)[2]]==2)
# ZeroVolt's route: jump from the gap floor, catch the block in the floor gap,
# then the floating block above it, and hold Up + Jump from the top.
r=setup(1896,480,dragon_row)
def hold(n,first):
 low=999
 for f in range(n):
  r.run(1,UP|JUMP if f<first else UP);s=state(r);low=min(low,s.cam_y)
  assert not dragon_awake(r,kinds),('dragon woke from below',s.p.x//256,s.p.y//256,s.cam_y,scroll_y(r))
 # A frame can end mid-update (after motion, before the view), so compare at rest.
 r.run(10);s=state(r);assert s.cam_y==scroll_y(r),('view left the source scroll camera',s.cam_y,scroll_y(r))
 return low
hold(30,4);hold(60,0);hold(30,4);hold(60,0)
s=state(r);check('hero hangs from the floating Round 6 block',s.p.climb==1 and s.p.y//256<=380)
lowest=min(hold(50,6) for _ in range(4))
check('view holds at the source scroll camera, below the dragon band, through the jumps',lowest>=150)
check('dragon stays dormant after repeated pillar high jumps',not dragon_awake(r,kinds))
r.capture('round6-pillar-jump.png');r.close()
# The ordinary approach along the top corridor still wakes it.
r=setup(1500,96,dragon_row);woke=None
for f in range(400):
 r.run(1,RIGHT)
 if dragon_awake(r,kinds):woke=state(r).p.x//256;break
check('walking the top corridor wakes the dragon',woke is not None)
r.close()
# MAME, Round 1 start, Up+Jump: E032 stays 752 while hero screen Y (F403)
# runs 144..84..144, sampled every third update from the first rise.
MAME_SCREEN=[124,112,102,94,88,85,84,85,88,94,102,112,124,139,144]
r=Runner(rom);r.run(100);r.start_game();r.run(20)
for _ in range(600):
 if state(r).mode==1 and r.read('round_ready',1)==b'\0':break
 r.run(1)
start=state(r).cam_y;trace=[]
for f in range(70):
 r.run(1,UP|JUMP if f<5 else UP if f<40 else 0);s=state(r)
 assert s.cam_y==start,('view moved during a jump',f,s.cam_y,start)
 trace.append(s.p.y//256-s.cam_y)
# The MAME log samples every third frame starting at an arbitrary phase.
phases=[trace[k::3][:len(MAME_SCREEN)] for k in range(len(trace))]
check('Round 1 jump keeps the view fixed with the MAME hero screen arc',start==752 and MAME_SCREEN in phases)
r.capture('arcade-camera-jump.png');r.close()
report=dict(round1_jump_screen_y=trace,passed=True,checks=checks,dragon_row=dragon_row,view_low=lowest,corridor_wake_x=woke,rom_sha256=hashlib.sha256(data).hexdigest(),
 scope=__doc__+' MAME: during Up+Jump the arcade camera E032 stays fixed while the hero rises; a 1B4C sweep constructs this row only for camera Y<=96. Positions injected, enemies isolated; controller input thereafter.')
(ROOT/'reports/round6-pillar-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
