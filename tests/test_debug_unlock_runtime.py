"""Hidden Debug unlock, edge-triggered code entry, and audible confirmation."""
import json,hashlib,numpy as np
from test_runtime import ROOT,Runner
CODE=(16,16,32,32,64,128,64,128)
def tap(r,key):r.run(8,key);r.run(8)
def boot(home=True):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100)
 if home:tap(r,32)
 tap(r,8);return r
def front(r):return r.read('frontend',20)
r=boot();assert not front(r)[18];r.capture('v36-home-debug-hidden.png')
# Ordinary navigation cannot select the hidden fourth slot.
for key in (128,32,16,64,32,128,32,64):
 tap(r,key);assert front(r)[2]!=3 and not front(r)[18]
# A held Up is one press, not two; wrong directions cannot unlock it.
r.close();r=boot()
r.run(40,16);r.run(8)
for key in CODE[2:]:tap(r,key)
assert not front(r)[18]
for key in (16,16,32,64,32,64,128,64,128):tap(r,key)
assert not front(r)[18]
# A partial code cannot carry across leaving the Home menu.
tap(r,16);tap(r,16);tap(r,1);tap(r,8)
for key in CODE[2:]:tap(r,key)
assert not front(r)[18]
for key in CODE:tap(r,key)
assert front(r)[18] and front(r)[2]==3 and front(r)[1]==1
r.capture('v36-home-debug-revealed.png');tap(r,8);assert front(r)[1]==4
r.capture('v36-debug-unlocked.png');tap(r,1);tap(r,1);tap(r,8)
assert front(r)[18],'unlock should persist for the session'
r.close()
r=boot(False)
for key in CODE:tap(r,key)
assert not front(r)[18],'code must be scoped to Home'
r.close()
# Compare identical music timelines: final Right unlocks, final Left does not.
def sound_run(correct):
 r=boot()
 for key in CODE[:-1]:tap(r,key)
 r.audio_capture=[]
 tap(r,128 if correct else 64);r.run(30)
 a=np.frombuffer(b''.join(r.audio_capture),dtype=np.int16).astype(np.int32)
 r.close();return a
ping=sound_run(True);silent=sound_run(False)
assert ping.shape==silent.shape
changed=int(np.count_nonzero(ping!=silent));assert changed>500,changed
r=boot();assert not front(r)[18],'reset must hide Debug again';r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),hidden_default=True,code=list(CODE),wrong_held_and_cross_menu_rejected=True,session_persistence=True,reset_hides=True,confirmation_changed_audio_samples=changed,scope=__doc__+' Real controller input, RAM menu state, screenshots and native PCM comparison with identical title-music timing.')
(ROOT/'reports/debug-unlock-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
