"""Round-two time rescue survives IN/EXIT cleanup before the old man departs."""
import hashlib,json,struct
from test_runtime import ROOT,Runner,state,put
rom=(ROOT/'out/release/rom.bin').read_bytes()
meta=json.loads((ROOT/'reports/assets.json').read_text())
bonus=json.loads((ROOT/'reference/bonus.json').read_text())
r=Runner(ROOT/'out/release/rom.bin')
try:
 r.run(100);r.start_game();r.run(30)
 rows=[(i,*struct.unpack_from('>4H',rom,r.symbols['spawn1']+i*8)) for i in range(meta['rounds'][1]['spawns'])]
 door=bonus['rounds'][1]['triggers'][0]
 row,x,y,d,_=min((t for t in rows if meta['actor_definitions'][t[3]]['npc_kind']==4),key=lambda t:abs(t[1]-door['x'])+abs(t[2]-door['y']))
 s=state(r);s.round=1;s.mode=4;s.mode_timer=0;put(r,s);r.run(100)
 s=state(r);s.mode=2;put(r,s);r.run(30)
 s=state(r);s.mode=1;s.time=120;s.clock=0;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0;s.p.invincible=10000
 s.cam_x=max(0,x-112);s.cam_y=max(0,min(y-144,800))
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 for i in range(160):s.spawned[i]=2
 s.spawned[row]=0;put(r,s)
 for _ in range(160):
  r.run(1)
  if state(r).mode==8:break
 else:raise AssertionError('time NPC contact failed')
 s=state(r);before=s.time;actor=s.rescue_actor
 for _ in range(650):
  r.run(1);s=state(r)
  if s.mode!=8:break
 assert s.mode==1 and s.time==before+30
 assert s.actors[actor].active and s.actors[actor].state==2,'missed pre-departure window'
 # Enter immediately, retaining the real source row's persistence state.
 for index,t in enumerate(bonus['rounds'][1]['triggers']):
  s=state(r);s.mode=2;put(r,s);r.run(20)
  s=state(r);s.mode=1;s.p.x=(t['x']-8)*256;s.p.y=(t['y']-8)*256;s.p.vx=s.p.vy=0;s.p.invincible=10000
  sx=(t['x']-136)&65535;sy=(t['y']-152)&65535
  motion=bytearray(struct.pack('>5H20B',sx,sy,128,144,0,*([0]*20)));motion[22]=1
  r.write('player_motion',0,motion);r.write('shop_poison',0,b'\x26');put(r,s)
  for _ in range(160):
   r.run(1)
   if r.read('bonus_consumed',1)[0]&(1<<index):break
  else:raise AssertionError(('bonus contact failed',index))
  s=state(r);s.mode=2;put(r,s);r.run(30)
  assert state(r).spawned[row]&2,('rescued NPC lost persistence',index)
  assert r.read('shop_poison',1)==b'\0','arcade bonus poison cure changed'
 s=state(r);s.mode=1;s.p.x=x*256;s.p.y=y*256;s.p.vx=s.p.vy=0;s.cam_x=max(0,x-112);s.cam_y=max(0,min(y-144,800));put(r,s)
 r.run(120);s=state(r)
 assert s.mode==1 and s.rescued==1 and s.time<=before+30
 assert not any(a.active and a.source==row for a in s.actors),'time NPC respawned'
 result=dict(passed=True,round=2,row=row,pre_departure_bonus_entry=True,no_second_reward=True,arcade_poison_cure=True,rom_sha256=hashlib.sha256(rom).hexdigest(),scope=__doc__+' Injected positioning; real spawn/contact/dialogue/door paths, not a natural playthrough.')
 (ROOT/'reports/npc-bonus-persistence-runtime-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:r.close()
