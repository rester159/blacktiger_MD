"""Arcade Start coin slot, A selection, source coin jingle and title credits."""
import hashlib,json,struct
import numpy as np
from test_runtime import ROOT,Runner,state,put
from arcade_source import Source
source=Source()
source.expect(None,0x0a3a,'3e20cde203') # coin chute sound, before coinage award
source.expect(None,0x0a62,'3affe1fe09') # original credit cap
assert source.read(None,0x16fa,6)==b'CREDIT'
checks=[]
def check(name,ok):assert ok,name;checks.append(name)
def tap(mask):r.run(8,mask);r.run(8)
def credits():return r.read('frontend',9)[4]
r=Runner(ROOT/'out/release/rom.bin');r.run(100)
tap(2);check('A selects Arcade menu',r.read('frontend',2)==bytes([0,1]))
tap(2);check('A cannot start with no credit',state(r).mode==0 and credits()==0)
r.audio_capture=[];r.run(30,8)
check('held Start inserts exactly one coin and stays in menu',credits()==1 and state(r).mode==0)
check('source FM coin command 20 plays on title',r.read('music_command',1)==b'\x20' and r.read('music_active',1)==b'\1')
check('coin produces audible PCM',np.max(np.abs(np.frombuffer(b''.join(r.audio_capture),np.int16).astype(np.int32)))>100)
r.run(8);tap(8);check('fresh Start edge adds another credit',credits()==2)
check('fresh coin retriggers jingle',int.from_bytes(r.read('music_tick'),'big')<100)
r.capture('v12-arcade-credits.png')
for _ in range(10):tap(8)
check('arcade source credit cap is nine',credits()==9)
# Coin audio belongs to Sound FX, independently of background Music.
r.write('settings',4,b'\0');tap(8)
check('coin jingle works with Music OFF',r.read('music_command',1)==b'\x20' and r.read('music_active',1)==b'\1')
r.run(100);r.write('settings',5,b'\0');tap(8)
check('Sound FX OFF suppresses coin jingle',r.read('music_active',1)==b'\0')
r.write('settings',4,b'\1\1')
# Coin sound is per inserted coin, even before multi-coin pricing awards a credit.
r.write('frontend',4,b'\0\0');r.write('frontend',8,b'\0');r.write('settings',2,b'\0')
for n in range(4):
 tap(8);check('4C/1C credit count after coin %d'%(n+1),credits()==int(n==3))
 check('4C/1C every coin plays source sound %d'%(n+1),r.read('music_command',1)==b'\x20' and int.from_bytes(r.read('music_tick'),'big')<100)
r.write('settings',2,b'\3');tap(2)
check('A starts and spends one credit',state(r).mode==9 and credits()==0)
r.run(40);tap(2);r.run(20);check('A skips arcade intro',state(r).mode==1)
tap(8);check('Start adds a coin during play without pausing',state(r).mode==1 and credits()==1)
check('credit accounting updates during gameplay',r.read('hud_credit',1)==b'\1')
r.capture('v12-arcade-game-credits.png')
# Complete last-life death using the normal restart/continue handler.
s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=1;put(r,s)
for _ in range(1200):
 r.run(1)
 if state(r).mode==7 and r.read('game_over',4)[2]==2:break
else:raise AssertionError('continue offer absent')
tap(8);check('Start adds credit without accepting continue',state(r).mode==7 and credits()==2)
r.capture('v12-arcade-continue.png');tap(2);check('A accepts continue and spends one credit',state(r).mode==1 and credits()==1)
s=state(r);s.mode=2;put(r,s);r.run(20);s=state(r);s.mode=3;put(r,s);r.run(20);tap(8)
check('shop coin accounting updates without a purchase',state(r).mode==3 and credits()==2 and r.read('hud_credit',1)==b'\2')
check('version metadata is v1.5',json.loads((ROOT/'reference/title_graphics.json').read_text())['version_stamp']['text']=='v1.5')
r.close()
report=dict(passed=True,checks=checks,source_witnesses=list(source.witnesses.values()),rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope=__doc__+' Coin FM stream has separate original-ROM register-trace checks; native PCM audibility tested here. CREDIT follows the original title-screen position; gameplay and shop retain the original Zenny HUD.')
(ROOT/'reports/arcade-coin-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=checks)))
