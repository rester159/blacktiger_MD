"""Compare native pot shuffle against 128 runs of the original Z80 routine."""
import ctypes as C, json, subprocess, tempfile, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/pots_oracle.json').read_text())
data=json.loads((ROOT/'reference/pots.json').read_text())
for key,path in [('trace_sha256','reference/pots_oracle_events.txt'),('lua_sha256','tools/pots_oracle.lua')]:
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 # Compile the production shuffle unchanged; discard unrelated runtime functions.
 src=(ROOT/'src/pots.c').read_text();src=src[src.index('static u8 rotate'):src.index('void pots_clear')]
 (tmp/'shuffle.c').write_text('#include "pots.h"\nconst u8 pot_initial[8][32]='+str(data['tables']).replace('[','{').replace(']','}')+';\n'+src)
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(tmp/'shuffle.c'),'-o',str(tmp/'p.dylib')],check=True)
 lib=C.CDLL(str(tmp/'p.dylib'));lib.pots_shuffle.restype=C.c_uint16;out=(C.c_uint8*32)();count=0
 for line in (ROOT/'reference/pots_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,contents,seed=line.split('|');c=ref['cases'][int(case)]
  actual=lib.pots_shuffle(c['round'],c['seed'],out)
  assert (bytes(out).hex(),actual)==(contents,int(seed)),c
  count+=1
 assert [len(x) for x in data['placements']]==[26,32,32,32,32,32,33,32]
 print(f'PASS: {count} original-ROM shuffle comparisons; 251 extracted placements.')
