#!/usr/bin/env python3
"""Stable paused rendering fixtures for pixel-equivalence checks across renderer changes."""
import sys,json,hashlib,struct,ctypes as C,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from test_runtime import Runner,state,put
def validate_sat(r):
 raw=r.read('vdpSpriteCache',64*8);atlas=(ROOT/'res/generated/object_patterns.bin').read_bytes()
 vram=(C.c_uint8*65536).in_dll(r.lib,'vram');counts=[0]*224;pixels=[0]*224
 bodies=struct.unpack('>20H',r.read('body_keys',40));pieces=struct.unpack('>80H',r.read('sprite_keys',160))
 for i in range(64):
  y,size,link,attr,x=struct.unpack_from('>HBBHH',raw,i*8);y-=128
  w=(size>>2)+1;h=(size&3)+1;tile=attr&2047
  for line in range(max(0,y),min(224,y+h*8)):
   counts[line]+=1;pixels[line]+=w*8
  if (w,h)==(4,4):
   assert (tile-1088)%16==0;key=bodies[(tile-1088)//16];expected=b''
   for col in range(4):
    at=(key+col//2)*128+(col%2)*64
    expected+=atlas[at:at+64]+atlas[at+8*128:at+8*128+64]
  else:
   assert (w,h)==(2,2);key=pieces[(tile-1088)//4];expected=atlas[key*128:key*128+128]
  assert bytes(vram[(tile*32+j)^1] for j in range(len(expected)))==expected,('sprite cache texture',i,key)
  if not link:break
 assert max(counts)<=16 and max(pixels)<=256,(max(counts),max(pixels))
meta=json.loads((ROOT/'reports/assets.json').read_text())
chosen=[d['id'] for d in meta['actor_definitions'] if d['pieces']==4 and not d['npc_kind'] and d['kind']!=9 and (d['bank'],d['address']) not in ((0,0x93ed),(0,0x9b85),(0,0xa35c),(2,0xb67f))]
baseline='--baseline-rom' in sys.argv
baseline_dir=Path(os.environ.get('BLACKTIGER_RENDER_BASELINE',str(ROOT/'dist')))
if baseline:assert hashlib.sha256((baseline_dir/'blacktiger_astra.bin').read_bytes()).hexdigest()=='308f65f977665b39b09223d8ddb66f9c3c13389ee601a9d678de13742d826096','Baseline mode requires the d0b1baf cartridge and its matching symbols.'
if '--record' in sys.argv:assert baseline,'Record pixel references only from the pinned baseline cartridge.'
r=Runner((baseline_dir/'blacktiger_astra.bin') if baseline else (ROOT/'out/release/rom.bin'))
if baseline:
 r.symbols={v[2]:int(v[0],16) for line in (baseline_dir/'symbols.txt').read_text().splitlines() if len(v:=line.split())>=3}
r.run(100);r.run(3,8);r.run(30);checks=[];costs=[]
for level in range(8):
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(100)
 for phase in range(6):
  flip=phase&1
  s=state(r);s.mode=2;s.cam_x=128;s.cam_y=128;s.p.x=240*256;s.p.y=188*256;s.p.vx=s.p.vy=0;s.p.grounded=1;s.p.climb=s.p.invincible=0;s.p.attack=(0,5,12,17,8,20)[phase];s.p.face=flip
  s.p.hp=4;s.p.armor=2;s.p.weapon=1;s.p.lives=3;s.score=0;s.coins=123;s.time=160
  for a in s.actors:a.active=0
  for q in s.shots:q.active=0
  for i in range(12):
   d=chosen[(i+phase*6)%len(chosen)]
   a=s.actors[i];a.active=1;a.definition=d;a.x=(s.cam_x-16+(i%4)*80)*256;a.y=(s.cam_y+20+(i//4)*80)*256;a.face=1 if flip else -1;a.hit=a.timer=a.state=0
  for i in range(3):
   q=s.shots[i];q.active=1;q.enemy=i==2;q.kind=i&1;q.x=(s.cam_x+48+i*64)*256;q.y=(s.cam_y+150)*256
  for i in range(12):
   d=meta['actor_definitions'][s.actors[i].definition]
   if (d['bank']==2 and d['address'] in (0x8000,0x81a2,0xa6f8)) or (d['bank']==0 and d['address']==0x8000):s.actors[i].face=-1
  put(r,s)
  # Ported families have private animation state. Initialize their source first
  # frame for this paused renderer fixture, without advancing their gameplay state.
  if 'emerging' in r.symbols:
   for i in range(12):
    d=meta['actor_definitions'][s.actors[i].definition]
    if d['bank']==2 and d['address'] in (0x8000,0x81a2):
     r.write('emerging',i*12,b'\0\0\0\x08'+bytes(8))
  if 'zombies' in r.symbols:
   for i in range(12):
    d=meta['actor_definitions'][s.actors[i].definition]
    if d['bank']==0 and d['address']==0x8000:r.write('zombies',i*16,b'\0\0\0\x18'+bytes(12))
  if 'wisps' in r.symbols:
   for i in range(12):
    d=meta['actor_definitions'][s.actors[i].definition]
    if d['bank']==2 and d['address']==0xa6f8:r.write('wisps',i*12,b'\0\0\0\x06'+bytes(8))
  r.run(100)
  costs.append(struct.unpack('>3H',r.read('video_cost',6))[1])
  if not baseline:validate_sat(r)
  checks.append({'round':level+1,'phase':phase,'sha256':hashlib.sha256(r.frame.tobytes()).hexdigest()})
# Reproduce the old conservative-band overflow with room under hardware scanline limits.
s=state(r);s.p.y=(s.cam_y+92)*256;s.p.attack=0;s.p.face=0
for q in s.shots:q.active=0
for i in range(12):s.actors[i].definition=chosen[i];s.actors[i].face=-1
put(r,s);r.run(100);before=int.from_bytes(r.read('video_dropped_sprites'),'big');r.run(20)
crowded_drops=(int.from_bytes(r.read('video_dropped_sprites'),'big')-before)&65535
if not baseline:validate_sat(r);assert crowded_drops==0
r.close();out=ROOT/'reports/sprite-render-baseline.json'
if '--record' in sys.argv:out.write_text(json.dumps(checks,indent=2)+'\n')
else:
 expected=json.loads(out.read_text());assert checks==expected,[(a,b) for a,b in zip(checks,expected) if a!=b]
 report={'passed':True,'pixel_fixtures':len(checks),'mean_sprite_subticks':sum(costs)/len(costs),'crowded_drops_in_20_frames':crowded_drops,'sprite_cache_vram_and_scanlines_checked':not baseline,'rom_sha256':hashlib.sha256(((baseline_dir/'blacktiger_astra.bin') if baseline else (ROOT/'out/release/rom.bin')).read_bytes()).hexdigest(),'baseline_rom_sha256':'308f65f977665b39b09223d8ddb66f9c3c13389ee601a9d678de13742d826096','scope':'Paused pixel equivalence across all rounds, flips, six hero poses, changing actor textures, clipping and mixed sprite sizes. A crowded fixture checks hardware scanline limits and removal of old false-positive drops; active cache textures are compared directly with VRAM.'}
 (ROOT/('reports/sprite-render-before.json' if baseline else 'reports/sprite-render-tests.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
