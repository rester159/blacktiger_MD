#!/usr/bin/env python3
"""Bounded simulation catch-up, single presentation per blank, pause/input safety."""
import hashlib,json
from test_runtime import finish_clear,ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);cases=[]
for level in range(8):
 if level:
  s=state(r);s.mode=5;s.mode_timer=1;finish_clear(r,s);r.run(12)
 s=state(r);s.p.invincible=10000;s.p.hp=4;s.p.lives=3;put(r,s);r.run(30)
 start=state(r).frame;before=int.from_bytes(r.read('early_vblank_flushes'),'big')
 last=start;peak=0;present=int.from_bytes(r.read('pacing_presentations',4),'big')
 for _ in range(600):
  r.run(1,130);now=state(r).frame;step=(now-last)&65535;peak=max(peak,step);assert step<=3,(level,step);last=now
  shown=int.from_bytes(r.read('pacing_presentations',4),'big')
  assert (shown-present)&0xffffffff<=1,(level,'multiple presentations in a refresh')
  present=shown
 s=state(r);updates=(s.frame-start)&65535;flushes=(int.from_bytes(r.read('early_vblank_flushes'),'big')-before)&65535
 assert 0<updates<=603,(level,updates)
 assert int.from_bytes(r.read('vblank_flush_overruns'),'big')==0,level
 cases.append(dict(round=level+1,video_frames=600,logic_updates=updates,early_flushes=flushes,max_updates_per_video_frame=peak))
 s.mode=1;s.round=level;put(r,s)
s=state(r);s.mode=2;put(r,s);r.run(30);start=state(r).frame;r.run(600);paused=(state(r).frame-start)&65535
assert paused==600,paused
# A held Start must create one edge even if the previous frame was late.
r.run(3,8);r.run(10,8);assert state(r).mode==1,'held Start re-paused during catch-up'
r.run(3);r.run(3,8);assert state(r).mode==2,'second Start did not pause'
# An exceptional stall is bounded; no seconds-long fast-forward on resume.
s=state(r);s.mode=1;s.p.invincible=10000;put(r,s);r.run(10)
before=int.from_bytes(r.read('pacing_discarded_ticks',4),'big')
timer=int.from_bytes(r.read('vtimer',4),'big');r.write('vtimer',0,(timer+120).to_bytes(4,'big'))
last=state(r).frame
for _ in range(12):
 r.run(1);now=state(r).frame;assert (now-last)&65535<=3,'unbounded catch-up';last=now
assert int.from_bytes(r.read('pacing_discarded_ticks',4),'big')>before,'stall clamp was not exercised'
async_draws=int.from_bytes(r.read('pacing_async_presentations',4),'big')
prepared_ticks=int.from_bytes(r.read('pacing_prepared_ticks',4),'big')
r.close();assert async_draws>0 and prepared_ticks>0
report=dict(passed=True,cases=cases,async_presentations=async_draws,prepared_ticks=prepared_ticks,paused_updates=paused,observed_overruns=0,held_start_single_edge=True,exceptional_stall_bounded=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Eight 600-video-frame NTSC route samples, paused cadence, held Start, and injected 120-refresh clock stall. Up to three fixed simulation ticks per iteration, never multiple presentations per refresh. Hardware and PAL validation remain separate.')
(ROOT/'reports/frame-scheduler-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
