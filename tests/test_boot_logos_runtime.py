"""Source-only startup, held Start isolation, and the original Black Tiger intro."""
import hashlib,json
from test_runtime import ROOT,Runner,state
rom=ROOT/'out/release/rom.bin'
for held in (False,True):
 r=Runner(rom,skip_boot=False)
 for _ in range(120):
  r.run(1,8 if held else 0)
  if int.from_bytes(r.read('boot_tick'),'big')>=1:break
 else:raise AssertionError('Startup did not begin')
 if held:
  r.run(10,8)
  assert r.read('boot_done',1)==b'\0','held Start leaked into menu'
 r.run(100)
 assert r.read('boot_done',1)==b'\1' and state(r).mode==0
 assert r.read('frontend',2)==b'\0\0','startup selected a menu item'
 for name in ('sega_chant_pcm','shinobi_logo_tiles','capcom_logo_tiles'):
  assert name not in r.symbols, 'Borrowed boot asset linked: '+name
 r.run(4,2);r.run(4);r.run(4,8);r.run(4);r.run(4,2);r.run(20)
 assert state(r).mode==9,'Original Black Tiger game intro missing'
 r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),held_start_isolated=True,black_tiger_intro_retained=True,third_party_boot_assets_absent=True,scope=__doc__)
(ROOT/'reports/boot-logos-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
