"""Inspect linked-ROM window tilemap for energy, armor and inventory changes."""
import json,hashlib,ctypes as C
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
vram=(C.c_uint8*65536).in_dll(r.lib,'vram')
def tile(x,y):
 a=0xd000+(y*32+x)*2;return ((vram[a^1]<<8)|vram[(a+1)^1])&2047
def number(x,y,n):return ''.join(chr(tile(x+i,y)-1440+32) for i in range(n))
for hp in range(6):
 s=state(r);s.mode=2;s.p.hp=hp;s.p.armor=8-hp;s.p.weapon=5;s.p.lives=3;s.coins=12345;s.score=87654321;s.time=199;put(r,s)
 r.write('progress_max_hp',0,b'\x05');r.write('container_keys',0,bytes([hp]));r.write('shop_antidotes',0,b'\x02');r.run(12)
 assert [tile(8+i,1) for i in range(5)]==[7 if i<hp else 8 for i in range(5)]
 assert [tile(22+i,1) for i in range(8)]==[7 if i<8-hp else 8 for i in range(8)]
 assert number(7,0,8)=='87654321' and number(21,0,3)=='199'
 assert number(5,2,2)==f'{hp:02}' and number(12,2,1)=='5' and number(20,2,1)=='3' and number(27,2,2)=='02'
 assert number(7,3,5)=='12345' and number(16,3,2)=='02'
r.capture('hud-inventory.png');r.close()
report=dict(passed=True,cases=6,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Actual window VRAM: energy/armor bars across empty/full values, keys, weapon, lives, antidotes, score, time, currency and credits.')
(ROOT/'reports/hud-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
