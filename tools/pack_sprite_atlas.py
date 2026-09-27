"""Pack 32x32 column strips, sharing identical 512-byte blocks losslessly."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def pack_atlas(raw):
 assert len(raw)==16384*128
 result=bytearray()
 for base in range(0,16384,16):
  for pair in range(0,8,2):
   for column in range(4):
    at=(base+pair+(column>>1))*128+(column&1)*64
    result.extend(raw[at:at+64]);result.extend(raw[at+1024:at+1088])
 for key in range(16384):
  at=(key&0xfff0)*128+(key&7)*256+(key&8)*8
  assert result[at:at+64]+result[at+128:at+192]==raw[key*128:(key+1)*128]
 return result
if __name__=='__main__':
 p=ROOT/'res/generated';full=pack_atlas((p/'object_patterns.bin').read_bytes())
 # Keep full strips for the hero and ordinary actors: adjacent columns
 # remain contiguous for the renderer's single-transfer 32x32 fast path.
 # Dragon rows and alternate-color hero rows can share smaller blocks.
 packed=bytearray();unique={};indices=[]
 for group in range(1024):
  key=group*16;code=key%2048;palette=key//2048
  size=512 if code>=1536 or (palette and code<512) else 2048
  block=bytes(full[group*2048:(group+1)*2048])
  for at in range(0,2048,size):
   data=block[at:at+size];token=(size,data)
   if token not in unique:
    offset=len(packed);unique[token]=offset;packed.extend(data)
    if size==2048:
     for part in range(0,2048,512):unique.setdefault((512,data[part:part+512]),offset+part)
   offset=unique[token]
   indices.extend((offset+part)//512 for part in range(0,size,512))
 assert len(indices)==4096
 assert b''.join(packed[i*512:(i+1)*512] for i in indices)==full
 (p/'object_patterns_packed.bin').write_bytes(packed)
 (ROOT/'src/sprite_atlas_index.inc').write_text('/* Generated lossless 512-byte block lookup. */\nstatic const u16 sprite_atlas_blocks[4096]={'+','.join(map(str,indices))+'};\n')
 manifest=ROOT/'reports/assets.json'
 if manifest.exists():
  report=json.loads(manifest.read_text())
  report['outputs']['object_patterns_packed.bin']={'bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest()}
  manifest.write_text(json.dumps(report,indent=2)+'\n')
 print(f'Packed all 16384 cells losslessly; {len(full)-len(packed)-len(indices)*2} ROM bytes saved')
