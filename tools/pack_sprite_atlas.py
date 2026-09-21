"""Reorder existing pixels into 32x32 column strips; no new art or ROM growth."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def pack_atlas(raw):
 assert len(raw)==16384*128
 result=bytearray()
 for base in range(0,16384,16):
  for pair in range(0,8,2):
   for column in range(4):
    at=(base+pair+(column>>1))*128+(column&1)*64
    result.extend(raw[at:at+64]);result.extend(raw[at+1024:at+1088])
 assert len(result)==len(raw)
 # Every original 16x16 cell must round-trip, including pair/row boundaries.
 for key in range(16384):
  at=(key&0xfff0)*128+(key&7)*256+(key&8)*8
  assert result[at:at+64]+result[at+128:at+192]==raw[key*128:(key+1)*128]
 return result
if __name__=='__main__':
 p=ROOT/'res/generated';(p/'object_patterns_packed.bin').write_bytes(pack_atlas((p/'object_patterns.bin').read_bytes()))
 print('Packed all 16384 sprite cells losslessly; ROM size unchanged')
