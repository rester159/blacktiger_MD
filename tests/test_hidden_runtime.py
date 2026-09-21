#!/usr/bin/env python3
"""Native cartridge: source-owned wall rows, damage, terrain pixels, rewards, persistence."""
import json,struct,hashlib,ctypes as C
from pathlib import Path
from test_runtime import Runner,state,put,check_video_cache
ROOT=Path(__file__).resolve().parents[1]
metadata=json.loads((ROOT/'reports/assets.json').read_text());contract=json.loads((ROOT/'reference/hidden.json').read_text())
rom=(ROOT/'out/release/rom.bin').read_bytes()
def enter(r,level):
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(60)
def place(r,level,row,x,y):
 s=state(r);s.mode=1;s.p.x=max(0,x-64)*256;s.p.y=(y-8)*256;s.p.vx=s.p.vy=0;s.p.hp=1;s.p.armor=2;s.p.lives=3;s.p.invincible=10000;s.coins=123;s.score=0;s.time=120;s.clock=0
 # At the left edge, stand on the right side to avoid collecting the reward.
 if x<64:s.p.x=(x+64)*256
 s.cam_x=max(0,min(x-112,metadata['rounds'][level]['width']-256));s.cam_y=max(0,min(y-144,metadata['rounds'][level]['height']-224))
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 s.spawned[row]=0;put(r,s)
 for _ in range(30):
  r.run(1);s=state(r)
  found=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
  if found:
   slot=found[0];s.mode=2;start_frame=s.frame;put(r,s)
   for _ in range(100):
    r.run(1);s=state(r)
    if (s.frame-start_frame)&65535>=3:break
   else:raise AssertionError('camera load did not settle')
   s.mode=1;put(r,s);return slot
 raise AssertionError(('wall did not spawn',level,row))
def vram_patch(r,level,patch):
 s=state(r);v=(C.c_uint8*65536).in_dll(r.lib,'vram');patterns=(ROOT/(f'res/generated/backdrop_bg{level}.bin' if level in (3,5,6) else f'res/generated/bg{level}.bin')).read_bytes()
 remap=None
 if level in (3,5,6):
  data=(ROOT/f'res/generated/backdrop_remap{level}.bin').read_bytes();n=len(data)//4;remap=struct.unpack('>'+str(n*2)+'H',data)
 start=r.symbols[f'open_tile{level}'];words=struct.unpack_from('>4H',rom,start)
 checked=0
 for dy in range(4):
  for dx in range(2):
   x=patch['x']//8+dx;y=patch['y']//8+dy
   if not(s.cam_x//8<=x<s.cam_x//8+33 and s.cam_y//8<=y<s.cam_y//8+29):continue
   at=0xe000+((y&31)*64+(x&63))*2;actual=(v[at^1]<<8)|v[(at+1)^1];expected=words[(dy%2)*2+dx]
   if remap is not None:expected=(expected&0xf800)|0x8000|remap[((expected>>13)&1)*n+(expected&2047)]
   assert actual&0xf800==expected&0xf800,('patch attributes',level,patch,x,y)
   tile=(expected&2047)-16;physical=actual&2047
   assert bytes(v[(physical*32+k)^1] for k in range(32))==patterns[tile*32:tile*32+32],('patch pixels',level,patch,x,y,hex(actual),hex(expected),r.read('world_opened',1).hex(),(s.cam_x,s.cam_y),r.read('old_x').hex(),r.read('old_y').hex(),r.read('video_cache_faults').hex(),r.read('logical_to_slot',2*(tile+1))[-2:].hex())
   checked+=1
 assert checked==8,('patch outside verification view',checked)
def fire(r,slot):
 s=state(r);initial_frame=s.frame;a=s.actors[slot];a.hit=0
 q=s.shots[0];q.active=1;q.enemy=0;q.life=40;q.damage=1;q.kind=0;q.vx=q.vy=0;q.x=a.x+8*256;q.y=a.y+8*256
 put(r,s)
 for _ in range(12):
  r.run(1);s=state(r)
  if not s.shots[0].active:return s
 raise AssertionError(('wall did not consume projectile',initial_frame,s.round,s.mode,s.frame,s.actors[slot].source,s.actors[slot].state,s.actors[slot].active,s.shots[0].x,s.shots[0].y,r.read('old_x').hex(),r.read('old_y').hex(),s.cam_x,s.cam_y))
def run():
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);r.write('progress_max_hp',0,b'\x05');results=[];reward_kinds=set()
 for level,patches in enumerate(contract['rounds']):
  for patch_index,patch in enumerate(patches):
   enter(r,level)
   count=metadata['rounds'][level]['spawns'];start=r.symbols[f'spawn{level}'];rows=[struct.unpack_from('>4H',rom,start+i*8) for i in range(count)]
   row=next(i for i,v in enumerate(rows) if v[3]==patch['persistent'] and metadata['actor_definitions'][v[2]]['kind']==9)
   x,y,d,_=rows[row];slot=place(r,level,row,x,y)
   assert state(r).actors[slot].hp==5
   before=(state(r).actors[slot].x,state(r).actors[slot].y)
   for damage in range(1,6):
    s=fire(r,slot)
    assert (s.actors[slot].x,s.actors[slot].y)==before,('closed wall moved',level,row)
    assert bool(r.read('world_opened',1)[0]&(1<<patch_index))==(damage==5)
    if damage<5:assert s.actors[slot].hp==5-damage
   r.run(5);vram_patch(r,level,patch)
   if len(results)==0:r.capture('hidden-open.png')
   kind=(metadata['actor_definitions'][d]['address']-0xb7da)//23
   # Move away and back while preserving the open terrain and uncollected item.
   s=state(r);s.actors[slot].active=0;s.spawned[row]=0;put(r,s)
   for _ in range(12):
    r.run(1);s=state(r)
    found=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
    if found:slot=found[0];break
   assert s.actors[slot].state==1,('closed wall respawned',level,row)
   r.run(5);s=state(r);a=s.actors[slot];s.p.x=a.x;s.p.y=a.y;s.p.vx=s.p.vy=0;s.p.invincible=10000;s.clock=0
   baseline=(s.p.lives,s.p.armor,s.p.hp,s.time,s.coins,s.score);put(r,s)
   for _ in range(12):
    r.run(1);s=state(r)
    if s.spawned[row]==2:break
   assert s.spawned[row]==2,('reward not collected',level,row,kind)
   life,armor,hp,time,coins,score=baseline
   expected=(life+(kind==1),min(8,armor+({2:2,6:2,7:3}.get(kind,0))),5 if kind==2 else hp,time+(30 if kind==4 else 0),coins+({5:1000,10:500}.get(kind,0)),score+({8:1000,9:5000,11:7000}.get(kind,0)))
   actual=(s.p.lives,s.p.armor,s.p.hp,s.time,s.coins,s.score);assert actual==expected,(kind,actual,expected)
   s=state(r);s.mode=2;put(r,s);r.run(50);vram_patch(r,level,patch);reward_kinds.add(kind);results.append({'round':level+1,'persistent':patch['persistent'],'kind':kind})
 r.close()
 report={'passed':True,'wall_cases':len(results),'reward_kinds':sorted(reward_kinds),'cases':results,'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':'All actual wall rows: five hits, stationary closed actors, live VDP replacement pixels, reveal, reward, open-state respawn and collection. Screen-attack target fidelity is not covered.'}
 (ROOT/'reports/hidden-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
