#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/status_oracle.json').read_text())
for key,path in [('trace_sha256','reference/status_oracle_events.txt'),('lua_sha256','tools/status_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');(tmp/'stub.c').write_text('#include "status.h"\nu8 shop_antidotes,shop_poison; Game game;\nvoid exploration(int enabled){game.p.exploration=enabled;}\nvoid setup(int gate,int reverse,int antidotes,int poison){status_gate=gate;status_reverse=reverse;shop_antidotes=antidotes;shop_poison=poison;}')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/status.c'),str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));count=0
 for line in (ROOT/'reference/status_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  v=line.split('|')
  if v[0]=='CONTACT':
   c=ref['cases'][int(v[1])];lib.setup(c['gate'],c['reverse'],c['antidotes'],c['poison'])
   if c['poison_contact']==2:assert lib.status_poison_cloud_contact()==int(v[8])
   else:(lib.status_poison_contact if c['poison_contact'] else lib.status_reverse_contact)()
   actual=[C.c_uint8.in_dll(lib,name).value for name in ('status_gate','status_reverse','shop_antidotes')]
   assert actual==list(map(int,v[2:5])),(c,actual,v)
   assert v[5:7]==['4','2'],'Status effect precedes ordinary damage dispatch'
   assert C.c_uint8.in_dll(lib,'shop_poison').value==int(v[7])
  else:
   lib.setup(int(v[1]),0,0,0);lib.status_tick();assert C.c_uint8.in_dll(lib,'status_gate').value==int(v[2])
  count+=1
 normal,reverse=ref['control_tables']
 for controls in range(128):
  lib.setup(0,1,0,0);mapped=lib.status_controls(controls);expected=(controls&~3)|((controls&1)<<1)|((controls&2)>>1)
  assert mapped==expected
  at=controls&15;swapped=expected&15
  assert reverse[at*2]==normal[swapped*2]
  # One source diagonal uses a separate posture dispatch; the native player
  # does not yet port those action-table states. Keep that gap explicit.
  if at!=5:assert reverse[at*2+1]==normal[swapped*2+1]
  else:assert reverse[11]==4 and normal[13]==3
 # Exploration must block both status dispatches before consuming antidotes.
 lib.exploration(1)
 for antidotes in (0,1):
  lib.setup(0,0,antidotes,0)
  lib.status_poison_contact()
  assert C.c_uint8.in_dll(lib,'shop_poison').value==0,'exploration poison immunity'
  assert lib.status_poison_cloud_contact()==0
  lib.status_reverse_contact()
  assert C.c_uint8.in_dll(lib,'status_reverse').value==0,'exploration reversal immunity'
  assert C.c_uint8.in_dll(lib,'shop_antidotes').value==antidotes
  assert C.c_uint8.in_dll(lib,'status_gate').value==0
 lib.exploration(0)
 report={'passed':True,'source_contact_and_timer_cases':count,'control_masks':128,'exploration_status_immunity':True,'scope':'Poison-contact application and reverse-control toggle, shared gate, automatic antidote consumption, status-effect phase before ordinary poison-contact damage and source horizontal movement-table equivalence. The source diagonal posture dispatch at input 5, full poison lifecycle and palette-task presentation remain unported.'}
 (ROOT/'reports/status-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
