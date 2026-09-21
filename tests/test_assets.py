#!/usr/bin/env python3
"""Validate complete exported worlds through an independent Genesis tile decoder."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def decode(raw):
 a=np.frombuffer(raw,np.uint8);p=np.empty(len(a)*2,np.uint8);p[0::2]=a>>4;p[1::2]=a&15;return p.reshape(-1,8,8)
def compose(round,mutate=False):
 p=ROOT/'res/generated';tiles=decode((p/f'bg{round}.bin').read_bytes());w,h=(1024,2048) if round==2 else (2048,1024)
 words=np.frombuffer((p/f'map{round}.bin').read_bytes(),'>u2').reshape(h//8,w//8).copy()
 if mutate:words[h//16,w//16]^=1
 palette=np.frombuffer((p/f'pal{round}.bin').read_bytes(),'>u2').astype(np.uint32)
 rgb=np.stack([(palette>>1)&7,(palette>>5)&7,(palette>>9)&7],1)*255//7
 assert words.min()>=16 and ((words&2047)-16).max()<len(tiles)
 assert ((words>>13)&3).max()<2
 frame=np.empty((h,w,3),np.uint8)
 for y,row in enumerate(words):
  for x,word in enumerate(row):
   tile=tiles[(word&2047)-16]
   if word&0x800:tile=tile[:,::-1]
   if word&0x1000:tile=tile[::-1,:]
   frame[y*8:y*8+8,x*8:x*8+8]=rgb[((word>>13)&3)*16+tile]
 return Image.fromarray(frame).resize((w//2,h//2))
def main():
 report=json.loads((ROOT/'reports/assets.json').read_text());checks=[]
 for name,expected in report['outputs'].items():
  b=(ROOT/'res/generated'/name).read_bytes();assert sha(b)==expected['sha256'] and len(b)==expected['bytes']
 checks.append('all asset output hashes')
 for r in range(8):
  expected=np.asarray(Image.open(ROOT/f'reports/round{r+1}.png'))
  assert np.array_equal(np.asarray(compose(r)),expected),f'round {r+1} Genesis decode'
  checks.append(f'round {r+1} every map pixel after reduction')
  collision=(ROOT/f'res/generated/collision{r}.bin').read_bytes();assert len(collision)==8192 and set(collision)<={0,1,2,3}
 checks.append('all collision maps have 8192 legal entries')
 assert not np.array_equal(np.asarray(compose(0,True)),np.asarray(Image.open(ROOT/'reports/round1.png')))
 checks.append('corrupt map tile negative control rejected')
 palette=np.frombuffer((ROOT/'res/generated/object_palette.bin').read_bytes(),'>u2');assert len(palette)==32 and palette[0]==palette[16]==0
 for r in range(8):
  for v in np.frombuffer((ROOT/f'res/generated/pal{r}.bin').read_bytes(),'>u2'):assert not v&0xf111
 checks.append('Genesis RGB333 and four palette lines')
 # Pinned pre-HUD sprite allocation (4657999); HUD changes must not recolor actors.
 assert sha((ROOT/'res/generated/object_palette.bin').read_bytes())=='a0cb487bb5002eeffdee4fc229798fbbcfa746e591a5657756710b2507fb2cbc'
 assert sha((ROOT/'res/generated/object_patterns.bin').read_bytes())=='57ba9b32a865803a02dcddd831ca95cd94f81879866ed49f7db97dfb0276d645'
 checks.append('pre-HUD hero/enemy palette and entire sprite atlas preserved')
 out={'passed':len(checks),'checks':checks};(ROOT/'reports/asset-tests.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
