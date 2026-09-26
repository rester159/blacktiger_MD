"""Original spawn records, native dragon palette selection, and smooth section palettes."""
import json,struct,hashlib
import numpy as np
from test_runtime import ROOT,Runner,state,put
from test_skeleton_runtime import fixture
from arcade_source import Source
from extract import rgb,decode
source=Source();rom=(ROOT/'out/release/rom.bin').read_bytes()
meta=json.loads((ROOT/'reports/assets.json').read_text());defs={d['id']:d for d in meta['actor_definitions']}
constructors={0x8000:(2,1,'blue'),0x991d:(5,2,'red'),0x9b24:(7,3,'black')}
checks=[]
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(30)
for level in range(8):
 records=set();root=source.word(None,0x1e07+level*2)
 for ptr in struct.unpack('<33H',source.read(5,root,66))[1:]:
  for i in range(128):
   raw=source.read(5,ptr+i*8,8)
   if raw[:2]==b'\xff\xff':break
   x,y,pc,bank,persistent=struct.unpack('<HHHBB',raw)
   if bank==3 and pc in constructors:records.add((x,y,pc,persistent))
 native=set()
 for row in range(meta['rounds'][level]['spawns']):
  x,y,definition,persistent=struct.unpack_from('>4H',rom,r.symbols[f'spawn{level}']+row*8);d=defs[definition]
  if d['bank']==3 and d['address'] in constructors:native.add((x,y,d['address'],persistent))
 assert native==records,(level,records,native)
 for x,y,pc,persistent in sorted(records):
  expected,profile,color=constructors[pc];assert level==expected
  slot,row,actual_level=fixture(r,0,3,pc,approach=96,vertical=80,hold_position=True)
  assert actual_level==level
  s=state(r);s.actors[slot].x=(s.cam_x+64)*256;s.actors[slot].y=(s.cam_y+64)*256;put(r,s);r.run(30)
  keys=struct.unpack('>20H',r.read('body_keys',40))
  assert any(k!=65535 and k//2048==profile and k%2048>=1536 for k in keys)
  if level==7:
   r.write('shop_poison',0,b'\x26');r.run(20)
   keys=struct.unpack('>20H',r.read('body_keys',40))
   assert any(k!=65535 and k//2048==7 and k%2048>=1536 for k in keys),'black dragon did not switch to poison-safe art'
   r.write('shop_poison',0,b'\0');r.run(20)
  checks.append(dict(level=level+1,color=color,x=x,y=y,constructor=hex(pc),persistent=persistent))
r.close();assert len(checks)==3
# Verify the generated black-dragon atlas has no dithering within any section,
# uses the selected physical palette, and improves source-color error.
board=json.loads((ROOT/'assets/board.json').read_text());sprites=decode(b''.join(source.files[f['path']] for f in board['regions']['sprites']['files']),board['layouts']['sprites'])
atlas=(ROOT/'res/generated/object_patterns.bin').read_bytes();palette=np.array([rgb(v) for v in struct.unpack('>32H',(ROOT/'res/generated/object_palette.bin').read_bytes())]).reshape(2,16,3)
raw=np.frombuffer(atlas[3*2048*128+1536*128:4*2048*128],dtype=np.uint8).reshape(512,4,32)
pixels=np.stack((raw>>4,raw&15),axis=-1).reshape(512,4,8,8);decoded=np.empty((512,16,16),dtype=np.uint8)
for i,(x,y) in enumerate(((0,0),(0,8),(8,0),(8,8))):decoded[:,y:y+8,x:x+8]=pixels[:,i]
choices=np.frombuffer((ROOT/'res/generated/black_dragon_palettes.bin').read_bytes(),dtype=np.uint8)
mem=bytearray(2048);ptr=source.word(6,0x8136+7*2)
for _ in range(20):
 start,dest,count=struct.unpack('<HHH',source.read(6,ptr,6))
 if start==65535:break
 mem[dest-0xd800:dest-0xd800+count]=source.read(6,start,count);ptr+=6
colors=np.array([(mem[i]>>5,(mem[i]&15)>>1,(mem[i+1024]&15)>>1) for i in range(624,639)])
old_distance=((colors[:,None,:]-palette[1,1:][None,:,:])**2).sum(2)
old_mapping=np.r_[old_distance.argmin(1)+1,0]
new_error=old_error=0;exact_gray_pixels=gray_pixels=0
for base in range(0,512,16):
 for col in range(0,8,2):
  codes=np.array([base+col,base+col+1,base+col+8,base+col+9]);bank=choices[codes[0]]-2
  assert bank in (0,1) and np.all(choices[codes]==bank+2)
  for pen in range(15):
   mask=sprites[1536+codes]==pen
   if not mask.any():continue
   indices=decoded[codes][mask];assert len(set(indices))==1,('dithering',base,col,pen)
   actual=palette[bank,indices];target=colors[pen]
   new_error+=int(((actual-target)**2).sum())
   old_error+=int(((palette[1,old_mapping[pen]]-target)**2).sum())*int(mask.sum())
   if pen in (2,3,4,5):
    gray_pixels+=len(actual);exact_gray_pixels+=int(np.all(actual==target,axis=1).sum())
# Poison uses an independent atlas choice so skin colors cannot tint the dragon.
poison_choices=np.frombuffer((ROOT/'res/generated/poison_dragon_palettes.bin').read_bytes(),np.uint8)
poison_raw=np.frombuffer(atlas[7*2048*128+1536*128:8*2048*128],np.uint8).reshape(512,128)
poison_pens=np.stack((poison_raw>>4,poison_raw&15),axis=-1)
assert not np.isin(poison_pens[poison_choices==2],[7,8,9,10]).any()
assert new_error<old_error,(new_error,old_error)
assert exact_gray_pixels>gray_pixels*.5,(exact_gray_pixels,gray_pixels)
report=dict(passed=True,spawns=checks,color_error_before=old_error,color_error_after=new_error,exact_gray_pixels=exact_gray_pixels,gray_pixels=gray_pixels,rom_sha256=hashlib.sha256(rom).hexdigest(),scope=__doc__)
(ROOT/'reports/dragon-colors-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
