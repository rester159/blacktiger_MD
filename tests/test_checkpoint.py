#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/checkpoint_oracle.json').read_text());data=json.loads((ROOT/'reference/checkpoint.json').read_text())
for key,path in [('trace_sha256','reference/checkpoint_oracle_events.txt'),('lua_sha256','tools/checkpoint_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 (tmp/'stub.c').write_text('#include "assets.h"\nconst u16 checkpoint_grid[8][32][2]='+str(data['grids']).replace('[','{').replace(']','}')+';\nconst u8 checkpoint_wide[8]={'+','.join(map(str,data['wide']))+'};\n')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/checkpoint.c'),str(tmp/'stub.c'),'-o',str(tmp/'c.dylib')],check=True)
 lib=C.CDLL(str(tmp/'c.dylib'));lib.checkpoint_lookup.argtypes=[C.c_uint8,C.c_uint16,C.c_uint16,C.POINTER(C.c_uint16),C.POINTER(C.c_uint16)];x=C.c_uint16();y=C.c_uint16();count=0
 for line in (ROOT/'reference/checkpoint_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,ex,ey=line.split('|');c=ref['cases'][int(case)];lib.checkpoint_lookup(c['round'],c['x'],c['y'],C.byref(x),C.byref(y))
  assert (x.value,y.value)==(int(ex),int(ey)),(c,x.value,y.value,ex,ey)
  count+=1
 report={'passed':True,'source_lookup_cases':count,'player_offset':data['player_offset'],'scope':'All 32 cells for all eight rounds, region boundaries, 16-bit coordinate wrapping and both original player-save destinations. Native game is single-player; ongoing camera movement is a separate port.'}
 (ROOT/'reports/checkpoint-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
