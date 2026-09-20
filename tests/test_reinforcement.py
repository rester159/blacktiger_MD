#!/usr/bin/env python3
"""Compare the native two-attempt constructor gate with both original constructors."""
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/reinforcement_oracle.json').read_text())
for key,path in [('trace_sha256','reference/reinforcement_oracle_events.txt'),('lua_sha256','tools/reinforcement_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 (tmp/'stub.c').write_text('#include "'+str(ROOT/'src/reinforcement.c')+'"\n'+'''Game game;
 void setup(int px,int py,int primary,int delay,int waiting,int attempts) {
 game=(Game){0};game.p.x=px*256;game.p.y=py*256;reinforcement_reset();game.spawned[0]=primary;
 reinforcement_rows[0]=(ReinforcementRow){delay,waiting,attempts};}
 void tick(int x,int y,int full,int *out) {out[0]=reinforcement_prepare(0,x,y) && !full;
 out[1]=game.spawned[0];out[2]=reinforcement_rows[0].delay;out[3]=reinforcement_rows[0].waiting;out[4]=reinforcement_rows[0].attempts;}
 ''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(tmp/'stub.c'),'-o',str(tmp/'r.dylib')],check=True)
 lib=C.CDLL(str(tmp/'r.dylib'));current=-1;out=(C.c_int*5)();count=0
 for line in (ROOT/'reference/reinforcement_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  tag,case,tick,*values=line.split('|');case=int(case);c=ref['cases'][case]
  if case!=current:lib.setup(*[c[k] for k in ('px','py','primary','delay','waiting','attempts')]);current=case
  lib.tick(c['x'],c['y'],c['full'],out);expected=list(map(int,values));expected[0]=bool(expected[0])
  assert list(out)==expected,(case,tick,list(out),expected)
  count+=1
report=dict(passed=True,cases=len(ref['cases']),constructor_attempts=count,scope='Both two-attempt reinforcement constructors: screen bounds, byte-wrapped proximity, forty eligible-call delay, row consumption before allocation, full-pool failure and byte overflow. Actor behavior and global scanner cadence remain separate.')
(ROOT/'reports/reinforcement-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
