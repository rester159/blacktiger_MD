"""Pack 32x32 column strips, sharing identical 2 KiB blocks losslessly."""
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
 unique={};indices=[]
 for at in range(0,len(full),2048):
  block=bytes(full[at:at+2048]);indices.append(unique.setdefault(block,len(unique)))
 packed=b''.join(unique)
 assert b''.join(packed[i*2048:(i+1)*2048] for i in indices)==full
 (p/'object_patterns_packed.bin').write_bytes(packed)
 (ROOT/'src/sprite_atlas_index.inc').write_text('/* Generated lossless 2 KiB block lookup. */\nstatic const u16 sprite_atlas_blocks[1024]={'+','.join(map(str,indices))+'};\n')
 manifest=ROOT/'reports/assets.json'
 if manifest.exists():
  report=json.loads(manifest.read_text())
  report['outputs']['object_patterns_packed.bin']={'bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest()}
  manifest.write_text(json.dumps(report,indent=2)+'\n')
 print(f'Packed all 16384 cells losslessly; {len(full)-len(packed)-len(indices)*2} ROM bytes saved')
