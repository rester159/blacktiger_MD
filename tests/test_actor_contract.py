#!/usr/bin/env python3
"""Check witnessed constructor values in the linked native cartridge."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
from actor_contract import load
source=Source();contract=load(source)
evidence=json.loads((ROOT/'reference/constructors.json').read_text())
assert hashlib.sha256((ROOT/'reference/constructor_oracle_events.txt').read_bytes()).hexdigest()==evidence['oracle_sha256']
assert hashlib.sha256((ROOT/'tools/constructor_oracle.lua').read_bytes()).hexdigest()==evidence['lua_sha256']
rom=(ROOT/'out/release/rom.bin').read_bytes()
symbols={v[2]:int(v[0],16) for line in (ROOT/'out/release/symbol.txt').read_text().splitlines() if len(v:=line.split())>=3}
base=symbols['actor_defs'];definitions=json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions']
health=graphics=0
for d in definitions:
 c=contract[(d['bank'],d['address'])];a=rom[base+8*d['id']:base+8*d['id']+8]
 assert len(a)==8
 if c['contact']:
  for field in ('pool','half_width','half_height'):
   assert rom[symbols['actor_contact_'+field]+d['id']]==c['contact'][field]
 if c['health'] is not None:
  assert a[4]==c['health'],(d['id'],'health',a.hex(),c);health+=1
 if c['initial_frame']:
  f=c['initial_frame'];assert (int.from_bytes(a[:2],'big'),a[3],a[5])==(f['code'],f['palette'],f['pieces']),(d['id'],'graphics');graphics+=1
# The old width-as-health bug must fail: skeleton width=8 versus one hit point.
sk=next(r for r in evidence['records'] if (r['bank'],r['constructor'])==(0,0x93ed))
t=bytes.fromhex(sk['copies'][0]['bytes']);assert t[14]==1 and t[16]!=1
assert rom[base+8*sk['id']+4]==1
report={'passed':True,'constructors_with_copies':sum(bool(r['copies']) for r in evidence['records']),
        'linked_health_definitions':health,'linked_initial_graphics_definitions':graphics,
        'wrong_health_offset_negative':True,'rom_sha256':hashlib.sha256(rom).hexdigest(),
        'scope':'Initial states observed under four oracle profiles, not full AI or all constructor branches.'}
(ROOT/'reports/actor-contract-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
