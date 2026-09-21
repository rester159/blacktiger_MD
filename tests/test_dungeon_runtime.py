"""Linked-ROM Dungeon lifecycle/clock and arcade HUD checks; not full Dungeon acceptance."""
import ctypes as C,json,hashlib
from test_runtime import ROOT,Runner,state,put,BE,U8,U16,U32
class Dungeon(BE):
 _fields_=[('seed',U32),('streams',U32*8),*[(k,U32) for k in ('clock','run_xp','banked_xp','score','zenny')],*[(k,U16) for k in ('timer','freeze','kills','last_kills','deaths','revision','seen_revision')],*[(k,U8) for k in ('active','phase','stage','max_hp','charges','cleared','banked','scene_reload','boon','rank')]]
def dstate(r):return Dungeon.from_buffer_copy(r.read('dungeon',C.sizeof(Dungeon)))
def dput(r,d):r.write('dungeon',0,bytes(d))
def tap(r,key):r.run(4,key);r.run(4)
r=Runner(ROOT/'out/release/rom.bin');r.run(100);tap(r,32);tap(r,8);tap(r,32);tap(r,32);tap(r,8)
d=dstate(r);assert d.active and d.phase==0,(d.active,d.phase);r.capture('dungeon-setup.png');seed=d.seed
assert list(d.streams)==list(dict.fromkeys(d.streams)) # distinct stream state seeds
credits=r.read('frontend',9)[4];tap(r,8);assert dstate(r).phase==1;r.run(20);r.capture('dungeon-stage-intro.png');r.run(145)
d=dstate(r);assert d.phase==2 and d.stage==1 and 170*15360<d.clock<=180*15360
assert r.read('frontend',9)[4]==credits,'Dungeon must not spend Home credits'
s=state(r);s.mode=2;put(r,s);r.run(8);paused=dstate(r).clock;r.run(90);assert dstate(r).clock==paused
s=state(r);s.mode=1;s.p.invincible=10000;s.kills+=2;put(r,s);before=dstate(r);r.run(5);d=dstate(r)
assert d.run_xp==2 and d.kills==2 and d.clock>before.clock,'kill XP and clock reward'
# Real C input freezes enemies and the clock; current controller can still move.
tap(r,256);d=dstate(r);assert d.freeze>0 and d.charges==0
before=d.clock;x=state(r).p.x;r.run(20,128);assert dstate(r).clock==before and state(r).p.x>x
vram=(C.c_uint8*65536).in_dll(r.lib,'vram');cram=(C.c_uint16*64).in_dll(r.lib,'cram')
def word(a):return vram[a^1]*256+vram[(a+1)^1]
# Dungeon uses the same original top/bottom icon HUD, without a Window panel.
assert word(0xc000+25*128+23*2)&2047==1440+ord('X')-32
assert word(0xc000+25*128+24*2)&2047==1440+ord('P')-32
# Sprite and background colors must equal the normal round palettes exactly.
import numpy as np
palette=np.frombuffer((ROOT/f'res/generated/pal{s.round}.bin').read_bytes(),'>u2').tolist()+np.frombuffer((ROOT/'res/generated/object_palette.bin').read_bytes(),'>u2').tolist()
palette[63]=0xeee
expected=[((w>>1)&7)|(((w>>5)&7)<<3)|(((w>>9)&7)<<6) for w in palette]
assert list(cram)==expected,'Dungeon must preserve normal gameplay CRAM'
# Verify XP digits against character-ROM transparency, independent of HUD tile IDs.
from arcade_source import Source
from extract import decode
source=Source();board=json.loads((ROOT/'assets/board.json').read_text())
chars=decode(b''.join(source.files[f['path']] for f in board['regions']['chars']['files']),board['layouts']['characters'])
def digit_shape(x,y,digit):
 tile=word(0xc000+y*128+x*2)&2047
 raw=bytes(vram[(tile*32+i)^1] for i in range(32))
 actual=np.array([p for b in raw for p in (b>>4,b&15)]).reshape(8,8)
 assert np.array_equal(actual==0,chars[digit]==3),(x,y,digit)
for i,ch in enumerate('00000002'):digit_shape(23+i,26,int(ch))
r.capture('dungeon-hud-xp.png')
s=state(r);s.mode=4;s.mode_timer=1;s.p.lives=99;put(r,s);d=dstate(r);d.freeze=0;dput(r,d);before=d.clock;r.run(1)
d=dstate(r);assert d.deaths==1 and d.clock==before-60*15360,(d.clock,before)
r.run(12);assert state(r).mode==1 and state(r).p.hp==8
# All sixteen generated stages are reachable through the same gate transition.
for stage in range(1,17):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.mode=5;put(r,s);r.run(8);d=dstate(r)
 if stage==16:
  assert d.phase==5 and d.cleared and d.banked and d.banked_xp==d.run_xp
 else:
  assert d.phase==4 and d.stage==stage,(stage,d.phase,d.stage)
  frozen=d.clock;r.run(20);assert dstate(r).clock==frozen
  tap(r,8);r.run(155);d=dstate(r);assert d.phase==2 and d.stage==stage+1
r.capture('dungeon-results.png');banked=dstate(r).banked_xp;r.run(30);assert dstate(r).banked_xp==banked
# Fresh random run seed and immediate expiry without spending Home continues.
tap(r,8);assert dstate(r).seed!=seed;tap(r,8);r.run(160)
d=dstate(r);d.clock=1;dput(r,d);r.run(4);d=dstate(r);assert d.phase==5 and d.clock==0 and not d.cleared
r.close();report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),stages=16,scope=__doc__,checks=['menu entry without credits','independent seeded streams','clock persists','pause/gate stop clock','kills award XP and time','C Hourglass freezes clock while movement continues','death costs 60s and respawns','16 generated stages','results bank XP once','fresh seed per run','zero clock ends immediately'])
(ROOT/'reports/dungeon-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
