#!/usr/bin/env python3
"""Early VBlank flushes stay in blanking and never double-step NTSC frames."""
import hashlib,json
from test_runtime import finish_clear,ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);cases=[]
for level in range(8):
 if level:
  s=state(r);s.mode=5;s.mode_timer=1;finish_clear(r,s);r.run(12)
 s=state(r);s.p.invincible=10000;s.p.hp=4;s.p.lives=3;put(r,s);r.run(30)
 start=state(r).frame;before=int.from_bytes(r.read('early_vblank_flushes'),'big')
 last=start;peak=0
 for _ in range(600):
  r.run(1,130);now=state(r).frame;step=(now-last)&65535;peak=max(peak,step);assert step<=1,(level,step);last=now
 s=state(r);updates=(s.frame-start)&65535;flushes=(int.from_bytes(r.read('early_vblank_flushes'),'big')-before)&65535
 assert 0<updates<=601,(level,updates)
 assert int.from_bytes(r.read('vblank_flush_overruns'),'big')==0,level
 cases.append(dict(round=level+1,video_frames=600,logic_updates=updates,early_flushes=flushes,max_updates_per_video_frame=peak))
 s.mode=1;s.round=level;put(r,s)
s=state(r);s.mode=2;put(r,s);r.run(30);start=state(r).frame;r.run(600);paused=(state(r).frame-start)&65535
assert paused==600,paused
r.close();assert sum(c['early_flushes'] for c in cases)>0
report=dict(passed=True,cases=cases,paused_updates=paused,observed_overruns=0,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Eight 600-video-frame NTSC route samples plus paused cadence; every opportunistic small-queue flush completed in VBlank. PAL retains strict scheduling. Hardware validation and worst-case full routes remain separate.')
(ROOT/'reports/frame-scheduler-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
