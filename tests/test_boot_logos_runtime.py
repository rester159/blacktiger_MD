"""Linked-cartridge boot order, animated palettes, jingle, skips and title spacing."""
import ctypes as C,hashlib,json,re,struct
import numpy as np
from test_runtime import ROOT,Runner,state
manifest=json.loads((ROOT/'reference/boot_logos.json').read_text())
for item in manifest['files']:
 assert hashlib.sha256((ROOT/item['destination']).read_bytes()).hexdigest()==item['sha256']
r=Runner(ROOT/'out/release/rom.bin',skip_boot=False);r.audio_capture=[]
seen=[];durations={1:0,2:0};palettes={1:set(),2:set()};audio={1:[],2:[]};captures=set()
for _ in range(720):
 old=int.from_bytes(r.read('boot_stage'),'big');r.audio_capture=[];r.run(1)
 stage=int.from_bytes(r.read('boot_stage'),'big');tick=int.from_bytes(r.read('boot_tick'),'big')
 if stage in (1,2):
  if stage not in seen:seen.append(stage)
  durations[stage]+=1
  palettes[stage].add(r.read('shinobi_logo_cram' if stage==1 else 'capcom_logo_cram',32))
  if old==stage:audio[stage].extend(r.audio_capture)
  target=(stage,20 if stage==1 else 80)
  if tick>=target[1] and target not in captures:
   r.capture('boot-sega.png' if stage==1 else 'boot-capcom.png');captures.add(target)
 if r.read('boot_done',1)==b'\x01':break
else:raise AssertionError('boot stalled')
assert seen==[1,2],seen
assert 209<=durations[1]<=214 and 359<=durations[2]<=400,durations
kit=(ROOT/'src/capcom_logo.c').read_text()
def words(name):return [int(x,0) for x in re.findall(r'0x[\da-fA-F]+|\d+',re.search(name+r'\[[^]]+\]\s*=\s*\{([^}]+)',kit)[1])]
base=words('base_pal');glint=words('glint_pal')
expected={tuple(sum(max(0,((w>>i)&15)-2*k)<<i for i in (0,4,8)) for w in base) for k in range(8)}
expected.update(tuple(glint[i:i+16]) for i in range(0,96,16))
assert len(palettes[1])==20 and palettes[2]=={struct.pack('>16H',*p) for p in expected}
pcm={s:np.frombuffer(b''.join(a),dtype=np.int16).astype(np.float64) for s,a in audio.items()}
rms={s:float(np.sqrt(np.mean(a*a))) for s,a in pcm.items()}
assert rms[1]<5 and rms[2]>100,(rms,'SEGA is silent; Capcom must play its FM jingle')
r.run(30);assert state(r).mode==0 and r.read('frontend',2)==b'\0\0'
assert not np.any(r.frame[208:216]),'blank row between copyright lines'
r.capture('title-spaced.png')
# An Arcade start still enters the original Black Tiger game intro.
r.run(4,8);r.run(4);r.run(4,4);r.run(4);r.run(4,8);r.run(20)
assert state(r).mode==9,'original game intro must remain'
r.close()
# Skip from either logo, consume held Start, then prove the title is idle.
for wanted in (1,2):
 r=Runner(ROOT/'out/release/rom.bin',skip_boot=False)
 for _ in range(650):
  r.run(1)
  if int.from_bytes(r.read('boot_stage'),'big')==wanted and int.from_bytes(r.read('boot_tick'),'big')>=60:break
 else:raise AssertionError(('missing phase',wanted))
 r.run(8,8);assert r.read('boot_done',1)==b'\0','held Start must not leak into title'
 r.run(80);assert r.read('boot_done',1)==b'\x01'
 assert state(r).mode==0 and r.read('frontend',2)==b'\0\0'
 # No stuck FM note after early jingle exit.
 r.audio_capture=[];r.run(90);tail=np.frombuffer(b''.join(r.audio_capture),dtype=np.int16).astype(float)
 assert np.sqrt(np.mean(tail[-20000:]**2))<10
 r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),order=['SEGA black background','CAPCOM with FM jingle','Black Tiger title'],phase_video_frames=durations,palette_states={s:len(p) for s,p in palettes.items()},audio_rms=rms,skip_cases=2,footer_gap_pixels=8,scope=__doc__)
(ROOT/'reports/boot-logos-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
