#!/usr/bin/env python3
import json,hashlib
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
data=json.loads((ROOT/'reference/checkpoint.json').read_text());checks=[]
def death():
 for _ in range(100):
  r.run(1);s=state(r)
  if s.mode==1:return s
 raise AssertionError('restart stalled')
for level in range(8):
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);death()
 # Use four distinct regions in each orientation, including lower/right edges.
 for cell in (0,9,18,31):
  columns=8 if data['wide'][level] else 4
  cx=(cell%columns)*256;cy=(cell//columns)*256
  s=state(r);s.mode=2;put(r,s);r.run(12)
  s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;s.cam_x=cx;s.cam_y=cy
  for i in range(160):s.spawned[i]=2
  put(r,s);s=death();ex,ey=data['grids'][level][cell]
  height=2048 if level==2 else 1024
  py=(ey+144)&(height-1)
  if ey+144>=height:ey=(py-144)&65535 if level==2 else max(0,py-144)
  assert (s.cam_x,s.cam_y,s.p.x,s.p.y)==(ex,ey,(ex+112)*256,py*256),(level,cell,s.cam_x,s.cam_y,s.p.x//256,s.p.y//256,ex,ey)
  assert s.p.vx==s.p.vy==0 and s.p.lives==2
  checks.append(dict(round=level+1,cell=cell,scroll=[ex,ey]))
  s.mode=2;put(r,s);r.run(12)
  if cell==9:r.capture('checkpoint-round-%d.png'%(level+1))
r.close();report={'passed':True,'cases':checks,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'scope':'Actual DEAD-to-PLAY transition for four regions per round: source checkpoint camera, player offset, stopped movement and life debit. Immediate restart placement only; continuous source camera limits and natural full routes remain unverified.'}
(ROOT/'reports/checkpoint-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
