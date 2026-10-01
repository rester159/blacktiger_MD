"""Battery SRAM round trips through the real cartridge and libretro save memory."""
import ctypes as C, hashlib, json, struct
from test_runtime import ROOT, Runner, state, put
rom=ROOT/'out/release/rom.bin'
header=rom.read_bytes()[0x1b0:0x1bc]
assert header==b'RA\xf8\x20'+struct.pack('>II',0x200001,0x2007ff),header.hex()
def memory(r):
 r.lib.retro_get_memory_data.argtypes=[C.c_uint];r.lib.retro_get_memory_data.restype=C.c_void_p
 r.lib.retro_get_memory_size.argtypes=[C.c_uint];r.lib.retro_get_memory_size.restype=C.c_size_t
 n=65536 # Genesis Plus GX trims its reported save length to the last non-FF byte.
 return (C.c_ubyte*n).from_address(r.lib.retro_get_memory_data(0))
def boot(saved=None):
 r=Runner(rom,skip_boot=False);m=memory(r)
 m[:]=bytes([255])*len(m)
 if saved is not None:m[:len(saved)]=saved
 r.run(180);return r
def score(r):return int.from_bytes(r.read('high_score',4),'big')
def award(r,n):
 r.write('high_score',0,n.to_bytes(4,'big'));r.run(10)
 assert score(r)==n
r=boot();assert score(r)==20000
award(r,54321);first=bytes(memory(r));assert b'BTS1' in first[1::2]
award(r,98765);second=bytes(memory(r));assert first!=second
r.run(100);assert bytes(memory(r))==second,'Unchanged score rewrote SRAM'
r.close()
r=boot(second);assert score(r)==98765
# Normal game rendering and streaming work after SRAM restores the ROM mapping.
r.start_game();r.run(180)
assert state(r).mode==1
assert int.from_bytes(r.read('video_cache_faults'),'big')==0
s=state(r);s.score=123456;put(r,s);r.run(10)
assert score(r)==123456
earned=bytes(memory(r))
r.close()
r=boot(earned);assert score(r)==123456;r.close()
# Corrupt every individual byte of the latest committed record. The previous
# record must survive both a bad checksum and an interrupted magic commit.
# The core save buffer retains the odd-address bus spacing.
latest=second[1::2].find(b'BTS1'+struct.pack('>I',98765));assert latest>=0
for byte in range(12):
 broken=bytearray(second);broken[(latest+byte)*2+1]^=0xff
 r=boot(broken);assert score(r)==54321,(byte,score(r));r.close()
# Interrupt the second write after each individual bus-byte store, including
# before the final magic byte commits it. The first slot remains recoverable.
record=second[1::2][latest:latest+12]
stores=[(0,0)]+list(enumerate(record[4:12],4))+list(enumerate(record[1:4],1))+[(0,record[0])]
partial=bytearray(first)
for step,(offset,value) in enumerate(stores):
 partial[(latest+offset)*2+1]=value
 r=boot(partial);assert score(r)==(98765 if step==len(stores)-1 else 54321),(step,score(r));r.close()
r=boot(first);assert score(r)==54321
award(r,20000);assert bytes(memory(r))==first,'Lower score replaced record'
r.close()
report=dict(passed=True,power_cycle=True,corrupt_record_cases=12,interrupted_write_cases=len(stores),previous_record_fallback=True,unchanged_score_no_writes=True,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest())
(ROOT/'reports/high-score-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
