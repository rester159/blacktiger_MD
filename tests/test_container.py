#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/container_oracle.json').read_text());data=json.loads((ROOT/'reference/container.json').read_text())
for key,path in [('trace_sha256','reference/container_oracle_events.txt'),('lua_sha256','tools/container_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 (tmp/'stub.c').write_text('#include "assets.h"\n#include "container.h"\nvolatile u16 loot_random;\nconst u16 container_coin_values[4]={50,100,500,1000};\nconst u8 container_initial[8][8]='+str(data['round_contents']).replace('[','{').replace(']','}')+';\nvoid restart(int round,int seed,u8 *out){loot_random=seed;container_round(round);for(int i=0;i<8;i++)out[i]=container_content(33+i);}\n')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/container.c'),str(tmp/'stub.c'),'-o',str(tmp/'c.dylib')],check=True)
 lib=C.CDLL(str(tmp/'c.dylib'));lib.container_shuffle.restype=C.c_uint16;out=(C.c_uint8*8)();count=0
 for line in (ROOT/'reference/container_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,contents,seed=line.split('|');c=ref['cases'][int(case)]
  actual=lib.container_shuffle(c['round'],c['seed'],out)
  assert (bytes(out).hex(),actual)==(contents,int(seed)),(c,bytes(out).hex(),actual,contents,seed)
  count+=1
 lib.container_new();lib.restart(3,451,out);first=bytes(out);lib.restart(3,12345,out)
 assert bytes(out)==first and C.c_uint16.in_dll(lib,'loot_random').value==12345
 report={'passed':True,'source_shuffle_cases':count,'same_round_contents_preserved':True,'scope':'Eight round tables and eight-swap RNG algorithm, with two original RNG updates per intercepted task yield. Exact global startup scheduling is not covered. Container opening, keys, traps and rewards are not yet implemented.'}
 (ROOT/'reports/container-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
