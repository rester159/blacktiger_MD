"""Render native effects through the cartridge and exercise actual player events."""
import array,hashlib,json,math,wave
from test_runtime import ROOT,Runner,state,put
meta=json.loads((ROOT/'reference/sfx.json').read_text());ends={p['command']:p['updates'] for p in meta['programs']};command=0
for l in (ROOT/'reference/sfx_oracle_events.txt').read_text().splitlines():
 f=l.split('|')
 if f[0]=='CASE':command=int(f[1])
 elif f[0]=='END':ends[command]=max(ends.get(command,0),int(f[1]))
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(30)
s=state(r);s.mode=2;put(r,s);r.run(60)
# Controller output is consumed once, in order, even on paused frames. Stop
# before landing must clear an existing sustained effect and retain landing.
r.write('sfx_request',0,b'\x14');r.run(3)
s=state(r);s.sound_commands[0]=0x1f;s.sound_commands[1]=0x1c;s.sound_count=2;put(r,s);r.run(3)
assert state(r).sound_count==0
assert r.read('sfx_slots',22)[8]==0x1c,'ordered stop/landing output lost'
r.run(90);assert r.read('sfx_active',1)==b'\0','controller output replayed'
# A finite FM cue ends before the effects-only capture; pause prevents reselection.
r.write('music_request',0,b'\x32');r.run(650);assert r.read('music_active',1)==b'\0'
cases=[];preview=[]
for command in meta['commands']:
 r.audio_capture=[];r.write('sfx_request',0,bytes([command]));r.run((ends[command]+3)//4+25)
 samples=array.array('h',b''.join(r.audio_capture));peak=max(abs(v) for v in samples);rms=math.sqrt(sum(v*v for v in samples)/len(samples))
 assert rms>1 and peak<32767,(command,peak,rms)
 assert r.read('sfx_active',1)==b'\0',(command,'finite effect did not stop')
 if command in (2,0x1b,0x3a):preview.extend(samples)
 cases.append(dict(command=command,peak=peak,rms=round(rms,2)))
# Check the additional PSG mix against an active round track as well.
r.write('music_request',0,b'\x21');r.run(8);r.audio_capture=[]
for command in meta['commands']:
 r.write('sfx_request',0,bytes([command]));r.run((ends[command]+3)//4+25)
mixed=array.array('h',b''.join(r.audio_capture));mixed_peak=max(abs(v) for v in mixed);assert mixed_peak<32767,mixed_peak
r.close()
with wave.open(str(ROOT/'reports/sfx-preview.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(array.array('h',preview).tobytes())
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(30)
for _ in range(30):
 r.run(1,1)
 if r.read('sfx_slots',22)[8]==0x1b:break
else:raise AssertionError('jump did not select source 1B')
r.run(8)
for _ in range(30):
 r.run(1,2)
 if r.read('sfx_slots',22)[8]==0x3a:break
else:raise AssertionError('attack did not select source 3A')
s=state(r);s.mode=2;put(r,s);r.run(60);s=state(r);s.mode=1;s.time=0;s.clock=59;s.p.invincible=0;s.p.hp=1;put(r,s)
for _ in range(30):
 r.run(1)
 if state(r).mode==4:break
r.run(3);assert state(r).mode==4 and r.read('sfx_slots',22)[8]==2
assert r.read('music_active',1)==b'\1','death stopped FM music'
r.close();report=dict(passed=True,cases=cases,mixed_music_peak=mixed_peak,ordered_controller_output=True,player_jump=True,player_attack=True,player_death_stop_then_effect=True,death_preserves_music=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='All 36 native effects render non-silent/unclipped isolated cartridge audio and stop. Input-driven jump/attack and timeout death select witnessed source commands. Not waveform equivalence, full gameplay-event binding, sustained effects, or hardware/PAL listening.')
(ROOT/'reports/sfx-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','player_jump','player_attack','player_death_stop_then_effect','rom_sha256')}))
