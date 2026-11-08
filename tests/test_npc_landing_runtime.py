"""Airborne overlap must not rescue; the same contact triggers after a real landing.

Initial nearby position/velocity and unrelated actor suppression are injected.
Subsequent fall, collision, landing and rescue use native gameplay updates.
"""
import hashlib,json,struct
from pathlib import Path
from test_runtime import ROOT,Runner,state,put
rom=(ROOT/'out/release/rom.bin').read_bytes();meta=json.loads((ROOT/'reports/assets.json').read_text())
r=Runner(ROOT/'out/release/rom.bin')
try:
 r.run(100);r.start_game();r.run(30)
 row,x,y,d,_=next((i,*struct.unpack_from('>4H',rom,r.symbols['spawn0']+i*8)) for i in range(meta['rounds'][0]['spawns']) if meta['actor_definitions'][struct.unpack_from('>H',rom,r.symbols['spawn0']+i*8+4)[0]]['npc_kind']==1)
 s=state(r);s.mode=2;put(r,s);r.run(20)
 s=state(r);s.mode=1;s.p.x=x*256;s.p.y=(y-16)*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;s.cam_x=x-128;s.cam_y=max(0,y-160)
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 s.spawned[row]=0;put(r,s)
 motion=bytearray(struct.pack('>5H20B',s.cam_x,s.cam_y,128,y-16-s.cam_y,0,*([0]*20)));motion[21]=1
 r.write('player_motion',0,motion)
 airborne_contacts=0
 for frame in range(180):
  r.run(1);s=state(r);motion=r.read('player_motion',30)
  actors=[a for a in s.actors if a.active and a.source==row]
  blocked=motion[15] or motion[19] or motion[21]
  if s.mode==8:
   assert not blocked,('dialogue started airborne',frame,list(motion))
   break
  if actors and blocked:
   a=actors[0]
   if abs(s.p.x-a.x)<16*256 and abs(s.p.y-a.y)<24*256:
    assert s.mode==1 and a.state==0 and not s.spawned[row]&2
    airborne_contacts+=1
 else:raise AssertionError('No rescue after landing')
 assert airborne_contacts>=2,('missing airborne overlap coverage',airborne_contacts)
 assert s.rescued==1 and s.spawned[row]&2
 r.capture('v197-npc-after-landing.png')
 result=dict(passed=True,airborne_contacts=airborne_contacts,landing_frame=frame,core=r.lib._name,core_sha256=hashlib.sha256(Path(r.lib._name).read_bytes()).hexdigest(),rom_sha256=hashlib.sha256(rom).hexdigest(),scope=__doc__)
 (ROOT/'reports/npc-landing-runtime-tests.json').write_text(json.dumps(result,indent=2)+'\n')
 (ROOT/'reports'/('npc-landing-'+Path(r.lib._name).stem+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:r.close()
