"""Compare grouped boss SAT cells and uploaded pixels with the canonical atlas."""
import ctypes as C, hashlib, json, struct
from test_skeleton_runtime import ROOT, Runner, state, put, fixture
rom=(ROOT/'out/release/rom.bin').read_bytes()
atlas=(ROOT/'res/generated/object_patterns.bin').read_bytes()
checks=[]
for bank,constructor,family,stride,columns in [(3,0x8000,'dragon',20,8),(3,0x991d,'dragon',20,8),(3,0x9b24,'dragon',20,8),(1,0x98a3,'waveboss',16,4),(1,0x98e8,'waveboss',16,4)]:
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game()
 slot,_,_=fixture(r,0,bank,constructor,approach=0 if family=='dragon' else 32,vertical=0 if family=='dragon' else 64,wait_frames=300,hold_position=True)
 s=state(r);s.mode=2;s.cam_x=0;s.cam_y=0;s.p.x=s.p.y=-1024*256
 for i,a in enumerate(s.actors):
  if i!=slot:a.active=0
 for q in s.shots:q.active=0
 a=s.actors[slot];a.x=64*256;a.y=64*256;a.hit=0
 put(r,s);r.run(40)
 name='dragons' if family=='dragon' else 'wavebosses'
 raw=bytearray(r.read(name,stride*24));segment=struct.unpack_from('>H',raw,slot*stride+8)[0]
 # Sample each source alignment and facing across the animation catalogue.
 pending=list(range(len(json.loads((ROOT/('reference/'+family+'.json')).read_text())['segments'])));seen=set();cases=[]
 while pending:
  seg=pending.pop(0)
  if seg in seen or seg==65535:continue
  seen.add(seg);at=r.symbols[family+'_segments']+seg*10
  clip,n0,n1=struct.unpack_from('>IHH',rom,at);ptr,count=struct.unpack_from('>IH',rom,clip)
  if count:
   code,duration,pal,flip=struct.unpack_from('>HBBB',rom,ptr)
   signature=(flip,code&7)
   if signature not in [c[0] for c in cases]:cases.append((signature,seg,code,pal,flip))

 for _,seg,code,pal,flip in cases:
  struct.pack_into('>HH',raw,slot*stride,0,1000);struct.pack_into('>H',raw,slot*stride+8,seg);r.write(name,0,raw);r.run(40)
  sat=r.read('vdpSpriteCache',512);keys=struct.unpack('>20H',r.read('body_keys',40));vram=(C.c_uint8*65536).in_dll(r.lib,'vram');actual=[];sprites=0
  for i in range(64):
   y,size,link,attr,x=struct.unpack_from('>HBBHH',sat,i*8);tile=attr&2047
   if tile>=1088:
    assert size==15,('expected grouped 32x32 boss',family,size)
    key=keys[(tile-1088)//16];expected=b'';sprites+=1
    for col in range(4):
     start=(key+col//2)*128+(col%2)*64
     expected+=atlas[start:start+64]+atlas[start+1024:start+1088]
    assert bytes(vram[(tile*32+j)^1] for j in range(512))==expected
    for row in range(2):
     for col in range(2):actual.append((x-128+col*16,y-128+row*16,key+row*8+(1-col if attr&0x800 else col),bool(attr&0x800)))
   if not link:break
  expected=[(64+col*16,64+row*16,code+row*8+(columns-1-col if flip else col)+pal*2048,bool(flip)) for row in range(4) for col in range(columns)]
  assert sorted(actual)==sorted(expected),(family,constructor,seg,actual,expected)
  assert sprites==columns
  checks.append(dict(constructor=constructor,segment=seg,flip=flip,sprites=sprites,source_cells=columns*4))
 r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),checks=checks,scope='Five source boss profiles, source frame alignments/facings, original 16x16 geometry and every uploaded pixel; grouped into 32x32 hardware sprites.')
(ROOT/'reports/large-sprite-render-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
