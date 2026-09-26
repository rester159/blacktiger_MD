#!/usr/bin/env python3
"""Validate complete exported worlds through an independent Genesis tile decoder."""
import json,hashlib,re,sys
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
 # The native activation search requires globally X-sorted spawn rows.
 source=(ROOT/'src/data.c').read_text()
 for r in range(8):
  rows=re.search(r'const Spawn spawn'+str(r)+r'\[\]=\{(.*?)\};',source).group(1)
  xs=[int(v) for v in re.findall(r'\{(\d+),',rows)]
  assert xs and xs==sorted(xs),(r,'spawn X order')
 checks.append('all eight spawn tables satisfy spatial search ordering')
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
 normalized_palette=bytearray((ROOT/'res/generated/object_palette.bin').read_bytes())
 assert palette[15]==0x888 and palette[1]==0
 normalized_palette[30:32]=b'\0\0' # Former duplicate black, now the dragon's gray 4.
 assert sha(normalized_palette)=='a0cb487bb5002eeffdee4fc229798fbbcfa746e591a5657756710b2507fb2cbc'
 sys.path.insert(0,str(ROOT/'tools'))
 from arcade_source import Source
 from extract import decode as source_decode,pack
 from hud_assets import rgb
 import struct
 source=Source();board=json.loads((ROOT/'assets/board.json').read_text())
 sprites=source_decode(b''.join(source.files[f['path']] for f in board['regions']['sprites']['files']),board['layouts']['sprites'])
 mem=bytearray(2048);ptr=source.word(6,0x8136)
 for _ in range(20):
  start,dest,count=struct.unpack('<HHH',source.read(6,ptr,6))
  if start==65535:break
  mem[dest-0xd800:dest-0xd800+count]=source.read(6,start,count);ptr+=6
 colors=[((mem[i]>>5)<<1)|(((mem[i]&15)>>1)<<5)|(((mem[1024+i]&15)>>1)<<9)for i in range(1024)]
 enemy=np.array([rgb(int(v)) for v in palette[17:]])
 restored=bytearray((ROOT/'res/generated/object_patterns.bin').read_bytes())
 # Every palette-0 pixel retains its old RGB after the duplicate-black remap.
 for code in range(2048):
  pens=sprites[code];old=np.where(pens==15,0,pens+1);new=np.where(pens==14,1,old)
  expected=b''.join(pack(new[y:y+8,x:x+8]) for x,y in ((0,0),(0,8),(8,0),(8,8)))
  assert restored[code*128:(code+1)*128]==expected
  assert np.array_equal(palette[new],np.frombuffer(normalized_palette,'>u2')[old])
  restored[code*128:(code+1)*128]=b''.join(pack(old[y:y+8,x:x+8]) for x,y in ((0,0),(0,8),(8,0),(8,8)))
 for bank,lo,hi in ((1,1536,2048),(2,1536,2048),(3,1536,2048),(7,0,256),(7,1536,2048)):
  pens=[int(((enemy-rgb(c))**2).sum(1).argmin())+1 for c in colors[512+bank*16:527+bank*16]]+[0]
  for code in range(lo,hi):
   tile=np.array(pens,dtype=np.uint8)[sprites[code]]
   raw=b''.join(pack(tile[y:y+8,x:x+8]) for x,y in ((0,0),(0,8),(8,0),(8,8)))
   restored[(bank*2048+code)*128:(bank*2048+code+1)*128]=raw
 assert sha(restored)=='57ba9b32a865803a02dcddd831ca95cd94f81879866ed49f7db97dfb0276d645'
 checks.append('all original hero pixel colors preserved; enemy palette and atlas unchanged outside dragon/poison variants')
 out={'passed':len(checks),'checks':checks};(ROOT/'reports/asset-tests.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
