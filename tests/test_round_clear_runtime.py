#!/usr/bin/env python3
"""Real cartridge clear states, native frame progression, payout and transitions."""
import json,hashlib,struct
from test_runtime import ROOT,Runner,state,put
source_frames={}
for line in (ROOT/'reference/clear_oracle_events.txt').read_text().splitlines():
 v=line.split('|')
 if v[0]=='FRAME':source_frames.setdefault(int(v[1]),[]).append(bytes.fromhex(v[5]+v[6]))
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(30);cases=[]
for final in (False,True):
 for weapon in range(1,6):
  for armor in (0,2):
   s=state(r);s.mode=2;put(r,s);r.run(60)
   s=state(r);s.mode=5;s.round=7 if final else 0;s.mode_timer=0;s.coins=200;s.p.weapon=weapon;s.p.armor=armor;s.p.hp=1;s.p.x=(s.cam_x+112)*256;s.p.y=(s.cam_y+144)*256
   for a in s.actors:a.active=0
   for q in s.shots:q.active=0
   r.write('player_motion',15,b'\0');r.write('player_motion',21,bytes(2));r.write('round_clear',0,bytes(8));put(r,s)
   seen=set();bonus=False;sprite_check=False
   case=(10 if final else 0)+(weapon-1)*2+(armor!=0)
   for _ in range(1800):
    r.run(1);s=state(r);c=r.read('round_clear',8)
    if s.mode!=5:break
    if c[0]==1:
     seen.add(c[3]);assert s.coins==200 and s.p.hp==1 and s.p.armor==2,(final,weapon,armor,'victory resources')
    if c[0]==1 and c[4]==40 and not sprite_check:
     raw=source_frames[case][c[3]-1];expected=[]
     for at in range(0,24,4):
      code,attr,y,x=raw[at:at+4]
      if y:expected.append(((code|((attr&224)<<3))+(attr&7)*2048,bool(attr&8),(x-112+c[5])%256,(y-144+c[6])%256,3 if attr&7 else 2))
     sat=r.read('vdpSpriteCache',len(expected)*8);keys=struct.unpack('>80H',r.read('sprite_keys',160));actual=[]
     for at in range(0,len(sat),8):
      y,size,link,attr,x=struct.unpack_from('>HBBHH',sat,at);assert size==5
      actual.append((keys[((attr&2047)-1088)//4],bool(attr&0x800),x-128,y-128,(attr>>13)&3))
     assert actual==expected,(case,actual,expected)
     sprite_check=True
     if not final and weapon==1:r.capture('round-clear-victory-'+str(armor)+'.png')
    if c[0]==2:
     bonus=True;assert not final and s.coins==500 and s.p.hp==1
     if weapon==1 and armor==0 and s.mode_timer==200:r.capture('round-clear-bonus.png')
   assert s.mode==(6 if final else 1),(final,weapon,armor,'transition',s.mode,list(c))
   assert s.coins==(200 if final else 500) and bonus!=final and sprite_check
   case=(10 if final else 0)+(weapon-1)*2+(armor!=0)
   expected=sum(line.startswith(f'FRAME|{case}|') for line in (ROOT/'reference/clear_oracle_events.txt').read_text().splitlines())
   assert set(range(1,expected+1))<=seen,(weapon,armor,expected,seen)
   cases.append(dict(final=final,weapon=weapon,armor=armor,frames_observed=len(seen),bonus=bonus,hardware_sprites=True))
r.close()
# Clear entry during an actual native jump must finish landing before restoring armor.
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(30)
s=state(r);s.mode=2;put(r,s);r.run(60)
s=state(r);s.mode=1;s.p.x=112*256;s.p.y=896*256;s.p.invincible=1000;s.previous_input=0
for a in s.actors:a.active=0
for i in range(160):s.spawned[i]=2
put(r,s);r.run(4);r.run(6,1)
assert r.read('player_motion',30)[15]
s=state(r);s.mode=2;put(r,s);r.run(60)
s=state(r);s.mode=5;s.p.armor=0;s.p.hp=1;s.coins=200;r.write('round_clear',0,bytes(8));put(r,s)
waiting=0
for _ in range(300):
 r.run(1);s=state(r);c=r.read('round_clear',8)
 if c[1]:break
 waiting+=1;assert s.p.armor==0 and s.coins==200
assert waiting>3 and c[1] and s.p.armor==2
m=r.read('player_motion',30);assert not(m[15] or m[21] or m[22])
r.close();report=dict(passed=True,cases=cases,airborne_entry_wait=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Injected grounded clear entry in cartridge, every weapon/armor profile, animation progression, source-matched hardware victory pose in all 20 profiles, no healing during victory, once-only ordinary payout, ordinary next-round and final ending transitions. Source frame bytes/timing checked separately; not a natural boss playthrough.')
(ROOT/'reports/round-clear-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
