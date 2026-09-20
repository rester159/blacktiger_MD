#!/usr/bin/env python3
"""Render every native FM program, including finite jingles, through YM2612."""
import array,hashlib,json,math
from test_runtime import ROOT,Runner,state,put
meta=json.loads((ROOT/'reference/music_conversion.json').read_text())
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20)
s=state(r);s.mode=2;put(r,s);r.run(30);cases=[]
for track in meta['tracks']:
 command=track['command'];r.write('music_request',0,bytes([command]));r.run(8)
 assert r.read('music_command',1)[0]==command
 r.audio_capture=[];r.run(120);samples=array.array('h',b''.join(r.audio_capture));peak=max(abs(v) for v in samples);rms=math.sqrt(sum(v*v for v in samples)/len(samples))
 assert rms>20,(command,rms)
 assert peak<32767,(command,peak)
 cases.append(dict(command=command,peak=peak,rms=round(rms,1)))
r.close();report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Two-second excerpts from all 25 FM programs produce non-silent, unclipped Genesis Plus GX audio. Complete waveform, timbre and hardware comparisons remain separate.')
(ROOT/'reports/music-catalog-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
