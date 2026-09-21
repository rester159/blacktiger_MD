#!/usr/bin/env python3
"""Linked cartridge integration of the three source skeleton constructors."""
import json,struct,hashlib
from pathlib import Path
from test_runtime import Runner,state,put
ROOT=Path(__file__).resolve().parents[1];rom=(ROOT/'out/release/rom.bin').read_bytes()
meta=json.loads((ROOT/'reports/assets.json').read_text());contract=json.loads((ROOT/'reference/skeleton.json').read_text())
def fixture(r,variant,bank=0,constructor=None,approach=96,wait_frames=100,vertical=80,hold_position=False,player_face=None):
 target=contract['constructors'][variant] if constructor is None else constructor;d=next(d['id'] for d in meta['actor_definitions'] if d['bank']==bank and d['address']==target)
 found=None
 for level,info in enumerate(meta['rounds']):
  for row in range(info['spawns']):
   x,y,definition,p=struct.unpack_from('>4H',rom,r.symbols[f'spawn{level}']+8*row)
   if definition==d:found=(level,row,x,y);break
  if found:break
 assert found
 level,row,x,y=found;s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(80)
 s=state(r);s.mode=1;s.p.x=max(0,x-approach)*256;s.p.y=max(0,y-vertical)*256;s.p.vx=s.p.vy=0;s.p.invincible=10000
 if player_face is not None:s.p.face=player_face
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 s.spawned[row]=0;s.cam_x=max(0,min(x-112,meta['rounds'][level]['width']-256));s.cam_y=max(0,min(y-144,meta['rounds'][level]['height']-224));put(r,s)
 for _ in range(wait_frames):
  if hold_position:
   s=state(r);s.p.x=max(0,x-approach)*256;s.p.y=max(0,y-vertical)*256;s.p.vx=s.p.vy=0;put(r,s)
  r.run(1);s=state(r);actors=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
  if actors:
   slot=actors[0];s.mode=2;start=s.frame;put(r,s)
   for _ in range(100):
    r.run(1);s=state(r)
    if ((s.frame-start)&65535)>=3:break
   else:raise AssertionError('camera load stuck')
   return slot,row,level
 raise AssertionError(('source skeleton did not spawn',variant))
def fire(r,slot,damage,face):
 s=state(r);a=s.actors[slot];s.mode=1;s.p.face=face;s.p.invincible=10000;s.clock=0
 q=s.shots[0];q.active=1;q.enemy=0;q.life=30;q.damage=damage;q.kind=0;q.vx=q.vy=0;q.x=a.x+16*256;q.y=a.y+16*256
 start=s.frame;put(r,s)
 # Facing now belongs to the shared native input/controller state.
 r.write("player_motion",25,bytes((face*4,face*4)))
 for _ in range(100):
  r.run(1);s=state(r)
  if ((s.frame-start)&65535)>=3 and not s.shots[0].active:return s
 raise AssertionError(('projectile not handled',slot,damage))
def weapon_edges(r):
 count=0
 for variant,profile in enumerate(contract['profiles']):
  definition=next(d['id'] for d in meta['actor_definitions'] if d['bank']==0 and d['address']==contract['constructors'][variant])
  for dx,dy in ((0,0),(11,12),(-11,-12),(12,0),(0,13)):
   s=state(r);s.mode=2;s.cam_x=16;s.cam_y=752;put(r,s);r.run(60)
   s=state(r);s.mode=1;s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.hp=4;s.p.armor=2;s.p.invincible=0;s.p.climb=0;s.clock=0;s.time=100
   for a in s.actors:a.active=0
   for q in s.shots:q.active=0
   for i in range(160):s.spawned[i]=2
   s.actors[0].definition=definition
   start=s.frame;put(r,s)
   r.write("player_motion",0,struct.pack(">5H20B",0,752,128,144,0,*([0]*20)))
   raw=bytearray(30*24)
   struct.pack_into('>H',raw,10,100)
   struct.pack_into('>Hhh',raw,18,profile['roots'][7],136-dx,904-dy)
   raw[29]=1;r.write('skeletons',0,bytes(raw))
   for _ in range(12):
    r.run(1);s=state(r)
    if s.frame!=start and int.from_bytes(r.read('skeletons',12)[10:12],'big')<100:
     r.run(1);s=state(r);break
   hit=abs(dx)<=11 and abs(dy)<=12
   assert s.p.armor==(1 if hit else 2),(variant,dx,dy,s.p.armor,s.p.x/256,s.p.y/256)
   count+=1
 return count

def run():
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);checks=[]
 for variant,profile in enumerate(contract['profiles']):
  slot,row,level=fixture(r,variant);s=state(r);assert s.actors[slot].hp==profile['durability']
  # Source hurt callback is distinct from the one-point trigger field.
  before=s.kills;s=fire(r,slot,1,0)
  assert s.actors[slot].hp==profile['durability']-1,(variant,'nonfatal damage',s.actors[slot].hp)
  assert s.kills==before
  score=s.score;s=fire(r,slot,100,0)
  assert s.kills==before+1 and s.spawned[row]==2,(variant,'death event')
  assert s.score==score+profile['score'],(variant,'source score')
  assert s.mode==1,(variant,'ordinary enemy incorrectly clears round')
  r.capture(f'skeleton-{variant}-death.png')
  r.run(120);assert not state(r).actors[slot].active,(variant,'death animation did not retire')
  if variant:
   slot,row,level=fixture(r,variant);s=fire(r,slot,1,1)
   assert s.actors[slot].hp==profile['durability'],(variant,'directional guard')
  checks.append({'variant':variant,'round':level+1,'durability':profile['durability'],'spawn_damage_death':True,'guard':bool(variant)})
 edges=weapon_edges(r)
 r.close();report={'weapon_contact_edges':edges,'passed':True,'variants':checks,'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':'Actual source spawns, durability, projectile callbacks, score, ordinary-enemy retirement and shield blocks. Full level playthrough remains unverified.'}
 (ROOT/'reports/skeleton-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
