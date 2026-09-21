"""A camera change must present one complete old or new image, never a split."""
import hashlib,json
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
s=state(r);s.mode=2;s.cam_x=s.cam_y=128;s.p.x=s.p.y=-1024*256
for a in s.actors:a.active=0
for q in s.shots:q.active=0
put(r,s);r.run(20)
# Stable paused fixtures isolate scroll presentation from gameplay animation.
def digest():return hashlib.sha256(r.frame[32:].tobytes()).hexdigest()
checks=[]
for dx,dy in [(2,0),(0,2),(-2,0),(0,-2)]*8:
 old=digest();s=state(r);s.cam_x+=dx;s.cam_y+=dy;put(r,s);seen=[]
 for _ in range(6):r.run(1);seen.append(digest())
 new=digest();assert old!=new,(dx,dy)
 assert set(seen)<={old,new},('Split scroll presentation',dx,dy,seen)
 checks.append(dict(dx=dx,dy=dy,complete_frames=True))
r.close();report=dict(passed=True,cases=len(checks),rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual linked ROM output: 32 horizontal/vertical sub-tile scroll transitions, every captured playfield equals the complete old or new view. Paused fixtures isolate scroll tearing. Host compositor/display tearing requires interactive checking.')
(ROOT/'reports/presentation-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
