"""Seven witnessed bonus screens in real cartridge VRAM, plus terrain restoration."""
import ctypes as C,hashlib,json,re,struct
from test_runtime import ROOT,Runner,state,put,check_video_cache
rom=ROOT/'out/release/rom.bin';cases=[]
patterns=(ROOT/'res/generated/clear_screen_patterns.bin').read_bytes()
digits=list(map(int,re.search(r'clear_digits\[10\]=\{([^}]+)',(ROOT/'src/clear_screen_data.inc').read_text())[1].split(',')))
r=Runner(rom);r.run(100);r.run(3,8);r.run(40)
for level in range(7):
 s=state(r);s.mode=2;put(r,s);r.run(60)
 s=state(r);s.round=level;s.mode=5;s.mode_timer=240;s.coins=12345+level
 # Deliberately leave actors/projectiles present: none may leak onto the bonus screen.
 r.write('round_clear',0,bytes([2,1,0,0,0,0,0,0]));put(r,s);r.run(30)
 assert state(r).mode==5 and r.read('clear_screen_active',1)[0]==level+1
 v=(C.c_uint8*65536).in_dll(r.lib,'vram')
 def read(at,n):return bytes(v[(at+i)^1] for i in range(n))
 assert read(16*32,len(patterns))==patterns,(level,'patterns')
 cram=(C.c_uint16*64).in_dll(r.lib,'cram')
 palette=struct.unpack('>48H',(ROOT/'res/generated/clear_screen_palette.bin').read_bytes())
 assert list(cram)[:48]==[((w&0xe00)>>3)|((w&0xe0)>>2)|((w&14)>>1) for w in palette],(level,'palette')
 for layer,base in [('bg',0xe000),('fg',0xc000)]:
  expected=bytearray((ROOT/f'res/generated/clear_screen_{layer}{level}.bin').read_bytes())
  if layer=='fg':
   for i,d in enumerate(str(s.coins).zfill(5)):
    struct.pack_into('>H',expected,(4*32+26+i)*2,digits[int(d)])
  for y in range(28):assert read(base+y*128,64)==expected[y*64:(y+1)*64],(level,layer,y)
 assert read(0xf400,2)==bytes([0,96]),(level,'hidden sprites')
 assert read(0xf404,4)==bytes([0,0,0,128]),(level,'hidden sprite attributes')
 r.capture(f'clear-screen-native{level+1}.png')
 # Advance the real hold into the following round and verify terrain cache rebuild.
 for _ in range(300):
  r.run(1)
  if state(r).mode!=5:break
 s=state(r);assert s.mode==1 and s.round==level+1
 s.mode=2;put(r,s);r.run(80);assert r.read('clear_screen_active',1)==b'\0'
 check_video_cache(r,state(r));assert int.from_bytes(r.read('video_cache_faults'),'big')==0
 restored=list(struct.unpack('>64H',(ROOT/f'res/generated/pal{level+1}.bin').read_bytes()+(ROOT/'res/generated/object_palette.bin').read_bytes()));restored[63]=0xeee
 assert list(cram)==[((w&0xe00)>>3)|((w&0xe0)>>2)|((w&14)>>1) for w in restored],(level,'restored palette')
 cases.append(dict(round=level+1,tilemaps=True,patterns=True,palette=True,dynamic_balance=s.coins,all_sprites_hidden=True,next_round_cache=True,next_round_palette=True))
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=cases,scope='Injected bonus holds for seven rounds: complete actual VRAM map/pattern match, native current-balance glyphs, hidden gameplay sprites, and real hold transition rebuilding the next terrain cache. Source setup captured separately; no fade or natural playthrough claim.')
(ROOT/'reports/clear-screen-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
