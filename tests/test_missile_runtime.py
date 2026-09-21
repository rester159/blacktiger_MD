#!/usr/bin/env python3
"""One-contact-tick missile fixtures expose linked-cartridge parity mistakes."""
import json,hashlib,struct
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20);cases=[]
for next_parity,dx,dy in ((0,0,0),(1,0,0),(0,11,12),(0,12,0),(0,0,13),(1,11,12)):
 s=state(r);s.mode=2;put(r,s);r.run(8)
 s=state(r);s.mode=1;s.frame=9+next_parity;s.p.x=128*256;s.p.y=896*256;s.p.vx=s.p.vy=0;s.p.climb=0;s.p.hp=4;s.p.armor=0;s.p.invincible=0;s.time=100;s.clock=0
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 put(r,s);raw=bytearray(26*12)
 # Last frame of the four-frame death clip, but deliberately still a contact-capable
 # projectile. It survives exactly one missile_tick, then retires on the next.
 struct.pack_into('>HH',raw,0,3,2)
 struct.pack_into('>IIhh',raw,8,r.symbols['thrower_21'],r.symbols['thrower_21'],136-dx,904-dy)
 raw[20:25]=bytes([1,0,1,8,4]);r.write('missiles',0,raw)
 for _ in range(60):
  r.run(1)
  if not r.read('missiles',26)[20]:
   r.run(1);break
 s=state(r);hit=next_parity==0 and abs(dx)<=11 and abs(dy)<=12
 assert s.p.hp==(3 if hit else 4),(next_parity,dx,dy,s.p.hp)
 assert not r.read('missiles',26)[20]
 cases.append(dict(frame_parity=next_parity,dx=dx,dy=dy,hit=hit))
r.close();report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Injected one-contact-tick native missiles validate player damage parity and inclusive normal bounds through the real game loop.'}
(ROOT/'reports/missile-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
