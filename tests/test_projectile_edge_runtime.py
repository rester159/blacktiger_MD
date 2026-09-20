#!/usr/bin/env python3
import json,hashlib,struct
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.run(3,8);r.run(20);checks=[]
for x,y,alive in ((-64,96,False),(320,96,False),(128,-64,False),(128,320,False),(0,96,True),(255,96,True),(128,0,True),(128,255,True)):
 s=state(r);s.mode=2;put(r,s);r.run(12);s=state(r)
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 s.mode=1;s.p.x=(s.cam_x+128)*256;s.p.y=(s.cam_y+112)*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;s.clock=0
 start=s.frame;put(r,s)
 raw=bytearray(26*12);struct.pack_into('>HH',raw,0,0,100)
 struct.pack_into('>IIhh',raw,8,r.symbols['thrower_21'],r.symbols['thrower_21'],s.cam_x+x,s.cam_y+y)
 raw[20:26]=bytes([1,0,1,8,4,1]);r.write('missiles',0,raw)
 for _ in range(20):
  r.run(1)
  if ((state(r).frame-start)&65535)>=3:break
 assert bool(r.read('missiles',26)[20])==alive,(x,y,alive,r.read('missiles',26).hex())
 checks.append(dict(screen_x=x,screen_y=y,remains_active=alive))
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()}
(ROOT/'reports/projectile-edge-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
