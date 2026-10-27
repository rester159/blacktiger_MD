"""Actual NPC contacts in parallax stages: dialogue rows survive queued scenery DMA."""
import ctypes as C,hashlib,json,struct,sys
from test_runtime import ROOT,Runner,state,put
rom=(ROOT/'out/release/rom.bin').read_bytes()
metadata=json.loads((ROOT/'reports/assets.json').read_text())
defs={d['id']:d for d in metadata['actor_definitions']}
glyphs=struct.unpack('>2048H',(ROOT/'res/generated/npc_dialogue_glyphs.bin').read_bytes())

def check(level,row):
 r=Runner(ROOT/'out/release/rom.bin')
 try:
  r.run(100);r.start_game();r.run(20)
  x,y,d,_=struct.unpack_from('>4H',rom,r.symbols[f'spawn{level}']+row*8)
  s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(100)
  s=state(r);s.mode=2;put(r,s);r.run(30)
  s=state(r);s.mode=1;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0;s.p.invincible=10000
  s.cam_x=(x-112)&65535;s.cam_y=max(0,min(y-144,800))
  for a in s.actors:a.active=0
  for q in s.shots:q.active=0
  for i in range(160):s.spawned[i]=2
  s.spawned[row]=0;put(r,s)
  for _ in range(120):
   r.run(1)
   if state(r).mode==8:break
  else:raise AssertionError(('NPC contact',level,row))
  v=(C.c_ubyte*65536).in_dll(r.lib,'vram')
  def read(at,n):return bytes(v[(at+i)^1] for i in range(n))
  checked=0;previous=None;stable=0
  for _ in range(650):
   r.run(1);s=state(r)
   if s.mode!=8:break
   seq=r.read('npc_sequence',8);page=seq[6]
   stable=stable+1 if page==previous else 0;previous=page
   if stable<6 or int.from_bytes(seq[:2],'big')<8:continue
   cells=struct.unpack_from('>128H',rom,r.symbols['npc_pages']+page*256)
   expected=struct.pack('>128H',*[glyphs[c] for c in cells])
   actual=b''.join(read(0xc000+(y+6)*128,64) for y in range(4))
   assert actual==expected,('scenery overwrote dialogue',level+1,row,page,list(seq),actual[:24].hex(),expected[:24].hex())
   for y in range(5,25):
    scroll=int.from_bytes(read(0xf000+y*32,2),'big')
    assert scroll==(0 if 6<=y<10 else (-(s.cam_x//2))&65535)
   checked+=1
   if checked==1:r.capture(f'dialogue-backdrop-{level+1}-{row}.png')
  assert checked>10 and s.mode in (1,3),('dialogue completion',level,row,checked,s.mode)
  # Shop exit rebuilds scenery; other rewards restore it immediately.
  if s.mode==3:r.run(3,1);r.run(3)
  s=state(r);s.mode=2;put(r,s);r.run(30)
  s=state(r)
  for y in range(5,25):
   assert int.from_bytes(read(0xf000+y*32,2),'big')==(-(s.cam_x//2))&65535
  return dict(round=level+1,row=row,kind=defs[d]['npc_kind'],dialogue_checks=checked,restored=True)
 finally:r.close()

if __name__=='__main__':
 if len(sys.argv)>1:pairs=[tuple(map(int,sys.argv[1:]))]
 else:
  # Symbol lookup requires an initialized core; run each encounter separately.
  r=Runner(ROOT/'out/release/rom.bin');pairs=[]
  for level in (4,6):
   for row in range(metadata['rounds'][level]['spawns']):
    d=struct.unpack_from('>H',rom,r.symbols[f'spawn{level}']+row*8+4)[0]
    if defs[d]['npc_kind']:pairs.append((level,row))
  r.close()
 result=dict(passed=True,cases=[check(*p) for p in pairs],rom_sha256=hashlib.sha256(rom).hexdigest(),scope=__doc__+' Injected proximity; native spawn/contact and complete dialogue, not a full level playthrough.')
 (ROOT/'reports/dialogue-backdrop-runtime-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
