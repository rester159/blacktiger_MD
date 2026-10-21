#!/usr/bin/env python3
"""Cold boot and repeated-fire smoke test using GPGX or PicoDrive.

Only controller input is used, except the shared Runner skips the round notice.
No internal GPGX VDP symbols are needed. This does not validate real hardware.
"""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_runtime import state
from run_rom import ROOT,CORE,Runner
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--core',type=Path,default=CORE);a=p.parse_args()
rom=ROOT/'out/release/rom.bin';r=Runner(rom,core=a.core,skip_boot=False)
r.run(700);assert r.read('boot_done',1)==b'\x01'
r.start_game();start=state(r).frame;r.run(900,2)
assert state(r).mode==1 and (state(r).frame-start)&65535>=850
assert r.read('video_cache_faults',2)==b'\0\0'
name=a.core.stem;r.capture(name+'-attack.png')
report=dict(passed=True,core=str(a.core),core_sha256=hashlib.sha256(a.core.read_bytes()).hexdigest(),rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),boot_refreshes=700,attack_refreshes=900,scope=__doc__)
r.close();(ROOT/'reports'/(name+'-smoke.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
