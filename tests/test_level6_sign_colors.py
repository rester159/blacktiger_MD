"""Blue arcade direction signs retain all four distinct source shades."""
import hashlib,json
import numpy as np
from test_runtime import ROOT
from arcade_source import Source
from extract import decode
s=Source();board=json.loads((ROOT/'assets/board.json').read_text());tiles=decode(b''.join(s.files[v['path']] for v in board['regions']['tiles']['files']),board['layouts']['tiles'])
raw=s.read(13,0x8000,16384);scenery=np.load(ROOT/'res/generated/scenery5.npy');palette=np.fromfile(ROOT/'res/generated/pal5.bin',dtype='>u2')
expected={0:(0,4,5),2:(0,5,7),3:(0,4,6),4:(0,3,4),5:(0,2,3)}
count=0
for y in range(64):
 for x in range(128):
  idx=(x&15)|((y&15)<<4)|((x&112)<<4)|((y&48)<<7);lo,a=raw[idx*2:idx*2+2];code=lo+((a&7)<<8)
  if (a>>3)&15!=11 or code not in (0x4a6,0x4a7,0x4af):continue
  pens=tiles[code];pens=pens[:,::-1] if a&128 else pens
  actual=palette[scenery[y*16:y*16+16,x*16:x*16+16]]
  for pen,rgb in expected.items():
   word=rgb[0]*2+rgb[1]*32+rgb[2]*512
   assert np.all(actual[pens==pen]==word),(x,y,pen)
  count+=1
assert count==14,count
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),blue_signs=count,distinct_arrow_shades=4,scope=__doc__)
(ROOT/'reports/level6-sign-colors-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
