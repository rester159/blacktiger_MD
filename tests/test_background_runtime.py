"""Live background phases update resident Genesis tiles without moving the camera."""
import json,hashlib,struct
from test_runtime import ROOT,Runner,state,put,check_video_cache
rom=(ROOT/'out/release/rom.bin').read_bytes();cases=[]
for level in range(6):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(40)
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(100)
 ptr,count=struct.unpack_from('>IH',rom,r.symbols['bonus_rounds']+level*20)
 width=64 if level==2 else 128;height=128 if level==2 else 64
 for entered in (0,1):
  patch=next(rom[ptr+i*40:ptr+(i+1)*40] for i in range(count) if rom[ptr+i*40+2+entered*16:ptr+i*40+10+entered*16]!=rom[ptr+i*40+10+entered*16:ptr+i*40+18+entered*16])
  cell=int.from_bytes(patch[:2],'big');bank=patch[38]
  s=state(r);s.mode=2;s.cam_x=max(0,min((cell%width)*16-112,width*16-256));s.cam_y=max(0,min((cell//width)*16-96,height*16-224));put(r,s)
  r.write('bonus_entered',0,bytes([entered]));r.run(100);check_video_cache(r,state(r));seen=set()
  for sample in range(4):
   s=state(r);s.mode=3;put(r,s);r.run(15)
   s=state(r);s.mode=2;put(r,s);r.run(80)
   check_video_cache(r,state(r));seen.add(r.read('bonus_phases',4)[bank])
   assert int.from_bytes(r.read('video_cache_faults'),'big')==0
  assert seen=={0,1},(level,entered,bank,seen)
  cases.append(dict(round=level+1,alternate=entered,cell=cell,bank=bank,phases=sorted(seen)))
 r.close()
report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256(rom).hexdigest(),scope='Both animated tile phases in all six populated rounds and both doorway states, fixed camera, actual VRAM pattern/attribute comparisons and zero cache faults. Source task-relative cadence verified separately; whole-board scheduler equivalence remains unproven.')
(ROOT/'reports/background-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
