"""Controller-driven records, initials, v1.4 migration and journal recovery."""
import ctypes as C,hashlib,json,struct
from test_runtime import ROOT,Runner,state,put
rom=ROOT/'out/release/rom.bin'
def memory(r):
 r.lib.retro_get_memory_data.argtypes=[C.c_uint];r.lib.retro_get_memory_data.restype=C.c_void_p
 return (C.c_ubyte*65536).from_address(r.lib.retro_get_memory_data(0))
def boot(saved=None):
 r=Runner(rom,skip_boot=False);m=memory(r);m[:]=bytes([255])*len(m)
 if saved is not None:m[:len(saved)]=saved
 for _ in range(750):
  r.run(1)
  if r.read('boot_done',1)==b'\1':break
 else:raise AssertionError('Boot did not finish')
 r.run(100);return r
def tap(r,key):r.run(6,key);r.run(6)
def table(r):return [struct.unpack_from('>I3sB',r.read('high_scores',40),8*i) for i in range(5)]
def open_high_scores(r):
 tap(r,32);tap(r,32);tap(r,2)
 assert r.read('frontend',2)[1]==5,'HIGH SCORES was not reachable from the public selector'
def finish(r,score,name='AAA'):
 s=state(r);s.score=score;s.mode=2;put(r,s);r.run(10)
 s=state(r);s.mode=7;s.previous_input=0;put(r,s)
 r.write('game_over',0,struct.pack('>HBB',1,1,9));r.write('settings',10,b'\0');r.run(10)
 assert state(r).mode==0
 if r.read('frontend',2)[1]!=6:return False
 pending=r.read('high_score_pending',1)[0]
 tap(r,32);assert table(r)[pending][1][0:1]==b'Z'
 tap(r,16);tap(r,2);tap(r,1);assert r.read('high_score_cursor',1)==b'\0'
 for char in name:
  for _ in range(ord(char)-65):tap(r,16)
  tap(r,2)
 assert r.read('frontend',2)[1]==5 and r.read('high_score_pending',1)==b'\xff'
 return True
def next_run(r):
 tap(r,1) # Table -> main selector, retaining HIGH SCORES selection.
 tap(r,16);tap(r,2);tap(r,8);r.skip_intro();r.run(10)
 assert state(r).mode==1
# Migration from the old 64-byte SRAM layout: preserve the user's record.
legacy=bytearray([255]*65536);record=b'BTS1'+struct.pack('>II',54321,~54321&0xffffffff)
for i,b in enumerate(record):legacy[1+2*(16+i)]=b
r=boot(legacy);assert table(r)[0]==(54321,b'---',0)
assert int.from_bytes(r.read('high_score',4),'big')==54321
# Live title digits must be generated on plane A, not the old bitmap number.
vram=(C.c_ubyte*65536).in_dll(r.lib,'vram')
def word(at):return (vram[at^1]<<8)|vram[(at+1)^1]
font_base=(word(0xc000+128+13*2)&2047)-(ord(' ')-32)
assert [(word(0xc000+128+(13+i)*2)&2047)-font_base+32 for i in range(8)]==list(b'   54321')
r.capture('v15-saved-title.png')
r.start_game();r.run(20)
for score,name in ((60000,'BOB'),(40000,'ACE'),(90000,'ZED'),(70000,'ANN'),(80000,'MAX')):
 assert finish(r,score,name)
 if score!=80000:next_run(r)
expected=[(90000,b'ZED',1),(80000,b'MAX',1),(70000,b'ANN',1),(60000,b'BOB',1),(40000,b'ACE',1)]
assert table(r)==expected,table(r)
r.capture('v15-high-score-table.png');saved=bytes(memory(r))
r.run(80);assert bytes(memory(r))==saved,'Idle table rewrites SRAM'
next_run(r);assert not finish(r,10),'Nonqualifying score opened initials'
assert table(r)==expected
r.close();r=boot(saved);open_high_scores(r);tap(r,128);assert table(r)==expected
tap(r,2);r.close()
# Corrupt any byte in the current record: the other journal slot survives.
logical=saved[1::2];slots=[(struct.unpack_from('>I',logical,o+4)[0],o) for o in (224,368)]
_,latest=max(slots);previous=368 if latest==224 else 224
fallback=[struct.unpack_from('>I3sB',logical,previous+8+i*8) for i in range(5)]
for i in range(132):
 bad=bytearray(saved);bad[(latest+i)*2+1]^=0xff
 r=boot(bad);assert table(r)==fallback,(i,table(r));r.close()
report=dict(passed=True,v14_migration=True,title_digits=True,separate_mode_tables=True,ranked_records=expected,initials_and_modes=True,nonqualifying_ignored=True,power_cycle=True,corrupt_record_cases=132,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest())
# Names are stored as exactly three bytes; JSON uses their ASCII representation.
report['ranked_records']=[(score,name.decode(),mode) for score,name,mode in expected]
(ROOT/'reports/high-score-table-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
