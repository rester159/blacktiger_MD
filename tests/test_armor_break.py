#!/usr/bin/env python3
"""Compare shared native armor animation against the original small-object loader."""
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/armor_break_oracle.json').read_text())
for key,path in [('trace_sha256','reference/armor_break_oracle_events.txt'),('lua_sha256','tools/armor_break_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'stub.c').write_text('''#include "armor_break.h"
 Game game;
 void setup(int x,int y){game=(Game){0};game.p.armor=4;game.p.x=(x-8)*256;game.p.y=(y-8)*256;armor_break_reset();armor_break_start();}
 void tick(int index,unsigned char *out){armor_break_step();ArmorFragment *a=&armor_fragments[index];const AnimFrame *f=armor_break_frame(index);out[0]=a->active;out[1]=a->x>>8;out[2]=a->x;out[3]=a->y>>8;out[4]=a->y;out[5]=a->anim.remaining;out[6]=a->anim.vx;out[7]=a->anim.vy;if(f){out[8]=f->code;out[9]=((f->code>>3)&224)|f->palette|(f->flip<<3);}}
 ''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/armor_break.c'),str(ROOT/'src/animation.c'),str(tmp/'stub.c'),'-o',str(tmp/'armor.dylib')],check=True)
 lib=C.CDLL(str(tmp/'armor.dylib'));out=(C.c_uint8*10)();current=-1;count=0
 for line in (ROOT/'reference/armor_break_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,actor,sprite=line.split('|');case=int(case);c=ref['cases'][case];a=bytes.fromhex(actor);s=bytes.fromhex(sprite)
  if current!=case:lib.setup(c['x'],c['y']);current=case
  lib.tick(c['profile'],out);v=bytes(out)
  assert bool(v[0])==bool(a[0]),(case,tick,'active',v.hex(),a.hex())
  if a[0]:
   assert v[1:5]==a[1:5] and v[5]==a[10] and v[6:8]==a[6:8] and v[8]==s[0] and v[9]==a[5],(case,tick,v.hex(),a.hex(),s.hex())
  count+=1
 report=dict(passed=True,source_updates=count,cases=len(ref['cases']),scope='Four armor fragments: frame duration, sprite, flip, palette, velocity, position and screen-edge retirement through the original common small-object loader.')
 (ROOT/'reports/armor-break-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
