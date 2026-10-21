#!/usr/bin/env python3
"""Source 237C..23C5 round-start notice: ROUND n / READY PLAYER 1 / SAVE n LIFE(S) for 122 updates."""
import json,hashlib
import numpy as np
from test_runtime import ROOT,Runner,state,put
r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3,notice=True)
def ready():return r.read('round_ready',1)[0]
def cells(row,first,count):
 """Pixels of text-plane cells (port row = source row - 2)."""
 return r.frame[row*8:row*8+8,first*8:(first+count)*8].astype(int)
def enter(lives):
 for _ in range(400):
  r.run(1)
  if state(r).mode==1 and ready():break
 else:raise AssertionError('no notice after round entry')
 s=state(r);assert ready()==122 and s.p.lives==lives,(ready(),s.p.lives,lives)
 return s
def hold_and_release(name):
 r.run(2);s=state(r);x,time=s.p.x,s.time
 text=[cells(8,13,5),cells(13,10,14),cells(15,11,12)]
 r.capture(name+'.png')
 r.run(60,1<<7)  # holding right must not move the player or start the clock
 s=state(r);assert (s.p.x,s.time)==(x,time),('moved during notice',s.p.x,x,s.time,time)
 for _ in range(122):
  if not ready():break
  r.run(1)
 assert not ready();r.run(2)
 for before,after in zip(text,[cells(8,13,5),cells(13,10,14),cells(15,11,12)]):
  assert np.abs(before-after).sum()>0,'notice text was not drawn or not erased'
 r.run(20,1<<7);assert state(r).p.x!=x,'play did not resume after notice'
cases=[]
enter(3);hold_and_release('round-ready-start');cases.append('new game: SAVE 3 LIVES')
s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s)
enter(2);hold_and_release('round-ready-death');cases.append('after death: SAVE 2 LIVES')
s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=2;put(r,s)
enter(1);hold_and_release('round-ready-last-life');cases.append('last life: SAVE 1 LIFE')
r.close()
report={'passed':True,'cases':cases,'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),
 'scope':'Linked ROM: notice appears on new game and each life restart, holds player input and the round clock for 122 updates, draws and erases the three text rows. Glyph codes, positions and timing come from source 16AD/237C via tools/build_hud.py. Colors are nearest actor-palette pens; real-hardware timing unverified.'}
(ROOT/'reports/round-ready-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
