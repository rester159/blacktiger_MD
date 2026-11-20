"""Warm-reset boot from leftover RAM (itch.io v1.9.9 Model 3 / Mega Sg black screens).

SGDK's entry skips RAM clearing and initialized-data setup whenever the I/O
control registers read non-zero, as after a reset button press and on some
consoles at power-on. The port must still reach a running title and play from
any RAM contents. v1.9.9 crashed with an address error from random RAM."""
import hashlib,json,random,sys
from pathlib import Path
from test_runtime import ROOT,Runner,state
rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'out/release/rom.bin'
cases=[('kept',None),('ff',0xff),('zero',0)]+[(f'random{s}',s) for s in range(6)]
results=[]
for name,fill in cases:
 r=Runner(rom,skip_boot=False);r.run(200)
 if name.startswith('random'):
  rnd=random.Random(fill)
  for i in range(65536):r.ram[i]=rnd.randrange(256)
 elif fill is not None:
  for i in range(65536):r.ram[i]=fill
 r.lib.retro_reset()
 r.run(900);s=state(r);first=s.frame
 assert r.read('boot_done',1)==b'\x01',(name,'boot did not finish')
 assert s.mode==0,(name,'not at title',s.mode)
 r.run(60);s=state(r)
 assert (s.frame-first)&65535>=50,(name,'title stalled',first,s.frame)
 r.start_game();r.run(40);s=state(r)
 assert s.mode==1 and s.p.hp>0,(name,'start did not enter play',s.mode)
 results.append(dict(case=name,title_frame=first));r.close()
report=dict(passed=True,cases=results,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),scope='Genesis Plus GX warm resets (SGDK soft-reset entry) from kept, filled and random work RAM. Does not validate a physical Model 3, Mega Sg or flashcart.')
(ROOT/'reports/reset-boot-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
