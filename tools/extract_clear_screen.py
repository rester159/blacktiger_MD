"""Compile witnessed bonus-screen tilemaps into Genesis native graphics."""
import hashlib,json,struct
import numpy as np
from PIL import Image
from arcade_source import ROOT

def generate(source,emit,decode,pack,words):
 ref=json.loads((ROOT/'reference/clear_screen_oracle.json').read_text())
 assert ref['source_set']==source.lock['aggregate_sha256']
 for key,path in [('trace_sha256','reference/clear_screen_oracle_events.txt'),('lua_sha256','tools/clear_screen_oracle.lua')]:
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
 board=json.loads((ROOT/'assets/board.json').read_text())
 def graphics(region,layout):return decode(b''.join(source.files[f['path']] for f in board['regions'][region]['files']),board['layouts'][layout])
 tiles=graphics('tiles','tiles');chars=graphics('chars','characters')
 unique={bytes(32):0};patterns=bytearray(32);screens=[];palette=None
 def tile(pixels,pal):
  raw=pack(pixels)
  if raw not in unique:unique[raw]=len(unique);patterns.extend(raw)
  return 16+unique[raw]+(pal<<13)
 for line in (ROOT/'reference/clear_screen_oracle_events.txt').read_text().splitlines():
  f=line.split('|')
  if f[0]!='SCREEN':continue
  r=int(f[1]);bg,fg,p=map(bytes.fromhex,f[2:]);assert len(bg)==512 and len(fg)==len(p)==2048
  source.expect(None,0x5c9e,'213c92');source.expect(None,0x5ca6,'1100c0010002edb0')
  assert bg==source.read(4,source.word(4,0x923c+2*r),512)
  colors=[((p[i]>>5)<<1)|(((p[i]&15)>>1)<<5)|(((p[1024+i]&15)>>1)<<9) for i in range(1024)]
  # Two original BG palettes fit exactly after RGB444 -> RGB333 truncation.
  # Move transparent pen 15 to Genesis zero; retain every opaque pen.
  cp=[0]+colors[96:111]+[0]+colors[112:127]+[0]+colors[768:771]+colors[800:803]+[0]*9
  assert len(cp)==48
  if palette is None:palette=cp
  assert cp==palette
  bmap=[];fmap=[];rgb=np.zeros((224,256,3),dtype=np.uint8)
  for y in range(28):
   sy=y+2
   for x in range(32):
    at=((sy//2)*16+x//2)*2;code,attr=bg[at:at+2];pal=(attr>>3)&15;assert pal in (6,7)
    pix=tiles[code|((attr&7)<<8)]
    if attr&128:pix=pix[:,::-1]
    pix=pix[(sy%2)*8:(sy%2+1)*8,(x%2)*8:(x%2+1)*8]
    bp=(pix+1)&15;bmap.append(tile(bp,pal-6))
    pos=sy*32+x;attr=fg[1024+pos];char=chars[fg[pos]|((attr&224)<<3)];cpal=attr&31;assert cpal in (0,8)
    fp=np.where(char==3,0,char+1+(3 if cpal==8 else 0)).astype(np.uint8)
    fmap.append(tile(fp,2))
    indexed=np.where(fp,32+fp,(pal-6)*16+bp)
    for iy in range(8):
     for ix in range(8):
      w=palette[indexed[iy,ix]];rgb[y*8+iy,x*8+ix]=[((w>>1)&7)*255//7,((w>>5)&7)*255//7,((w>>9)&7)*255//7]
  emit(f'clear_screen_bg{r}',words(bmap));emit(f'clear_screen_fg{r}',words(fmap))
  Image.fromarray(rgb).save(ROOT/f'reports/clear-screen-source{r+1}.png')
  screens.append({'round':r+1,'background_sha256':hashlib.sha256(words(bmap)).hexdigest(),'foreground_sha256':hashlib.sha256(words(fmap)).hexdigest(),'rgb_sha256':hashlib.sha256(rgb.tobytes()).hexdigest()})
 digit_words=[tile(np.where(chars[d]==3,0,chars[d]+1).astype(np.uint8),2) for d in range(10)]
 assert len(screens)==7 and len(unique)<=1056
 emit('clear_screen_patterns',bytes(patterns),'u32');emit('clear_screen_palette',words(palette))
 (ROOT/'src/clear_screen_data.inc').write_text('/* Source bonus screens; shared deduplicated native tiles. */\n#define CLEAR_SCREEN_TILES '+str(len(unique))+'\nstatic const u16 clear_digits[10]={'+','.join(map(str,digit_words))+'};\nstatic const u16 *const clear_bg[7]={'+','.join('clear_screen_bg'+str(r) for r in range(7))+'};\nstatic const u16 *const clear_fg[7]={'+','.join('clear_screen_fg'+str(r) for r in range(7))+'};\n')
 report=dict(source_set=ref['source_set'],tiles=len(unique),screens=screens,scope='Seven source bonus maps and text, cropped to arcade visible Y16..239. Exact RGB333 pens using two background palettes and one character palette; HUD remains the native console HUD. Fade timing excluded.')
 (ROOT/'reference/clear_screen.json').write_text(json.dumps(report,indent=2)+'\n')
 return report
