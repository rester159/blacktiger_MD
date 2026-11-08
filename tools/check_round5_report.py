#!/usr/bin/env python3
"""Recheck the November 2 hardware report against the exact published v1.9.6.

Isolated injected wall fixtures, not a natural route or a console test.
"""
import sys,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tests'))
import test_hidden_runtime as t
from run_rom import Runner
rompath=root/'dist/blacktiger_MD_v1.9.6.bin'
assert hashlib.sha256(rompath.read_bytes()).hexdigest()=='b53aea19996347237ff892c9a994a96c5951dd8d523a2a56904a3ccf101972a3','This diagnostic targets the published v1.9.6 ROM'
assert hashlib.sha256((root/'dist/blacktiger_MD_v1.9.6-symbols.txt').read_bytes()).hexdigest()=='f5300053e572b7fc0f80b4151c2f9ac7da0140ca82b5ae5220d6a176e2adc8c9','Use the matching released symbols'
def release_runner(*args):
 r=Runner(rompath,skip_boot=False)
 r.symbols={v[2]:int(v[0],16) for l in (root/'dist/blacktiger_MD_v1.9.6-symbols.txt').read_text().splitlines() if len(v:=l.split())>=3}
 aliases={}
 for n,a in r.symbols.items():
  if '.lto_priv.' in n:aliases.setdefault(n.split('.lto_priv.')[0],[]).append(a)
 for n,a in aliases.items():
  if len(a)==1:r.symbols.setdefault(n,a[0])
 r.run(700)
 start=r.start_game
 def legacy_start(*args,**kwargs):r.run(3,32);r.run(3);return start(*args,**kwargs)
 r.start_game=legacy_start
 return r
import ctypes as C,struct
r=release_runner();r.run(100);r.start_game();r.run(20);t.rom=rompath.read_bytes();cases=[]
for patch in t.contract['rounds'][4]:
 t.enter(r,4)
 rows=[struct.unpack_from('>4H',t.rom,r.symbols['spawn4']+i*8) for i in range(t.metadata['rounds'][4]['spawns'])]
 row=next(i for i,v in enumerate(rows) if v[3]==patch['persistent'] and t.metadata['actor_definitions'][v[2]]['kind']==9)
 x,y,d,_=rows[row];slot=t.place(r,4,row,x,y)
 for _ in range(5):t.fire(r,slot)
 r.run(8);s=t.state(r);s.mode=2;t.put(r,s);r.run(30);s=t.state(r);a=s.actors[slot]
 v=(C.c_uint8*65536).in_dll(r.lib,'vram')
 def word(at):return (v[at^1]<<8)|v[(at+1)^1]
 index=0;found=[]
 for _ in range(80):
  at=0xf400+index*8;sy=(word(at)&511)-128;sx=(word(at+6)&511)-128;tile=word(at+4)&2047
  if (sx,sy)==(a.x//256-s.cam_x,a.y//256-s.cam_y):
   found.append(any(v[(tile*32+i)^1] for i in range(128)))
  index=word(at+2)&127
  if not index:break
 kind=(t.metadata['actor_definitions'][d]['address']-0xb7da)//23
 assert found and any(found)==bool(kind),(patch,kind,found)
 r.capture('v196-round5-wall-%d.png'%patch['persistent'])
 cases.append(dict(persistent=patch['persistent'],x=x,y=y,kind=kind,nontransparent_sprite=any(found)))
r.close()

# Read original arcade placement bytes independently of generated native data.
from arcade_source import Source
source=Source();source_rows=set()
for p in struct.unpack('<33H',source.read(5,source.word(None,0x1e07+8),66))[1:]:
 for i in range(128):
  raw=source.read(5,p+i*8,8)
  if raw[:2]==b'\xff\xff':break
  x,y,pc,bank,persistent=struct.unpack('<HHHBB',raw)
  if bank>7 or not 0x100<=pc<0xc000:break
  if bank==2 and 0xb7da<=pc<=0xb8d7 and (pc-0xb7da)%23==0:
   source_rows.add((x,y,persistent,(pc-0xb7da)//23))
assert source_rows=={(c['x'],c['y'],c['persistent'],c['kind']) for c in cases}
assert sum(c['kind']==0 for c in cases)==3

report=dict(passed=True,cases=cases,rom_sha256=hashlib.sha256(t.rom).hexdigest(),scope='Released ROM with matching symbols. Isolated nearby-position and five projectile injections. Checks SAT and sprite pixels after reveal; not a natural playthrough or hardware test.')
(root/'reports/round5-released-wall-visual-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
