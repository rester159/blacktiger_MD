"""Supported Level 5 column caps stop both the hero and native skeleton falls."""
import hashlib,json,struct
from test_runtime import ROOT,Runner,state,put
from arcade_source import Source
source=Source();raw=source.read(12,0x8000,16384);table=source.files['bdu-03a.8e'][0x363a:0x3e3a]
expected={(992,144),(848,496),(992,496),(1120,496),(1920,496),(832,864),(1664,864),(192,880),(288,880),(1152,880),(96,896)}
cap_cells={(x+dx,y) for x,y in expected for dx in (0,16)}
compiled=(ROOT/'res/generated/collision4.bin').read_bytes()
for y in range(64):
 for x in range(128):
  at=(x&15)|((y&15)<<4)|((x&112)<<4)|((y&48)<<7)
  lo,attr=raw[at*2:at*2+2];original=table[lo+((attr&7)<<8)]
  assert compiled[y*128+x]==(2 if (x*16,y*16) in cap_cells else original),('unexpected collision change',x,y)
rom=(ROOT/'out/release/rom.bin').read_bytes();checks=[]
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(exploration=True);r.run(20)
s=state(r);s.round=4;s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
kind=next(i for i,v in enumerate(rom[r.symbols['skeleton_kinds']:r.symbols['skeleton_kinds']+66]) if v==0)
row=next(i for i in range(160) if struct.unpack_from('>4H',rom,r.symbols['spawn4']+i*8)[2]==kind)
root=json.loads((ROOT/'reference/skeleton.json').read_text())['profiles'][0]['roots'][13]
for x,y in sorted(expected):
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.cam_x=x-112;s.cam_y=max(0,y-176);s.p.x=x*256;s.p.y=(y-96)*256;s.p.vx=s.p.vy=0
 for a in s.actors:a.active=0
 for i in range(160):s.spawned[i]=2
 put(r,s);r.run(30);s=state(r);s.mode=1;put(r,s);r.run(60)
 s=state(r);assert s.p.y//256==y-32 and s.p.grounded,('hero sank into cap',x,y,s.p.y//256)
 # Inject one initialized source skeleton into its falling segment above the
 # same cap, then use unmodified native actor motion and terrain probes.
 s.mode=2;put(r,s);r.run(20);s=state(r)
 a=s.actors[0];a.active=1;a.definition=kind;a.source=row;a.hp=12;a.life=12;a.state=a.hit=0;a.x=x*256;a.y=(y-80)*256;a.vx=a.vy=0
 body=bytearray(30);struct.pack_into('>H',body,16,root)
 r.write('skeletons',0,body);s.mode=1;put(r,s)
 ys=[]
 for _ in range(45):
  r.run(1);a=state(r).actors[0]
  assert a.active,('skeleton unexpectedly retired',x,y)
  ys.append(a.y//256)
 assert y-32<=max(ys)<=y-28,('skeleton sank into cap',x,y,ys)
 checks.append(dict(cap=[x,y],hero_y=state(r).p.y//256,skeleton_lowest_y=max(ys)))
 if (x,y)==(832,864):r.capture('v32-level5-column-fixed.png')
# Walk into a cap from both adjacent lower walkways. The cap is only one
# tile above these floors, which reproduced the original pass-through.
walk_checks=[]
for start,buttons,direction in ((224,128,1),(336,64,-1)):
 s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r)
 s.cam_x=176;s.cam_y=720;s.p.x=start*256;s.p.y=864*256;s.p.vx=s.p.vy=0
 for a in s.actors:a.active=0
 put(r,s);r.run(30);s=state(r);s.mode=1;put(r,s);r.run(60,buttons)
 s=state(r);x=s.p.x//256
 assert (x<=264 if direction==1 else x>=310), ('walked through cap',direction,x)
 assert s.p.y//256==864
 walk_checks.append(dict(direction=direction,stopped_x=x))
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),changed_cells=len(cap_cells),checks=checks,walk_checks=walk_checks,scope=__doc__+' All other source collision cells are unchanged. Player and enemy start positions/state injected above each cap; normal physics thereafter. Not a full playthrough.')
(ROOT/'reports/level5-columns-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
