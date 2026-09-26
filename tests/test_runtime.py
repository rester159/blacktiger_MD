#!/usr/bin/env python3
"""Linked-ROM integration tests. Injected states test subsystems, not a playthrough."""
import ctypes as C,sys,struct,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_rom import Runner,ROOT
class BE(C.BigEndianStructure):_pack_=2
U8=C.c_uint8;U16=C.c_uint16;S8=C.c_int8;S16=C.c_int16;U32=C.c_uint32;S32=C.c_int32
class Player(BE):_fields_=[('x',S32),('y',S32),('vx',S16),('vy',S16),('invincible',U16),('attack',U16),*[(k,U8) for k in ('grounded','climb','face','hp','armor','weapon','lives','exploration')]]
class Actor(BE):_fields_=[('x',S32),('y',S32),('vx',S16),('vy',S16),('definition',U16),('timer',U16),('life',U16),*[(k,U8) for k in ('active','hp','hit','source')],('face',S8),('state',U8)]
class Shot(BE):_fields_=[('x',S32),('y',S32),('vx',S16),('vy',S16),*[(k,U8) for k in ('active','enemy','life','damage','kind')]]
class Game(BE):_fields_=[('p',Player),('actors',Actor*24),('shots',Shot*18),('spawned',U8*160),('score',U32),*[(k,U16) for k in ('coins','time','clock','frame','cam_x','cam_y','previous_input','mode_timer')],*[(k,U8) for k in ('round','mode','sound','shop_item','rescued','boss_dead')],('kills',U16),('rescue_actor',U8),('rescue_kind',U8),('player_low',U8),('sound_count',U8),('sound_commands',U8*16)]
def state(r):return Game.from_buffer_copy(r.read('game',C.sizeof(Game)))
def put(r,s):r.write('game',0,bytes(s))
def finish_clear(r,s):
 """Inject the end-of-clear hold when testing unrelated round-entry behavior."""
 r.write("round_clear",0,bytes([2,1,0,0,0,0,0,0]));put(r,s)
def save(r,name):r.capture(name+'.png')
def check_video_cache(r,s):
 level=s.round;width=128 if level==2 else 256;height=256 if level==2 else 128
 rush=bool(r.read('boss_rush',1)[0])
 world=(ROOT/('res/generated/palace_map.bin' if rush else f'res/generated/map{level}.bin')).read_bytes();patterns=(ROOT/('res/generated/palace_patterns.bin' if rush else f'res/generated/backdrop_bg{level}.bin' if level in (4,6) else f'res/generated/bg{level}.bin')).read_bytes()
 remap=None
 if level in (4,6):
  data=(ROOT/f'res/generated/backdrop_remap{level}.bin').read_bytes();n=len(data)//4;remap=struct.unpack('>'+str(n*2)+'H',data)
 v=(C.c_uint8*65536).in_dll(r.lib,'vram')
 def word(a):return (v[a^1]<<8)|v[(a+1)^1]
 camera_y=(s.cam_y+32768)%65536-32768
 for screen_y in range(camera_y//8,camera_y//8+29):
  y=screen_y%height if level==2 else screen_y
  for x in range(s.cam_x//8,s.cam_x//8+33):
   at=0xe000+((screen_y&31)*64+(x&63))*2;actual=word(at)
   if y>=height:assert actual==0;continue
   x%=width
   expected=int.from_bytes(world[(y*width+x)*2:(y*width+x)*2+2],'big')
   # Alternate-area artwork uses compiled source map writes.
   rom=(ROOT/'out/release/rom.bin').read_bytes() if not hasattr(r,'bonus_rom') else r.bonus_rom
   r.bonus_rom=rom
   if 'bonus_rounds' in r.symbols:
    ptr,count=struct.unpack_from('>IH',rom,r.symbols['bonus_rounds']+level*20)
    cell=(y//2)*(width//2)+x//2
    for pi in range(count):
     at=ptr+pi*40
     if int.from_bytes(rom[at:at+2],'big')==cell:
      expected=struct.unpack_from('>H',rom,at+2+(r.read('bonus_entered',1)[0]*2+r.read('bonus_phases',4)[rom[at+38]])*8+((y&1)*2+(x&1))*2)[0];break
   if remap is not None:expected=(expected&0xf800)|0x8000|remap[((expected>>13)&1)*n+(expected&2047)]
   assert actual&0xf800==expected&0xf800,(level,x,y,'attribute')
   original=(expected&2047)-16;physical=actual&2047
   if level==7 and not rush and r.read('bonus_phases',4)[original&3]:
    original=struct.unpack_from('>H',rom,r.symbols['torch_alternate']+original*2)[0]
   assert bytes(v[(physical*32+k)^1] for k in range(32))==patterns[original*32:original*32+32],(level,x,y,'tile')

def test():
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);s=state(r);assert s.mode==0,(C.sizeof(Game),s.mode,s.round);checks=[];cadence=[]
 def check(name,condition):
  assert condition,name;checks.append(name)
 check('title boots',s.frame>20 and s.p.hp==1 and s.coins==200 and s.p.armor==2);save(r,'tested-title')
 # Use the shared three-refresh input pulse through menu redraws.
 r.start_game();r.run(30);s=state(r);check('start enters play',s.mode==1 and s.p.grounded==1)
 s.p.invincible=0;put(r,s);save(r,'tested-start')
 before=s.p.x;r.run(24,1<<7);s=state(r);check('right movement',s.p.x>before);r.run(4);before=s.p.y;r.run(5,1<<0);s=state(r);check('jump rises',s.p.y<before and s.p.vy<0);save(r,'tested-jump')
 r.run(40);r.run(3,8);r.run(5);s=state(r);check('pause',s.mode==2);xy=(s.p.x,s.p.y);r.run(30,(1<<7)|(1<<1));s=state(r);check('pause freezes world',xy==(s.p.x,s.p.y));r.run(3,8);r.run(1);check('resume',state(r).mode==1)
 r.run(3,1<<1);s=state(r);check('attack creates projectiles',any(r.read('player_daggers',18*9)[i*18+14] for i in range(9)))
 # Climbing a continuous source-map ladder must move upward.
 initial=bytes(s)
 coll=(ROOT/'res/generated/collision0.bin').read_bytes();width=128
 at=next(i for i in range(width,len(coll)-width) if coll[i]==coll[i-width]==coll[i+width]==1)
 s.p.x=((at%width)*16-8)*256;s.p.y=((at//width)*16-16)*256;s.p.vx=s.p.vy=0;s.p.invincible=1000;s.previous_input=0;put(r,s)
 r.write('player_attack',0,bytes(12));r.write('player_daggers',0,bytes(18*9))
 y=s.p.y;r.run(8,1<<4);s=state(r);check('ladder climb',s.p.climb==1 and s.p.y<y)
 put(r,Game.from_buffer_copy(initial));r.run(2)
 # Independent injected combat fixture, actual projectile/actor update path.
 s=state(r);s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.invincible=1000;s.p.attack=0;s.p.face=0;s.previous_input=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 a=s.actors[0];a.active=1;a.definition=8;a.hp=1;a.life=1;a.state=0;a.hit=0;a.source=0;a.x=176*256;a.y=912*256;a.vx=a.vy=0;a.face=-1
 roots=json.loads((ROOT/'reference/crawler.json').read_text())['roots']
 crawler_state=bytes(8)+roots[10].to_bytes(2,'big')+bytes((0,0,8,0))
 r.write('crawlers',0,crawler_state)
 r.write('player_attack',0,bytes(12));r.write('player_daggers',0,bytes(18*9))
 kills=s.kills;put(r,s);r.run(90,(1<<1)|(1<<5));s=state(r);check('projectile defeats enemy',s.kills>kills)
 s.p.invincible=0;s.p.armor=2;a=s.actors[0];a.active=1;a.hp=12;a.state=0;a.life=2;a.hit=0;a.x=s.p.x;a.y=s.p.y;a.vy=0;r.write('crawlers',0,crawler_state);put(r,s);r.run(8);s=state(r);check('armor absorbs contact',s.p.armor==1 and s.p.hp==1)
  # Shop purchase uses the same public input path after state injection.
 s.mode=3;s.coins=300;s.shop_item=0;s.previous_input=0;s.p.weapon=1;put(r,s);r.run(2);r.run(3,1<<1);s=state(r);check('shop weapon purchase',s.coins==100 and s.p.weapon==2);r.run(2);r.run(3,1<<0);r.run(2);check('shop exits',state(r).mode==1)
 # Death must take a life and restore the round through the production entry path.
 # The shop now restores the complete terrain/palette scene on exit. Drain
 # that presentation before replacing the running state with a death fixture.
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.mode=4;s.mode_timer=1;s.p.lives=3;put(r,s)
 for _ in range(120):
  r.run(1);s=state(r)
  if s.mode==1 and s.p.lives==2 and s.p.hp==r.read('progress_max_hp',1)[0]:break
 check('death respawn',s.mode==1 and s.p.lives==2 and s.p.hp==r.read('progress_max_hp',1)[0])
 # Every next-round edge uses production CLEAR -> game_round -> video_round.
 for level in range(8):
  if level:
   s=state(r);s.mode=5;s.mode_timer=1;finish_clear(r,s);r.run(8)
  s=state(r);check(f'round {level+1} entry',s.round==level and s.mode==1)
  s.p.invincible=10000;put(r,s);r.run(30);save(r,f'tested-round{level+1}')
  check(f'round {level+1} cache',int.from_bytes(r.read('video_cache_faults'),'big')==0)
  # Advance normal input for several seconds and ensure logic does not stall.
  f=state(r).frame;shown=int.from_bytes(r.read('pacing_presentations',4),'big')
  r.run(180,(1<<7)|(1<<1));delta=(state(r).frame-f)&65535
  presentations=int.from_bytes(r.read('pacing_presentations',4),'big')-shown
  cadence.append({'round':level+1,'video_frames':180,'logic_updates':delta,'full_rate':delta==180,'presentations':presentations,'full_presentation_rate':presentations==180});check(f'round {level+1} running',delta>0)
  r.run(3,8);r.run(3);check_video_cache(r,state(r));check(f'round {level+1} live VRAM',True)
  # Reset round on death if the open route hits a pit, preserving the next entry test.
  s=state(r);s.mode=1;s.round=level;s.p.hp=4;s.p.lives=3;put(r,s)
 s=state(r);s.mode=5;s.mode_timer=1;finish_clear(r,s);r.run(5);check('ending edge',state(r).mode==6);save(r,'tested-ending')
 out={'cadence':cadence,'full_rate_all_routes':all(x['full_rate'] for x in cadence),'checks':checks,'passed':len(checks),'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'frames':r.frames,'limitations':['full_rate measures simulation updates, not distinct rendered frames.','State injection covers entry and subsystem behavior; does not prove natural completion or arcade fidelity.']};(ROOT/'reports/runtime-tests.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));r.close()
if __name__=='__main__':test()
