"""Home menu setting and normal-input jumps across the pictured 64px step up."""
import hashlib,json
from test_runtime import ROOT,Runner,state,put

def tap(r,key):r.run(8,key);r.run(8)
def boot():
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);return r
r=boot();assert r.read('frontend',18)[17]==0
tap(r,32);tap(r,8);tap(r,128);tap(r,8)
assert r.read('frontend',2)==bytes([1,2])
for _ in range(7):tap(r,32)
tap(r,128);assert r.read('frontend',18)[17]==1
r.capture('v35-home-jump-assist.png')
tap(r,64);assert r.read('frontend',18)[17]==0
tap(r,2);assert r.read('frontend',18)[17]==1
tap(r,32);assert r.read('frontend',4)[3]==8
tap(r,8);assert r.read('frontend',2)[1]==1
tap(r,64);tap(r,8);r.skip_intro();assert state(r).mode==1 and r.read('frontend',18)[17]==1
r.close()
checks=[]
def run_case(home,assist,level,x,y=288,direction=128):
 r=boot();r.start_game(exploration=True);r.run(20)
 r.write('frontend',0,bytes([home]));r.write('frontend',17,bytes([assist]))
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
 s=state(r);s.mode=2;s.cam_x=(x-112)&65535;s.cam_y=144;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0;s.p.invincible=1000;s.previous_input=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 put(r,s);r.run(30)
 s=state(r);s.mode=1;put(r,s);r.run(1,direction)
 trace=[];landed=False;enabled=0
 for f in range(64):
  r.run(1,direction|1 if f<4 else direction);s=state(r)
  enabled|=r.read('player_motion_jump_assist',1)[0]
  trace.append([s.p.x//256,s.p.y//256,int(s.p.grounded)])
  if s.p.grounded and ((s.p.x//256)&2047)>=300 and 220<=s.p.y//256<=230:
   landed=True;break
 if home and assist and level==6:r.capture(f'v35-assisted-jump-{x}.png')
 r.close()
 return trace,landed,enabled
for x in (242,250,258,2298,-1798):
 original,old_landed,flag=run_case(1,0,6,x)
 assisted,landed,enabled=run_case(1,1,6,x)
 assert not flag and landed and not old_landed,(x,old_landed,landed,assisted)
 checks.append(dict(takeoff_x=x,original_lands=False,assist_lands=True,landing=assisted[-1],apex_y=min(p[1] for p in assisted)))
# Selecting the Home preference must not alter Arcade or another level.
for home,level in ((0,6),(1,5)):
 a,_,off=run_case(home,0,level,250);b,_,on=run_case(home,1,level,250)
 assert not off and not on and a==b,(home,level)
# Outside the takeoff strip, at a different height, and jumping away from the
# gap or straight up, the entire trajectory must match Original exactly.
unchanged=[]
for x,y,direction in ((200,288,128),(220,288,128),(274,288,128),(350,224,128),(250,280,128),(250,288,64),(250,288,0)):
 a,_,off=run_case(1,0,6,x,y,direction);b,_,on=run_case(1,1,6,x,y,direction)
 assert not off and not on and a==b,(x,y,direction)
 unchanged.append([x,y,direction])
report=dict(unchanged_level7_fixtures=unchanged,passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),checks=checks,menu_toggle=True,default_off=True,arcade_and_other_level_unchanged=True,scope=__doc__+' Initial positions injected and enemies suppressed to isolate the jump. Ordinary controller, collision, gravity and landing logic thereafter. No full playthrough.')
(ROOT/'reports/level7-jump-assist-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
