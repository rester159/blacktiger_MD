"""Instruction-level stack sampling on the hash-pinned ARM64 GPGX core.

Exercises cold boot, repeated attacks and transitions to all eight rounds.
The PAL-ID case changes the reported hardware region while retaining 60 Hz VDP
 timing. It does not emulate the electrical behavior of a modified console.
"""
import ctypes as C
import hashlib,json,subprocess
from test_runtime import ROOT,Runner,state,put
from run_rom import CORE
expected='20903bdbe7dde068ebc55eabb00a2bf45238a254f24fbe2285d12389520dbba0'
assert hashlib.sha256(CORE.read_bytes()).hexdigest()==expected,'Unsupported core for internal opcode hook'
source=ROOT/'tools/stack_watch_hook.c';library=ROOT/'.local/stack_watch_hook.dylib'
subprocess.run(['cc','-O2','-dynamiclib',str(source),'-o',str(library)],check=True)
h=C.CDLL(str(library));h.begin.argtypes=[C.c_void_p]*3
results=[]
for label,region in [('NTSC',0x80),('PAL-ID-60Hz',0xc0)]:
 r=Runner(ROOT/'out/release/rom.bin',skip_boot=False)
 C.c_uint8.in_dll(r.lib,'region_code').value=region
 assert C.c_int.in_dll(r.lib,'vdp_pal').value==0
 C.c_uint32.in_dll(h,'lowest').value=65536
 base=C.cast(r.lib.m68k_get_reg,C.c_void_p).value-0x55aac
 assert h.begin(C.addressof(C.c_uint8.in_dll(r.lib,'m68k')),base+0x1fefb0,C.cast(r.lib.m68k_get_reg,C.c_void_p))==0
 try:
  r.run(700);r.start_game();r.run(900,2)
  for level in range(8):
   s=state(r);s.mode=2;put(r,s);r.run(20)
   s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=9;put(r,s)
   r.run(150);r.run(150,130)
  lowest=C.c_uint32.in_dll(h,'lowest').value
  heap_end=int.from_bytes(r.read('heapEnd',4),'big')&65535
  margin=lowest-heap_end
  assert margin>=256,(label,'insufficient sampled stack margin',margin)
  assert state(r).mode==1
  results.append(dict(region=label,lowest_sp=hex(lowest),heap_end=hex(heap_end),margin_bytes=margin,lowest_pc=hex(C.c_uint32.in_dll(h,'lowest_pc').value)))
 finally:
  h.end();r.close()
report=dict(passed=True,cases=results,core_sha256=expected,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope=__doc__+' Sampling is not a proof of worst-case stack use or physical console compatibility.')
(ROOT/'reports/stack-margin-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
