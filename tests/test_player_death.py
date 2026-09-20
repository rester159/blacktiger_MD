#!/usr/bin/env python3
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/player_death_oracle.json').read_text())
for key,path in [('trace_sha256','reference/player_death_oracle_events.txt'),('lua_sha256','tools/player_death_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'stub.c').write_text('''#include "player_death.h"
 Game game;
 void setup(int profile,int x,int y){game=(Game){0};game.p.x=x*256;game.p.y=y*256;player_death_start(profile/2,profile%2);}
 int tick(unsigned char *out){int done=player_death_step();const PlayerDeathFrame *f=player_death_frame();if(f)for(int i=0;i<2;i++)for(int n=0;n<4;n++){int k=i*16+n*4;int col=n%2;out[k]=(f->code[i]&255)+(col^f->flip[i])+(n/2)*8;out[k+1]=((f->code[i]>>3)&224)|f->palette[i]|(f->flip[i]<<3);out[k+2]=player_death.y[i]+(n/2)*16;out[k+3]=player_death.x[i]+col*16;}return done;}
 int remaining(void){return player_death.remaining;}
 ''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/player_death.c'),str(tmp/'stub.c'),'-o',str(tmp/'death.dylib')],check=True)
 lib=C.CDLL(str(tmp/'death.dylib'));out=(C.c_uint8*32)();current=-1;count=0
 for line in (ROOT/'reference/player_death_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,remain,first,second=line.split('|');case=int(case);tick=int(tick);c=ref['cases'][case]
  if current!=case:lib.setup(c['profile'],c['x'],c['y']);current=case
  done=lib.tick(out);assert done==(tick==329);assert lib.remaining()==int(remain),(case,tick,'duration')
  if not done:assert bytes(out)==bytes.fromhex(first+second),(case,tick,bytes(out).hex(),first+second)
  count+=1
 report=dict(passed=True,source_updates=count,cases=len(ref['cases']),profiles=4,completion_update=329,scope='Four complete source death sequences: two sprite groups, frame durations, motion on frame changes, flipping, palettes and byte-coordinate wrapping.')
 (ROOT/'reports/player-death-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
