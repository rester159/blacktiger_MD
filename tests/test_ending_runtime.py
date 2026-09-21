"""Real final-clear entry, source ending lettering/VRAM, and terminal lifecycle."""
import ctypes as C,hashlib,json,struct
from test_runtime import ROOT,Runner,state,put,check_video_cache
rom=ROOT/'out/release/rom.bin';r=Runner(rom);r.run(100);r.start_game(3);r.run(40)
s=state(r);s.mode=2;put(r,s);r.run(60)
s=state(r);s.mode=5;s.round=7;s.mode_timer=0;s.cam_x=1664;s.cam_y=48;s.p.x=1776*256;s.p.y=192*256;s.p.armor=2;s.p.weapon=1;s.coins=12345
for a in s.actors:a.active=0
for q in s.shots:q.active=0
r.write('player_motion',15,b'\0');r.write('player_motion',21,bytes(2));r.write('round_clear',0,bytes(8));put(r,s)
for _ in range(400):
 r.run(1)
 if state(r).mode==6:break
assert state(r).mode==6 and r.read('ending',8)[4]==1
assert r.read('music_command',1)[0]==0x33
# Stable intervals after long source waits let queued VRAM transfers settle.
checkpoints=[];source=[]
for line in (ROOT/'reference/ending_oracle_events.txt').read_text().splitlines():
 f=line.split('|');source.append(f)
 if f[0]=='WAIT' and int(f[2])>=60:checkpoints.append(int(f[1])+20)
v=(C.c_uint8*65536).in_dll(r.lib,'vram');cram=(C.c_uint16*64).in_dll(r.lib,'cram')
def read(at,n):return bytes(v[(at+i)^1] for i in range(n))
def palette(raw):return [((w&0xe00)>>3)|((w&0xe0)>>2)|((w&14)>>1) for w in struct.unpack('>'+str(len(raw)//2)+'H',raw)]
glyphs=struct.unpack('>256H',(ROOT/'res/generated/ending_glyphs.bin').read_bytes());font=(ROOT/'res/generated/ending_font.bin').read_bytes();cases=[];next_check=0;captures=[]
for frame in range(6000):
 r.run(1,8 if frame%60<2 else 0);s=state(r)
 if s.mode!=6:break
 tick,index,active,pal,scene,complete=struct.unpack('>HH4B',r.read('ending',8))
 if next_check>=len(checkpoints) or tick<checkpoints[next_check]:continue
 next_check+=1
 assert read(1408*32,min(1024,len(font)))==font[:1024]
 if len(font)>1024:assert read(1072*32,len(font)-1024)==font[1024:]
 assert list(cram)[48:52]==palette((ROOT/'res/generated/ending_text_palette.bin').read_bytes())
 expected=bytearray([32]*896)
 for f in source:
  if f[0] in ('COMPLETE',):continue
  if int(f[1])>=tick:break
  if f[0]=='TEXT':expected[int(f[2])-64]=int(f[3])
  elif f[0]=='CLEAR':expected[64:]=bytes([32]*832)
 assert r.read('ending_text',896)==expected,(tick,'source text')
 for y in range(2,28):
  assert read(0xc000+y*128,64)==struct.pack('>32H',*[glyphs[c] for c in expected[y*32:(y+1)*32]]),(tick,y,'text VRAM')
 if scene==0:
  fades=(ROOT/'res/generated/ending_fades.bin').read_bytes();assert list(cram)[:32]==palette(fades[pal*64:(pal+1)*64])
 elif scene==1:
  mapping=(ROOT/'res/generated/ending_map.bin').read_bytes();patterns=(ROOT/'res/generated/ending_patterns.bin').read_bytes()
  for y in range(28):assert read(0xe000+y*128,64)==mapping[y*64:(y+1)*64]
  assert read(512,len(patterns))==patterns
  assert list(cram)[:32]==palette((ROOT/'res/generated/ending_palette.bin').read_bytes())
  assert read(0xf400,2)==b'\0\x60'
 if (scene==0 and tick>800) or scene==1:
  name=f'ending-native-{tick}.png';r.capture(name);captures.append(name)
 cases.append(dict(tick=tick,palette=pal,scene=scene,text_vram=True,graphics=True))
assert s.mode==7 and next_check==len(checkpoints),(s.mode,next_check,len(checkpoints))
assert r.read('ending',8)[7] and s.p.lives==0 and s.coins==12345
r.run(8);assert r.read('music_command',1)[0]==0x31
# Completed games bypass the ordinary continue offer, even with repeated Start.
for frame in range(500):
 r.run(1,8 if frame%6<3 else 0);s=state(r)
 assert r.read('game_over',4)[2]!=2,'Completed game offered a continue'
 if s.mode==0:break
else:raise AssertionError('Completed game did not return to title')
r.run(80,0);r.run(3,8);r.run(3);r.run(3,8);r.run(30);s=state(r);assert s.mode==1 and s.round==0 and r.read('ending',8)[7]==0
s.mode=2;put(r,s);r.run(60);check_video_cache(r,state(r));assert int.from_bytes(r.read('video_cache_faults'),'big')==0
r.close();report=dict(passed=True,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=cases,captures=captures,final_clear_entry=True,original_music_continuity=True,start_does_not_skip=True,no_post_completion_continue=True,new_game_resets=True,scope='Injected final victory leading through all native ending pages, source-matched text/actual VRAM, adapted palette stages, credits map/patterns, final game-over without continue, and new-game terrain restoration. Not a natural eight-round playthrough or board sprite-retention proof.')
(ROOT/'reports/ending-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','rom_sha256','no_post_completion_continue','new_game_resets')}))
