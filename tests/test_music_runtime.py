#!/usr/bin/env python3
"""All eight native FM tracks produce cartridge audio and keep display-clock tempo."""
import array,json,hashlib,math,wave
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(30);cases=[]
for level in range(8):
 if level:
  s=state(r);s.mode=5;s.mode_timer=1;put(r,s);r.run(20)
 assert r.read('music_round',1)[0]==level and r.read('music_active',1)[0]==1
 s=state(r);s.mode=2;put(r,s);r.run(40)
 start=int.from_bytes(r.read('music_tick'),'big');r.audio_capture=[];r.run(240)
 end=int.from_bytes(r.read('music_tick'),'big');elapsed=(end-start)&65535
 assert 999<=elapsed<=1002,(level,elapsed)
 pcm=b''.join(r.audio_capture);samples=array.array('h',pcm);rms=math.sqrt(sum(v*v for v in samples)/len(samples));assert rms>30,(level,rms)
 assert not any(abs(v)>=32767 for v in samples),(level,'clipped FM mix')
 if level==0:
  with wave.open(str(ROOT/'reports/music-preview.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(round(r.sample_rate));w.writeframes(pcm)
 cases.append(dict(round=level+1,source_ticks_per_240_frames=elapsed,rms=round(rms,1),peak=max(abs(v) for v in samples),clipped_samples=sum(abs(v)>=32767 for v in samples)))
 s=state(r);s.mode=1;s.round=level;put(r,s)
s=state(r);s.mode=4;s.mode_timer=300;put(r,s);r.run(20)
assert r.read('music_active',1)[0]==1
s=state(r);s.mode=1;put(r,s);r.run(3);assert int.from_bytes(r.read('music_tick'),'big')<20
s=state(r);s.mode=7;put(r,s);r.run(8);assert r.read('music_active',1)[0]==0
r.close();report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='All eight round-entry selections, non-silent FM audio after effects expire, wall-clock tempo while paused, and stop on game over. Boss/jingle selection and original PSG effects remain incomplete.')
(ROOT/'reports/music-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
