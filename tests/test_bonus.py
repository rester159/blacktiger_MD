"""Native contact/camera policy against captured original-ROM outputs."""
import ctypes as C,json,hashlib,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/bonus_oracle.json').read_text());data=json.loads((ROOT/'reference/bonus.json').read_text())
for key,path in [('trace_sha256','reference/bonus_oracle_events.txt'),('lua_sha256','tools/bonus_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'genesis.h').write_text('')
 rows=['{0,0,'+','.join(map(str,[*r['camera'],r['return_x_low_add'],0]))+',{{0,0},{0,0}}}' for r in data['rounds']]
 (p/'stub.c').write_text('#include "bonus.h"\n#include "player_motion.h"\nGame game;PlayerMotion player_motion;const Round rounds[8]={0};u8 player_contact(s16 x,s16 y,u8 w,u8 h){return 0;}\nconst BonusRound bonus_rounds[8]={'+','.join(rows)+'};\n')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(p),'-I'+str(ROOT/'inc'),str(ROOT/'src/bonus.c'),str(p/'stub.c'),'-o',str(p/'bonus.dylib')],check=True)
 lib=C.CDLL(str(p/'bonus.dylib'));u=C.c_uint16;ptr=C.POINTER(u)
 lib.bonus_destination.argtypes=[C.c_uint8,C.c_uint8,ptr,ptr,ptr,ptr];lib.bonus_gate.argtypes=[C.c_uint8]*3;lib.bonus_gate.restype=C.c_uint8
 count=0
 for line in (ROOT/'reference/bonus_oracle_events.txt').read_text().splitlines()[:-1]:
  fields=line.split('|');c=ref['cases'][int(fields[1])];expected=list(map(int,fields[2:]))
  if c['kind']==0:assert lib.bonus_gate(c['jumping'],c['falling'],c['returning'])==expected[0]
  else:
   x,y,sx,sy=map(u,[c['x'],c['y'],c['saved_x'],c['saved_y']]);lib.bonus_destination(c['round'],c['alternate'],C.byref(x),C.byref(y),C.byref(sx),C.byref(sy));assert [x.value,y.value,sx.value,sy.value]==expected[:4]
  count+=1
 report=dict(passed=True,source_cases=count,scope='Native gate and camera selection only; production integration is checked by bonus-runtime-tests.')
 (ROOT/'reports/bonus-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
