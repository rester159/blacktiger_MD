"""Unused Genesis C must not grant the prototype's extra screen attack."""
import hashlib,json
from test_runtime import ROOT,Runner,state
rom=ROOT/'out/release/rom.bin';snapshots=[]
for extra in (0,256):
 r=Runner(rom);r.run(100);r.run(2,8)
 for tick in range(180):
  keys=128|(1 if tick%60<20 else 0)|(2 if tick%32<8 else 0)
  r.run(1,keys|(extra if tick%12<6 else 0))
 snapshots.append(bytes(state(r))+r.read('player_motion',30)+r.read('player_attack',12)+r.read('player_daggers',162));r.close()
assert snapshots[0]==snapshots[1]
report=dict(passed=True,video_frames=180,c_button_ignored=True,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),scope='Identical real-input movement/jump/attack replay with and without repeated C presses; complete Game, motion, attack and dagger state match. POW pickup behavior remains covered by pickup/cartridge tests.')
(ROOT/'reports/controls-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
