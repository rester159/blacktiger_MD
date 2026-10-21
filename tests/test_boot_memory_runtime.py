"""Cold boot, heap integrity and repeated sprite-cache epochs in NTSC/PAL emulation."""
import hashlib,json,tempfile
from pathlib import Path
from test_runtime import ROOT,Runner,state,put
rom=ROOT/'out/release/rom.bin';results=[]
for region in ('U','E'):
 with tempfile.TemporaryDirectory() as folder:
  data=bytearray(rom.read_bytes());data[0x1f0:0x200]=region.encode().ljust(16,b' ')
  path=Path(folder)/'region-test.bin';path.write_bytes(data)
  r=Runner(path);r.run(100);assert r.read('boot_done',1)==b'\x01'
  r.start_game();r.run(40)
  assert state(r).mode==1,(region,state(r).mode)
  start=state(r).frame
  # Repeated stationary attacks cross the byte-sized sprite epoch repeatedly.
  s=state(r);s.p.invincible=60000;put(r,s);r.run(900,2)
  assert (state(r).frame-start)&65535>=850,(region,'gameplay stalled')
  assert r.read('video_cache_faults',2)==b'\0\0'
  heap=int.from_bytes(r.read('heap',4),'big')&65535
  end=int.from_bytes(r.read('heapEnd',4),'big')&65535
  cursor=heap;free=0;blocks=0
  while cursor<end:
   size=(r.ram[cursor^1]<<8)|r.ram[(cursor+1)^1];length=size&65534
   assert length>=2 and cursor+length<=end,(region,'heap corruption',hex(cursor),size)
   if not size&1:free+=length-2
   cursor+=length;blocks+=1
  assert cursor==end and free>0,(region,'exhausted heap',free)
  results.append(dict(region=region,free_heap_bytes=free,heap_blocks=blocks,frames=900))
  r.close()
report=dict(passed=True,cases=results,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),scope='Genesis Plus GX cold boots with region header U and E, 900 attack refreshes, intact heap and tile cache. Does not validate physical Model 3, flashcart, or PAL hardware modified to 60 Hz.')
(ROOT/'reports/boot-memory-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
