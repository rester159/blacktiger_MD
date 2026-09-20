#!/usr/bin/env python3
"""Linked-cartridge player frame tables and hardware-sprite composition."""
import ctypes as C,json,hashlib,sys,struct
from test_runtime import *
sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
class Motion(BE):
 _fields_=[(k,U16) for k in ('scroll_x','scroll_y','screen_x','screen_y','jump_origin')]+[(k,S8) for k in ('vx','vy')]+[(k,U8) for k in ('fraction','subtick','pose','jumping','jump_request','direction','redirected','camera_return','below_origin','falling','ladder','low','frame','selector','previous','idle','jump_history','screen_motion')]
assert C.sizeof(Motion)==30
source=Source();r=Runner(ROOT/'out/release/rom.bin');r.run(100)
rom=(ROOT/'out/release/rom.bin').read_bytes();address=r.symbols['hero_frames'];frames=[]
for armored,root in enumerate((0x9698,0x9120)):
 for pose in range(10):
  table=source.word(7,root+pose*2)
  for selector in range(6):
   first=source.word(7,table+selector*2)
   for index in range(8):
    base,attr,weapon,wa,dx,dy=source.read(7,first+index*6,6);flip=(attr>>3)&1
    codes=[base,base+1,base+8,base+9]
    if flip:codes=[base+1,base,base+9,base+8]
    expected=struct.pack('>5H4B',*[c|((attr&224)<<3) for c in codes],weapon|((wa&224)<<3),flip,(wa>>3)&1,dx,dy)
    offset=((armored*10+pose)*48+selector*8+index)*14
    assert rom[address+offset:address+offset+14]==expected,(armored,pose,selector,index)
    frames.append(expected)
s=state(r);s.mode=2;s.cam_x=0;s.cam_y=800;s.p.x=128*256;s.p.y=896*256;s.p.invincible=s.p.attack=0
for a in s.actors:a.active=0
for q in s.shots:q.active=0
r.write("player_attack",0,bytes(12));r.write("player_daggers",0,bytes(18*9));put(r,s);r.run(20)
checks=0
for armor in (0,2):
 for selector in range(6):
  for pose in (0,6,12,18):
   s=state(r);s.p.armor=armor;s.p.weapon=1;put(r,s)
   motion=Motion();motion.pose=pose;motion.selector=selector;motion.frame=3
   r.write('player_motion',0,bytes(motion));r.run(8)
   sat=r.read('vdpSpriteCache',16)
   y,size,link,attr,x=struct.unpack_from('>HBBHH',sat)
   assert (x-128,y-128,size)==(128,96,15),(armor,selector,pose,sat.hex())
   key=struct.unpack('>20H',r.read('body_keys',40))[((attr&2047)-1088)//16]
   raw=frames[((bool(armor)*10+pose//2)*48+selector*8+3)]
   codes=struct.unpack('>5H4B',raw)
   assert key==codes[0]-codes[5] and bool(attr&0x800)==bool(codes[5]),(armor,selector,pose,key,codes)
   checks+=1
   if selector==1 and pose==0:r.capture('player-crouch-'+str(armor)+'.png')
# Normal inputs exercise the native controller and exported crouch-aim state.
s=state(r);s.mode=1;s.previous_input=0;s.p.x=112*256;s.p.y=896*256;s.p.invincible=1000
for i in range(160):s.spawned[i]=2
put(r,s);r.run(12,1<<5)
m=Motion.from_buffer_copy(r.read('player_motion',30));assert m.low and m.selector==1
assert r.read('reinforcement_player_low',1)==b'\x01'
r.run(12,1<<7);m=Motion.from_buffer_copy(r.read('player_motion',30));assert not m.low and m.vx==2
r.run(4);start=state(r).p.y;r.run(6,1);s=state(r);assert s.p.y<start and s.p.vy<0
r.capture('player-native-jump.png');r.close()
report=dict(passed=True,source_frame_records=len(frames),hardware_sprite_cases=checks,native_input_checks=3,rom_sha256=hashlib.sha256(rom).hexdigest(),scope='All armor/pose/selector/frame records and paused hardware body composition; real crouch, walk and jump input. Attack timing is checked separately; full-game routes remain unverified.')
(ROOT/'reports/player-motion-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
