"""Round 2 unreachable shopkeeper placement and right-edge escape, in the linked ROM."""
import hashlib,json
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100)
def tap(key):r.run(8,key);r.run(8)
# Real Debug menu: Home -> Debug -> level 2, with all switches ON.
for key in (8,16,16,32,32,64,128,64,128,8,32,32,32,8):tap(key)
assert state(r).round==1 and state(r).p.exploration

def place(x,y):
 s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
 s.mode=1;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0
 s.cam_x=max(0,min(x-112,1792));s.cam_y=max(0,min(y-144,800));put(r,s);r.run(90)

# Fixed 1B4C never constructs Round 2's (640,928) shopkeeper: its row is filed under
# start-area cell 25, which no camera that can see it probes (MAME sweep of 1B4C).
# Standing beside the placement must show no old man and must not start a rescue.
place(592,896)
s=state(r)
assert not any(a.active and abs(a.x//256-640)<=16 and 880<=a.y//256<=944 for a in s.actors),'unreachable source shopkeeper spawned'
r.capture('level2-no-buried-shopkeeper.png')
for _ in range(60):
 r.run(1,128);assert state(r).mode!=8,'rescue started at the unreachable shopkeeper placement'
place(1992,512);s=state(r)
assert (s.p.x//256,s.p.y//256)==(1992,528)
r.capture('level2-right-ledge.png')
steps=[]
for frames,keys in ((25,65),(50,16),(15,65),(40,16),(40,65)):
 r.run(frames,keys);r.run(2);s=state(r)
 steps.append(dict(frames=frames,keys=keys,x=s.p.x//256,y=s.p.y//256,climbing=bool(s.p.climb)))
assert any(step['climbing'] for step in steps),'nearby poles cannot be climbed'
assert s.mode==1 and s.p.x//256<1800,'player cannot leave the right ledge'
r.capture('level2-ledge-route-left.png');r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),unreachable_shopkeeper=[640,928],shopkeeper_spawned=False,right_ledge_route=steps,scope='Injected player starting positions at the two reported locations; normal actor spawns, collisions and controller input thereafter. Jumping left via the poles also leaves this ledge; horizontal wrap has its own regression. Not a complete level playthrough.')
(ROOT/'reports/level2-routes-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
