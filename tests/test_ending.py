"""Compare the native ending sequencer with every original observed update."""
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/ending_oracle.json').read_text())
for key,path in [('trace_sha256','reference/ending_oracle_events.txt'),('lua_sha256','tools/ending_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
by_tick={};palette=0
for line in (ROOT/'reference/ending_oracle_events.txt').read_text().splitlines():
 f=line.split('|')
 if f[0] in ('WAIT','COMPLETE'):continue
 if f[0]=='PALETTE':f.append(str(palette));palette+=1
 by_tick.setdefault(int(f[1]),[]).append(f)
class Ending(C.Structure):_fields_=[('tick',C.c_uint16),('index',C.c_uint16),('active',C.c_uint8),('palette',C.c_uint8),('scene',C.c_uint8),('complete',C.c_uint8)]
with tempfile.TemporaryDirectory() as folder:
 target=Path(folder)/'ending.dylib'
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/ending.c'),'-o',str(target)],check=True)
 lib=C.CDLL(str(target));lib.ending_start();native=Ending.in_dll(lib,'ending');text=(C.c_uint8*896).in_dll(lib,'ending_text');dirty=C.c_uint32.in_dll(lib,'ending_dirty_rows')
 expected=bytearray([32]*896);pal=255;scene=0;done=0;characters=0
 for tick in range(ref['ticks']+1):
  rows=0;dirty.value=0
  for f in by_tick.get(tick,[]):
   if f[0]=='TEXT':
    cell=int(f[2])-64;expected[cell]=int(f[3]);rows|=1<<(cell//32);characters+=1
   elif f[0]=='CLEAR':expected[64:]=bytes([32]*832);rows=0x0ffffffc
   elif f[0]=='PALETTE':pal=int(f[-1])
   elif f[0]=='HIDE':scene=2
   elif f[0]=='SCENE':scene=1
   elif f[0]=='END':done=1
  assert lib.ending_step()==done,(tick,'completion')
  assert bytes(text)==expected,(tick,'text')
  assert (native.palette,native.scene,native.complete)==(pal,scene,done),(tick,'presentation')
  assert dirty.value==rows,(tick,'dirty rows')
 assert lib.ending_step()==1 and native.tick==ref['ticks']
 lib.ending_reset();assert not native.active and not native.complete and native.palette==255
report=dict(passed=True,updates=ref['ticks']+1,characters=characters,palette_steps=palette,dirty_rows=True,source_set=ref['source_set'],scope='Every source-observed task-relative update, character cell, page clear, palette index, scene switch and terminal event, compiled production C. Board scheduler and physical display cadence are separate.')
(ROOT/'reports/ending-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
