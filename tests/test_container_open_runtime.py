#!/usr/bin/env python3
import json,hashlib,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);r.write('progress_max_hp',0,b'\x05');checks=[]
rom=(ROOT/'out/release/rom.bin').read_bytes()
def hold_contact(slot,ticks,near=True):
 start=state(r).frame
 for _ in range(500):
  s=state(r)
  if ((s.frame-start)&65535)>=ticks:return s
  a=s.actors[slot];s.mode=1;s.p.x=a.x+(0 if near else -96*256);s.p.y=a.y;s.p.vx=s.p.vy=0;s.clock=0
  put(r,s);r.run(1)
 raise AssertionError('logic stalled')
for pc in (0xacbe,0xacd3):
 for content in range(6):
  # Each content case starts with independently unopened persistence.
  r.write('container_opened',0,bytes(8));r.write('container_collected',0,bytes(8))
  r.write('container_keys',0,b'\0')
  slot,row,level=fixture(r,0,1,pc);s=state(r);a=s.actors[slot];a.life=content;s.coins=123;s.score=987;s.p.hp=1;s.p.invincible=10000;put(r,s)
  persistent=struct.unpack_from('>4H',rom,r.symbols['spawn'+str(level)]+8*row)[3]-33
  r.write('container_contents',persistent,bytes([content+16]))
  s=hold_contact(slot,4)
  assert not r.read('container_opened',8)[persistent]
  assert r.read('container_locked_hint',1)[0]>0
  if pc==0xacbe and content==0:r.capture('container-locked.png')
  r.write('container_keys',0,b'\x02');s=hold_contact(slot,4)
  assert r.read('container_keys',1)==b'\x01'
  assert r.read('container_locked_hint',1)==b'\0'
  assert r.read('container_opened',8)[persistent]==1
  assert r.read('container_collected',8)[persistent]==(content==0)
  assert s.coins==123 and s.p.hp==1 and s.score==987
  # Leave during opening, so collection remains a distinct contact.
  s=hold_contact(slot,40,False)
  if content==0:
   raw=r.read('container_traps',18*24)
   assert sum(raw[i*18+14]!=0 for i in range(24))==6,(pc,'trap allocation',raw.hex())
  else:
   assert r.read('container_collected',8)[persistent]==0
   s=hold_contact(slot,4)
   assert r.read('container_collected',8)[persistent]==1
   assert s.coins==123+([0,50,100,500,1000,0][content])
   if content==5:assert s.p.hp==5 and s.p.invincible==0
  assert r.read('container_keys',1)==b'\x01' and s.score==987
  before=s.coins;s=hold_contact(slot,6);assert s.coins==before
  # Force camera retirement, then let the actual row reconstruct its empty phase.
  s.mode=1;s.p.x=max(0,s.actors[slot].x//256-700)*256;s.cam_x=max(0,s.p.x//256-112);put(r,s)
  # A direct offscreen actor displacement guarantees retirement even near map edges.
  s=state(r);original=(s.actors[slot].x,s.actors[slot].y);s.actors[slot].x=(s.cam_x+1000)*256;put(r,s);r.run(8)
  s=state(r);assert not s.actors[slot].active
  s.mode=1;s.p.x=original[0]-96*256;s.p.y=original[1]-80*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;put(r,s)
  for _ in range(100):
   r.run(1);s=state(r);found=[i for i,a in enumerate(s.actors) if a.active and a.source==row]
   if found:break
  assert found
  slot=found[0];s=hold_contact(slot,6);assert s.coins==before and r.read('container_keys',1)==b'\x01'
  s.mode=2;put(r,s);r.run(5)
  if content in (0,5):r.capture('container-%x-%d.png'%(pc,content))
  checks.append(dict(constructor=pc,content=content,key_debit_once=True,persistent_empty_respawn=True))
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256(rom).hexdigest(),'scope':'Injected key inventory and contents exercise actual source rows: refusal without key, opening delay, trap allocation, coin/heal collection and empty reconstruction. Natural key acquisition, source startup inventory and equipment maximum remain unported.'}
(ROOT/'reports/container-open-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
