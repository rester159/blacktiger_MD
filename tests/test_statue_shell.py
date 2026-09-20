#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/statue_shell_oracle.json').read_text())
for key,path in [('trace_sha256','reference/statue_shell_oracle_events.txt'),('lua_sha256','tools/statue_shell_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definition=next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(0,0xb84f))
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/statue_shell.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int direction) {
 game=(Game){0};game.p.x=160*256;game.p.y=120*256;statue_shell_reset();statue_shell_spawn(128,96,direction);}
 void tick(int hit,int contact,int *out) {
 if(hit)statue_shell_hit(0);if(contact)statue_shell_contact(0);statue_shell_tick();
 for(int n=0;n<2;n++) {
 StatueShell *s=n?&statue_blasts[0]:&statue_shells[0];const AnimFrame *f=statue_shell_frame(s);
 int v[]={s->active,s->x,s->y,s->cycles,s->mode,s->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1};
 for(int i=0;i<9;i++)out[n*9+i]=v[i];}}
''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/name) for name in ('animation.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));out=(C.c_int*18)();current=-1;count=0
 for line in (ROOT/'reference/statue_shell_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  _,case,tick,a,display,clear,persist,blast=line.split('|');case=int(case);tick=int(tick);c=ref['cases'][case]
  if current!=case:lib.setup(case//3);current=case
  lib.tick(tick==c['hit_tick'],tick==c['contact_tick'],out)
  ba,bd=blast.split(':')
  for n,(actor,disp) in enumerate(((a,display),(ba,bd))):
   actor=bytes.fromhex(actor);disp=bytes.fromhex(disp);actual=list(out)[n*9:n*9+9]
   assert actual[0]==bool(actor[0]),(case,tick,n,'active',actual,actor.hex())
   if actor[0]:
    flip=(actor[5]>>3)&1;code=(disp[0]-(flip if n else 0))|((actor[5]&224)<<3)
    expected=[1,int.from_bytes(actor[1:3],'big',signed=True),int.from_bytes(actor[3:5],'big',signed=True),actor[8],actor[12],actor[10],code,actor[5]&7,flip]
    assert actual==expected,(case,tick,n,actual,expected)
  count+=1
 report={'passed':True,'source_projectile_ticks':count,'cases':len(ref['cases']),'scope':'All 16 shell directions, cycle expiry, weapon hit, player contact and independent explosion animation. Integrated native effects; shared source allocation contention not reproduced.'}
 (ROOT/'reports/statue-shell-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
