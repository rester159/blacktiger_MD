#!/usr/bin/env python3
"""Source boss placement and production mode transitions select original FM cues."""
import json,hashlib
from test_runtime import finish_clear
from test_skeleton_runtime import ROOT,Runner,state,put,fixture
cases=[]
for bank,constructor in ((4,0x9eb1),(4,0x9f16),(1,0x9fc4),(1,0x98a3),(1,0x98e8),(3,0x8000),(3,0x991d),(3,0x9b24)):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
 slot,row,level=fixture(r,0,bank,constructor,approach=32,vertical=64,wait_frames=300)
 expected=(0x29,0x29,0x2a,0x29,0x29,0x2a,0x29,0x2b)[level]
 assert r.read('music_command',1)[0]==expected,(bank,hex(constructor),level,r.read('music_command',1))
 cases.append(dict(round=level+1,constructor=constructor,command=expected));r.close()
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(20)
s=state(r);s.mode=3;put(r,s);r.run(8);assert r.read('music_command',1)[0]==0x2c
s=state(r);s.mode=1;put(r,s);r.run(8);assert r.read('music_command',1)[0]==0x21+s.round
s=state(r);s.mode=5;s.mode_timer=10000;finish_clear(r,s);r.run(8);assert r.read('music_command',1)[0]==0x32
r.run(450);assert r.read('music_active',1)[0]==0
s=state(r);s.mode=2;s.round=7;put(r,s);r.run(80)
s=state(r);s.mode=5;s.mode_timer=10000;finish_clear(r,s);r.run(8);assert r.read('music_command',1)[0]==0x33
before=int.from_bytes(r.read('music_tick'),'big');s=state(r);s.mode=6;put(r,s);r.run(8);after=int.from_bytes(r.read('music_tick'),'big');assert after>before
r.close();report=dict(passed=True,bosses=cases,shop_entry_exit=True,clear_one_shot=True,final_clear_continues_into_ending=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope='Eight actual boss spawns, shop transitions, clear jingle termination and final clear/ending continuity. Full cutscene durations and other event mappings remain separate.')
(ROOT/'reports/music-events-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
