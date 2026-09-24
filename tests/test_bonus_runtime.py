"""Injected door contacts exercise production transition and map upload paths."""
import json,hashlib,struct
from PIL import Image
from test_runtime import ROOT,Runner,state,put,check_video_cache
ref=json.loads((ROOT/'reference/bonus.json').read_text());cases=[]
for level,lap in [*( (level,0) for level in range(6) ),(2,-2048)]:
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(40)
 s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(100)
 saved=None
 for index,t in enumerate(ref['rounds'][level]['triggers']):
  s=state(r);s.mode=2;put(r,s);r.run(60)
  s=state(r);s.mode=1;s.p.x=(t['x']-8)*256;s.p.y=(t['y']+lap-8)*256;s.p.climb=1;s.p.invincible=10000;s.p.hp=3;s.coins=789;s.score=12345;s.time=100;s.clock=0
  for a in s.actors:a.active=0
  for q in s.shots:q.active=0
  for i in range(160):s.spawned[i]=2
  x=(t['x']-8-128)&65535;y=(t['y']+lap-8-144)&65535
  motion=bytearray(struct.pack('>5H20B',x,y,128,144,0,*([0]*20)));motion[22]=1
  r.write('player_motion',0,motion);r.write('player_attack',0,bytes(12));r.write('player_daggers',0,bytes(18*9));put(r,s)
  for _ in range(160):
   r.run(1)
   if r.read('bonus_consumed',1)[0]&(1<<index):break
  else:raise AssertionError(('door did not trigger',level,index,state(r).p.x//256,state(r).p.y//256))
  s=state(r);s.mode=2;put(r,s);r.run(70);s=state(r)
  if index==0:
   saved=((x&0xff00)|((x+ref['rounds'][level]['return_x_low_add'])&255),y)
   expected=ref['rounds'][level]['camera'];command=0x2d
  else:expected=saved;command=0x21+level
  actual=struct.unpack('>HH',r.read('player_motion',4))
  assert tuple(expected)==actual,(level,index,expected,actual)
  assert r.read('bonus_entered',1)[0]==1
  assert r.read('bonus_consumed',1)[0]==(1<<(index+1))-1
  assert s.p.hp==3 and s.coins==789 and s.score==12345
  assert all(v==2 for v in s.spawned)
  assert r.read('music_command',1)[0]==command
  assert int.from_bytes(r.read('video_cache_faults'),'big')==0
  check_video_cache(r,s)
  if index==0:Image.fromarray(r.frame).save(ROOT/f"reports/bonus-round{level+1}.png")
  cases.append(dict(round=level+1,vertical_lap=lap,trigger=index,camera=list(actual),music=command))
 # Life restart clears the entrance latch but retains consumed door rows.
 s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(100)
 assert r.read('bonus_entered',1)[0]==0 and r.read('bonus_consumed',1)[0]==3
 r.close()
# One round-one doorway also runs normal gravity/ground contact, without a ladder override.
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(40)
s=state(r);s.mode=2;put(r,s);r.run(60)
t=ref['rounds'][0]['triggers'][1];s=state(r);s.mode=1;s.p.x=(t['x']-16)*256;s.p.y=(t['y']-16)*256;s.p.climb=0;s.p.invincible=10000
for a in s.actors:a.active=0
r.write('player_motion',0,bytes(30));put(r,s)
for _ in range(160):
 r.run(1)
 if r.read('bonus_entered',1)[0]:break
else:raise AssertionError('normal grounded entrance failed')
r.run(80)
assert any(a.active and a.definition==0 and a.x//256==128 and a.y//256==232 for a in state(r).actors),'alternate-area hidden-wall actor did not spawn'
Image.fromarray(r.frame).save(ROOT/'reports/bonus-natural-entry.png')
r.close()
report=dict(passed=True,normal_grounded_entrance=True,room_hidden_wall_spawns=True,cases=cases,rewards_and_consumed_rows_preserved=True,restart_latch_reset=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='All 12 injected trigger contacts plus both level-3 contacts in the wrapped vertical lap, both camera branches, source music, preserved rewards/persistence, restart latch and actual VRAM. Grounded ladder fixtures isolate contacts; not a natural playthrough or animation timing test.')
(ROOT/'reports/bonus-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
