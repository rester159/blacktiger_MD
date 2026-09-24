import sys,struct,json,statistics,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_runtime import finish_clear,ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);rows=[]
for level in range(8):
 if level:
  s=state(r);s.mode=5;s.mode_timer=1;finish_clear(r,s);r.run(12)
 s=state(r);s.p.invincible=10000;put(r,s);r.run(30);costs=[];start=state(r).frame;last=start;sample=-1
 for _ in range(180):
  r.run(1,130);s=state(r)
  last=s.frame;current=int.from_bytes(r.read('profile_samples'),'big')
  if current!=sample:costs.append(struct.unpack('>3H',r.read('frame_cost',6)));sample=current
 rows.append(dict(round=level+1,updates=(last-start)&65535,cost_median=[statistics.median(c[i] for c in costs) for i in range(3)],cost_max=[max(c[i] for c in costs) for i in range(3)]))
 s=state(r);s.mode=1;s.round=level;s.p.hp=4;s.p.lives=3;put(r,s)
r.close();report=dict(rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),subticks_per_second=76800,columns=['game','video','audio'],rounds=rows,scope='Injected round entries with 180 video frames of right+attack input; costs are sampled once per sixteen presentations, per outer-loop iteration (including catch-up ticks), approximate, and exclude VBlank/DMA processing. Update counts do not measure presentation cadence. Not a full-route benchmark.');(ROOT/'reports/performance-profile.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
