"""Match boss segments to original Z80 HUD writes, including layer-transition timing."""
import ctypes as C,hashlib,json
import numpy as np
from test_runtime import ROOT,Runner,state,put
from arcade_source import Source
from extract import decode
from hud_assets import observed,color,rgb
source=Source();rom=ROOT/'out/release/rom.bin'
ref=json.loads((ROOT/'reference/boss_hud_oracle.json').read_text());trace=(ROOT/'reference/boss_hud_oracle_events.txt').read_bytes()
assert ref['source_set']==source.lock['aggregate_sha256'] and ref['trace_sha256']==hashlib.sha256(trace).hexdigest()
rows={}
for line in trace.decode().splitlines():
 if line.startswith('ROW|'):
  _,stage,life,count,attr,codes,attrs=line.split('|');rows[int(stage),int(life)]=(bytes.fromhex(codes),bytes.fromhex(attrs))
board=json.loads((ROOT/'assets/board.json').read_text())
chars=decode(b''.join(source.files[f['path']] for f in board['regions']['chars']['files']),board['layouts']['characters'])
_,pal,_=observed();banks=np.fromfile(ROOT/'res/generated/object_palette.bin',dtype='>u2').reshape(2,16)
available=[[i for i in range(1,16) if i not in (7,8,9,10)],list(range(1,16))]
def tile_pixels(r,x,y):
 v=(C.c_uint8*65536).in_dll(r.lib,'vram');at=0xc000+y*128+x*2;word=(v[at^1]<<8)|v[(at+1)^1]
 raw=np.array([v[((word&2047)*32+i)^1] for i in range(32)],np.uint8)
 return np.stack((raw>>4,raw&15),1).reshape(8,8),(word>>13)&3

def verify(r,stage,life):
 codes,attrs=rows[stage,life];cram=(C.c_uint16*64).in_dll(r.lib,'cram')
 for x,(code,attr) in enumerate(zip(codes[:31],attrs[:31])): # Column 31 belongs to the cave backdrop.
  expected=chars[code+((attr&224)<<3)];actual,bank=tile_pixels(r,x,4)
  assert np.array_equal(actual!=0,expected!=3),(stage,life,x,'source glyph shape/placement')
  if code==32:continue
  colors=[color(pal,768+(attr&31)*4+i) for i in range(3)]
  costs=[sum(min(sum((rgb(c)-rgb(banks[b][i]))**2) for i in available[b]) for c in colors) for b in range(2)]
  b=int(np.argmin(costs));assert bank==b+2
  for pen in range(3):
   best=banks[b][min(available[b],key=lambda i:sum((rgb(colors[pen])-rgb(banks[b][i]))**2))]
   packed=((int(best)>>1)&7)|(((int(best)>>5)&7)<<3)|(((int(best)>>9)&7)<<6)
   actual_colors={int(cram[bank*16+i]) for i in actual[expected==pen]}
   assert not actual_colors or actual_colors=={packed},(stage,life,x,pen,actual_colors,packed)
 for y in (3,4):
  for x in range(24,31):assert not tile_pixels(r,x,y)[0].any(),'Zenny remained over boss HUD'
checks=[]
for rush in (1,0):
 for stage in range(8):
  count=source.read(None,0x5db6+stage*2,1)[0]
  r=Runner(rom);r.run(100);r.start_game();r.run(30)
  s=state(r);s.mode=2;put(r,s);r.run(20)
  r.write('boss_rush',0,bytes([1,stage,0,0]));s=state(r);s.round=7;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(40)
  s=state(r);s.mode=2;s.p.invincible=0;put(r,s);r.run(20)
  if not rush:
   r.write('boss_rush',0,b'\0');s=state(r);s.round=stage;put(r,s);r.run(20)
  s=state(r);assert s.actors[0].active and s.actors[0].life==count,(rush,stage,s.actors[0].life,count)
  verify(r,stage,count)
  # Partial HP and pending hit reactions cannot remove a layer prematurely.
  for life in range(count,0,-1):
   for hp,status in ((1,0),(1,1)):
    s=state(r);s.actors[0].life=life;s.actors[0].hp=hp;s.actors[0].state=status;put(r,s);r.run(10);verify(r,stage,life)
  s=state(r);s.actors[0].life=0;s.actors[0].state=2;put(r,s);r.run(10);verify(r,stage,0)
  assert r.read('hud_boss_present',1)==b'\1','empty outlines vanished during defeat'
  s=state(r)
  for a in s.actors:a.active=0
  put(r,s);r.run(10)
  assert r.read('hud_boss_present',1)==b'\0'
  for x in range(7,23):assert not tile_pixels(r,x,4)[0].any(),'boss row not cleared after encounter'
  checks.append(dict(stage=stage+1,boss_rush=bool(rush),segments=count,source_style=hex(source.read(None,0x5db7+stage*2,1)[0])))
  r.close()
report=dict(passed=True,checks=checks,source_rows=len(rows),rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),scope=__doc__+' All eight bosses in regular and Boss Rush HUD contexts; source glyph shapes and placement, nearest stable Genesis colors, HP-only/pending-hit stability, empty defeat outlines and cleanup. Controlled emulator fixtures; no natural full-game playthrough.')
(ROOT/'reports/boss-hud-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
