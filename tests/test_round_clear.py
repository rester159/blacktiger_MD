#!/usr/bin/env python3
import ctypes as C, hashlib, json, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/clear_oracle.json').read_text())
for key,path in [('trace_sha256','reference/clear_oracle_events.txt'),('lua_sha256','tools/clear_oracle.lua')]:
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
frames={};ends={}
for line in (ROOT/'reference/clear_oracle_events.txt').read_text().splitlines():
 v=line.split('|')
 if v[0]=='FRAME':frames.setdefault(int(v[1]),[]).append((int(v[2]),int(v[3]),int(v[4]),bytes.fromhex(v[5]+v[6])))
 if v[0]=='END':ends[int(v[1])]=int(v[2])
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder)
 (tmp/'stub.c').write_text('''#include "round_clear.h"
 Game game;
 void setup(int round,int weapon,int armor,int coins){game=(Game){0};game.round=round;game.p.weapon=weapon+1;game.p.armor=armor;game.p.hp=1;game.coins=coins;game.p.x=112*256;game.p.y=144*256;round_clear_reset();round_clear_start();}
 int tick(unsigned char *out){int done=round_clear_step();const ClearFrame *f=round_clear_frame();if(f && !f->hold)for(int i=0;i<6;i++){const ClearSprite *s=&f->sprites[i];out[i*4]=s->code;out[i*4+1]=((s->code>>3)&224)|s->palette|(s->flip<<3);out[i*4+2]=round_clear.y+s->dy;out[i*4+3]=round_clear.x+s->dx;}return done;}
 int coins(void){return game.coins;}int armor(void){return game.p.armor;}int hp(void){return game.p.hp;}int phase(void){return round_clear.phase;}
 ''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/round_clear.c'),str(tmp/'stub.c'),'-o',str(tmp/'clear.dylib')],check=True)
 lib=C.CDLL(str(tmp/'clear.dylib'));out=(C.c_uint8*24)();updates=0
 for case,seq in frames.items():
  c=ref['cases'][case];lib.setup(c['round'],c['weapon'],c['armor'],200)
  for tick,delay,armor,raw in seq:
   for n in range(delay):
    assert lib.tick(out)==0,(case,tick+n,'early completion')
    assert lib.armor()==armor and lib.hp()==1
    if not(tick==0 and c['armor']==0):assert bytes(out)==raw,(case,tick+n,bytes(out).hex(),raw.hex())
    assert lib.coins()==200;updates+=1
  assert sum(f[1] for f in seq)==ends[case]
  if c['round']==7:assert lib.tick(out)==1 and lib.coins()==200
  else:
   assert lib.tick(out)==0 and lib.phase()==2 and lib.coins()==500
   for _ in range(239):assert lib.tick(out)==0 and lib.coins()==500
   assert lib.tick(out)==1 and lib.coins()==500
 rewards=[300,500,800,1200,1600,2400,4800,0]
 for round,reward in enumerate(rewards):
  assert lib.round_clear_reward(round)==reward
  for coins in [0,200,65000,65535]:
   lib.setup(round,0,2,coins)
   for _ in range(400):
    done=lib.tick(out)
    if done:break
   assert done and lib.coins()==(coins+reward)%65536
 report=dict(passed=True,source_animation_cases=len(frames),source_animation_updates=updates,reward_cases=32,bonus_hold_updates=240,scope='All weapons, armored/unarmored, ordinary/final source sprite sequences and durations; armor restoration without healing; once-only Zenny awards and overflow. Bonus background/fades and final cutscene excluded.')
 (ROOT/'reports/round-clear-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
