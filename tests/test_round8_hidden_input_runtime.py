"""Round 8 lower healing wall: grab the adjacent pole and attack five times.

Only the initial nearby position and actor selection are injected. Pole grab,
stationary attacks, five damage events and terrain opening use controller input.
This is not a full route from the start of the level or a reward-collection test.
"""
import hashlib,json,struct
from test_hidden_runtime import Runner,ROOT,state,put,enter,place,metadata
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20);enter(r,7)
rom=(ROOT/'out/release/rom.bin').read_bytes()
rows=[struct.unpack_from('>4H',rom,r.symbols['spawn7']+i*8) for i in range(metadata['rounds'][7]['spawns'])]
row=next(i for i,v in enumerate(rows) if v[3]==46 and metadata['actor_definitions'][v[2]]['kind']==9)
x,y,_,_=rows[row];slot=place(r,7,row,x,y)
s=state(r);s.mode=2;put(r,s);r.run(20)
s=state(r);s.mode=1;s.p.x=(x-40)*256;s.p.y=(y-4)*256;s.p.face=0;s.p.weapon=1;s.p.vx=s.p.vy=0;s.previous_input=0;put(r,s)
r.write('player_motion',0,struct.pack('>5H20B',x-40-128,y-4-144,128,144,0,*([0]*20)))
s=state(r);s.mode=2;put(r,s);r.run(30)
s=state(r);s.mode=1;put(r,s)
r.run(3,16) # UP grabs the pole; do not keep climbing while firing.
hits=[]
for hit in range(5):
 r.run(30,2);r.run(10);s=state(r);a=s.actors[slot]
 assert (s.p.x//256,s.p.y//256)==(1880,704)
 if hit<4:assert a.hp==4-hit and a.state==0
 else:assert a.state==1 and r.read('world_opened',1)[0]&32
 hits.append(dict(hp=int(a.hp),revealed=bool(a.state)))
r.capture('round8-healing-wall-open-input.png');r.close()
report=dict(passed=True,hits=hits,rom_sha256=hashlib.sha256(rom).hexdigest(),scope=__doc__)
(ROOT/'reports/round8-hidden-input-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
