"""Original display timeline, saved rankings, coin interruption and clean exits."""
import ctypes as C,gzip,hashlib,json,struct
from test_runtime import ROOT,Runner,state,put
rom=ROOT/'out/release/rom.bin';raw=gzip.decompress((ROOT/'reference/attract_oracle_frames.bin.gz').read_bytes())
checks=[]
def check(name,ok):assert ok,name;checks.append(name)
def memory(r):
 r.lib.retro_get_memory_data.argtypes=[C.c_uint];r.lib.retro_get_memory_data.restype=C.c_void_p
 return (C.c_ubyte*65536).from_address(r.lib.retro_get_memory_data(0))
def tap(r,key):r.run(6,key);r.run(6)
def boot(saved=None):
 r=Runner(rom,skip_boot=False);m=memory(r);m[:]=bytes([255])*65536
 if saved is not None:m[:]=saved
 for _ in range(750):
  r.run(1)
  if r.read('boot_done',1)==b'\1':break
 else:raise AssertionError('Opening did not complete')
 r.run(80);return r
def glyph(r,bank,c):
 at=r.symbols['attract_chars'+str(bank)]+(ord(c)-32)*2
 return int.from_bytes(rom.read_bytes()[at:at+2],'big')
def row(r,y):
 v=(C.c_ubyte*65536).in_dll(r.lib,'vram')
 return [(v[(0xc000+y*128+x*2)^1]<<8)|v[(0xc001+y*128+x*2)^1] for x in range(32)]
record=bytearray(b'BTL2'+struct.pack('>I',1))
entries=[(90000,b'ACE',0),(80000,b'BOB',1),(70000,b'CAT',2),(60000,b'DAN',0),(50000,b'EVE',1)]
for score,name,mode in entries:record+=struct.pack('>I3sB',score,name,mode)
h=2166136261
for b in record[4:48]:h=((h^b)*16777619)&0xffffffff
record+=struct.pack('>I',h)
saved=bytearray([255])*65536
for i,b in enumerate(record):saved[(32+i)*2+1]=b
r=boot(saved);tap(r,2)
check('Arcade enters attract without spending a credit',r.read('attract_running',1)==b'\1' and r.read('frontend',9)[4]==0)
sram=bytes(memory(r));records=r.read('high_scores',40);initial_game_score=state(r).score
r.run(50)
check('Saved high score appears in arcade header',row(r,1)[12:20]==[glyph(r,7,c) for c in '   90000'])
for i,(score,name,_) in enumerate(entries):
 y=16+i*2
 check('Saved ranking '+str(i+1),row(r,y)[13:20]==[glyph(r,7,c) for c in str(score).rjust(7)] and row(r,y)[21:24]==[glyph(r,0,chr(c)) for c in name])
r.capture('v15-attract-rankings.png')
seen=set();blink=set();wrap=False;last=-1;samples=0
# Read the actual native replay state out of the shared title-only workspace.
for _ in range(4300):
 r.run(1);frame=int.from_bytes(r.read('attract_frame'),'big')
 if last>frame:wrap=True;break
 last=frame
 if 650<=frame<=800:blink.add(bool(r.frame[152:160,80:184].any()))
 if frame%17 or r.read('attract_decoding',1)!=b'\0':continue
 source=raw[(frame+150)*5126:(frame+151)*5126]
 display=r.read('sprite_slot_for_key',4096+3334)[4096:]
 sx,sy=struct.unpack('<HH',source[:4])
 assert struct.unpack('>HH',display[:4])==(sx&511,(sy+16)&255),(frame,'scroll')
 assert display[2822:]==(source[4614:5126] if not source[5]&4 else bytes(512)),(frame,'sprites')
 samples+=1;seen.add(bool(display[5] and frame>1367))
 if 1800<=frame<1820:r.capture('v15-attract-demo.png')
 if 3600<=frame<3620:r.capture('v15-attract-demo-late.png')
check('Complete source timeline and loop',wrap and samples>200 and seen=={False,True})
check('Original INSERT COIN prompt flashes',blink=={False,True})
check('Attract clock does not discard source ticks',int.from_bytes(r.read('pacing_discarded_ticks',4),'big')==0)
check('Demo never changes records, score, credits or SRAM',bytes(memory(r))==sram and r.read('high_scores',40)==records and state(r).score==initial_game_score and r.read('frontend',9)[4]==0)
# Interrupt during gameplay rather than only at the initial ranking screen.
r.run(1700);r.run(24,8)
check('Coin interrupts demonstration and keeps one credit',r.read('attract_credit',1)==b'\1' and r.read('frontend',9)[4]==1)
check('Original coin sound plays',r.read('music_command',1)==b'\x20')
r.capture('v15-attract-credit.png');r.run(100,8)
check('Held Start does not add repeat coins',r.read('frontend',9)[4]==1)
r.run(8);tap(r,2)
check('A spends one credit and starts original introduction',state(r).mode==9 and r.read('frontend',9)[4]==0 and r.read('attract_running',1)==b'\0')
r.run(40);tap(r,2);r.run(20)
check('Gameplay renderer restored after replay workspace reuse',state(r).mode==1 and int.from_bytes(r.read('video_cache_faults'),'big')==0)
# A real completed Arcade run records initials, then automatically resumes attract.
game=state(r);game.score=95000;game.mode=2;put(r,game);r.run(10)
game=state(r);game.mode=7;game.previous_input=0;put(r,game)
r.write('game_over',0,struct.pack('>HBB',1,2,0));r.run(20)
check('Qualifying Arcade run opens initials entry',r.read('frontend',2)[1]==6)
for _ in range(3):tap(r,2)
r.run(20)
check('Confirmed Arcade initials return to attract',r.read('frontend',2)==b'\0\1' and r.read('attract_running',1)==b'\1' and r.read('high_scores',8)==struct.pack('>I3sB',95000,b'AAA',0))
new_save=bytes(memory(r));r.close();r=boot(new_save);tap(r,2);r.run(50)
check('New Arcade initials persist after restart',row(r,16)[21:24]==[glyph(r,0,c) for c in 'AAA'] and int.from_bytes(r.read('high_score',4),'big')==95000)
r.close();r=boot(sram);tap(r,2);r.run(50)
check('Power cycle preserves scores in attract rankings',r.read('high_scores',40)==records and row(r,16)[21:24]==[glyph(r,0,c) for c in 'ACE'])
tap(r,32);check('Down opens DIP switches',r.read('frontend',2)==b'\0\2' and r.read('attract_running',1)==b'\0')
tap(r,1);check('B returns from DIP to attract',r.read('attract_running',1)==b'\1')
tap(r,1);check('B exits attract to mode selector',r.read('frontend',2)[1]==0 and r.read('attract_running',1)==b'\0')
tap(r,32);tap(r,2);tap(r,8);r.skip_intro();r.run(20)
check('Home remains playable after attract and DIP exits',state(r).mode==1 and int.from_bytes(r.read('video_cache_faults'),'big')==0)
r.close()
report=dict(passed=True,checks=checks,source_frame_samples=samples,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),scope=__doc__+' RGB333/palette and sprite-limit adaptation; original observed demo replay, not a second gameplay engine.')
(ROOT/'reports/attract-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
