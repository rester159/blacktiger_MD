#!/usr/bin/env python3
"""Cartridge death -> source drop -> collection/expiry integration; controlled RNG/player state."""
import hashlib,json,struct
from test_skeleton_runtime import ROOT,Runner,state,put,fixture,fire

def drops(r):
 raw=r.read('loot',33*14)
 return [(i,*struct.unpack_from('>hh',raw,i*14),raw[i*14+12],raw[i*14+13]) for i in range(33) if raw[i*14+12]]

def run():
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);checks=[]
 for variant,expected in enumerate((1,2,2)):
  slot,row,level=fixture(r,variant)
  # Zero is a deliberate deterministic selection fixture, not a normal RNG seed.
  r.write('loot_random',0,b'\0\0');before=state(r).coins
  s=fire(r,slot,100,0);live=drops(r)
  assert len(live)==1,(variant,live)
  index,x,y,active,kind=live[0];assert active==1 and kind==expected,(variant,live)
  assert s.coins==before,'Enemy death must not award coins before contact'
  if variant<2:
   s.p.x=(x-8)*256;s.p.y=(y-8)*256;s.p.vx=s.p.vy=0;put(r,s)
   for _ in range(100):
    r.run(1);s=state(r)
    if s.coins!=before:break
   assert s.coins==before+(1,5,10,50,100,500,1000)[kind],(variant,s.coins,before)
   for _ in range(120):
    r.run(1)
    if state(r).sound_count==0:break
   else:raise AssertionError('coin event queue did not drain')
   assert r.read('sfx_slots',22)[8]==6,('coin cue',variant,r.read('sfx_slots',22).hex())
   r.run(20);assert not drops(r) and state(r).coins==s.coins
   outcome='collected once'
  else:
   start=s.frame
   for _ in range(1200):
    r.run(1);s=state(r)
    if not drops(r):break
   assert not drops(r) and s.coins==before
   assert 230<=((s.frame-start)&65535)<=241,('expiry timing',start,s.frame)
   outcome='expired without reward'
  checks.append({'variant':variant,'kind':kind+1,'outcome':outcome})
 r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Three actual skeleton death callbacks, deterministic injected RNG sample, contact rewards and expiry. Exact source contact bounds and shared-pool contention remain unverified.'}
 (ROOT/'reports/loot-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
