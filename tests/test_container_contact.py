#!/usr/bin/env python3
"""Compare the native contact-effect kernel with all six original handlers."""
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/container_contact_oracle.json').read_text());data=json.loads((ROOT/'reference/container.json').read_text())
for key,path in [('trace_sha256','reference/container_contact_oracle_events.txt'),('lua_sha256','tools/container_contact_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
class Contact(C.Structure):
 _fields_=[('coins',C.c_uint16),('invincible',C.c_uint16)]+[(k,C.c_uint8) for k in ('keys','hp','max_hp','opened','collected')]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 (tmp/'stub.c').write_text('#include "assets.h"\nvolatile u16 loot_random;\nconst u8 container_initial[8][8]={0};\nconst u16 container_coin_values[4]={'+','.join(map(str,data['coin_values']))+'};\n')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/container.c'),str(tmp/'stub.c'),'-o',str(tmp/'c.dylib')],check=True)
 lib=C.CDLL(str(tmp/'c.dylib'));lib.container_contact.argtypes=[C.c_uint8,C.POINTER(Contact)];lib.container_contact.restype=C.c_uint8;count=0
 for line in (ROOT/'reference/container_contact_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  tag,case,*values=line.split('|');assert tag=='CONTACT';c=ref['cases'][int(case)]
  keys,opened,collected,coins,hp,inv,mode,remaining,cursor,display=map(int,values)
  state=Contact(**{name:c[name] for name,_ in Contact._fields_});effect=lib.container_contact(c['content'],C.byref(state))
  assert (state.keys,state.opened,state.collected,state.coins,state.hp,state.invincible)==(keys,opened,collected,coins,hp,inv),(c,values)
  assert display==keys
  assert (mode,remaining,cursor)==((11,1,0xb247) if effect else (9,37,0xb215))
  if effect:assert effect==(2 if c['content']==0 else 3 if c['opened'] else 1)
  count+=1
 report={'passed':True,'source_contact_cases':count,'coin_values':data['coin_values'],'scope':'Six native contact effects compared with original handlers: key debit, opened/collected flags, coin word including wrap, healing and invulnerability clearing. Effect results queue the source animation transition. Kernel not yet integrated with gameplay inventory, animations or traps.'}
 (ROOT/'reports/container-contact-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
