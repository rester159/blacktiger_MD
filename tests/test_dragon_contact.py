#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/dragon_contact_oracle.json').read_text());profiles=json.loads((ROOT/'reference/dragon.json').read_text())
for key,path in [('trace_sha256','reference/dragon_contact_oracle_events.txt'),('lua_sha256','tools/dragon_contact_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
class Shape(C.Structure):_fields_=[('x',C.c_int8),('y',C.c_int8),('ww',C.c_uint8),('wh',C.c_uint8),('bw',C.c_uint8),('bh',C.c_uint8)]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/large_contact.c'),'-o',str(tmp/'c.dylib')],check=True)
 lib=C.CDLL(str(tmp/'c.dylib'));counts=[0,0,0]
 for line in (ROOT/'reference/dragon_contact_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,index,expected,pc=line.split('|');c=ref['cases'][int(index)];t=bytes.fromhex(profiles['templates'][(0x8045,0x9962,0x9b69).index(c['template'])]);shape=Shape(c['weak_x'],C.c_int8(t[33]).value,t[34],t[35],t[16],t[17])
  fn=lib.wide_player_contact if c['kind']==2 else lib.wide_weapon_contact
  result=fn(C.byref(shape),c['ax'],c['ay'],c['x'],c['y'],c['w'],c['h'],c['alternate'] if c['kind']==2 else c['kind'])
  assert result==int(expected),(c,result,expected,pc)
  counts[c['kind']]+=1
 report={'passed':True,'chain_cases':counts[0],'dagger_cases':counts[1],'player_cases':counts[2],'scope':'All three dragon shapes with both final-dragon weak-point offsets, weak-point hits versus blocked body hits, normal/alternate player geometry, asymmetric bounds and unsigned screen-coordinate wrapping. Native player currently selects normal posture; complete chain animation and its dynamic extents remain separate.'}
 (ROOT/'reports/dragon-contact-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
