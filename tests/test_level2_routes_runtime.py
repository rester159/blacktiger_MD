"""Reported level-2 shopkeeper placement and right-edge escape, in the linked ROM."""
import hashlib,json
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100)
def tap(key):r.run(8,key);r.run(8)
# Real Debug menu: Home -> Debug -> level 2, with all switches ON.
for key in (32,8,16,16,32,32,64,128,64,128,8,32,32,32,8):tap(key)
assert state(r).round==1 and state(r).p.exploration

def place(x,y):
 s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
 s.mode=1;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0
 s.cam_x=max(0,min(x-112,1792));s.cam_y=max(0,min(y-144,800));put(r,s);r.run(90)

# Only inject the starting position; the original spawn and controller contact
# must place and rescue the shopkeeper without modifying an actor or collider.
place(592,896)
s=state(r);npc=next(a for a in s.actors if a.active and a.source==37)
assert (npc.x//256,npc.y//256)==(640,896),'shopkeeper is inside the ice platform'
r.capture('level2-shopkeeper-fixed.png')
for _ in range(60):
 r.run(1,128)
 if state(r).mode==8:break
else:raise AssertionError('standing player cannot rescue corrected shopkeeper')
s=state(r);assert s.rescue_kind==2
for _ in range(700):
 r.run(1)
 if state(r).mode==3:break
else:raise AssertionError('shopkeeper did not open shop')
# Exit the actual shop, then reproduce the reported ledge.
tap(1)
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
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),shopkeeper_position=[640,896],rescue_opens_shop=True,right_ledge_route=steps,scope='Injected player starting positions at the two reported locations; normal actor spawns, collisions and controller input thereafter. Jumping left via the poles also leaves this ledge; horizontal wrap has its own regression. Not a complete level playthrough.')
(ROOT/'reports/level2-routes-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
