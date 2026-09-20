#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ref=json.loads((ROOT/'reference/eruption_oracle.json').read_text())
for key,path in [('trace_sha256','reference/eruption_oracle_events.txt'),('lua_sha256','tools/eruption_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());definitions=[next(d['id'] for d in meta['actor_definitions'] if (d['bank'],d['address'])==(1,pc)) for pc in (0x8a5d,0x8a03,0x8b9b,0x8bf5)]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','Game game;','#include "'+str(ROOT/'src/eruption.c')+'"']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int definition){game=(Game){0};game.actors[0].def=definition;game.actors[0].active=1;eruption_spawn(0);}
 void constructor_setup(int px,int py){game=(Game){0};game.p.x=px*256;game.p.y=py*256;eruption_reset();}
 void constructor(int x,int y,int *out){out[0]=eruption_prepare(0,x,y);out[1]=game.spawned[0];out[2]=eruption_delay[0];}
 void tick(int clear,int *out){Actor *a=&game.actors[0];EruptionState *s=&eruptions[0];
 if(clear){a->active=0;game.spawned[0]^=1;}if(a->active)eruption_step(0);
 const AnimFrame *f=eruption_frame(0);int v[]={a->active,s->contact,s->animation.remaining,f?f->code:-1,f?f->palette:-1,f?f->flip:-1,game.spawned[0]};for(int i=0;i<7;i++)out[i]=v[i];}
 ''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/animation.c'),str(ROOT/'src/data.c'),str(tmp/'stub.c'),'-o',str(tmp/'e.dylib')],check=True)
 lib=C.CDLL(str(tmp/'e.dylib'));out=(C.c_int*7)();current=None;counts={'BODY':0,'SPAWN':0}
 for line in (ROOT/'reference/eruption_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  tag,case,tick,*values=line.split('|');case=int(case);tick=int(tick);c=ref['cases']['body' if tag=='BODY' else 'spawns'][case]
  if current!=(tag,case):
   if tag=='BODY':lib.setup(definitions[c['kind']])
   else:lib.constructor_setup(c['px'],c['py'])
   current=(tag,case)
  if tag=='BODY':
   a=bytes.fromhex(values[0]);display=bytes.fromhex(values[1]);lib.tick(tick==c['clear'],out)
   assert out[0]==bool(a[0]) and out[6]==int(values[2]),(case,tick,list(out),values)
   if a[0]:
    flip=(a[5]>>3)&1;code=(display[0]-flip)|((a[5]&224)<<3)
    assert list(out)[1:6]==[int(not(a[12]&2)),a[10],code,a[5]&7,flip],(case,tick,list(out),a.hex())
  else:
   lib.constructor(c['x'],c['y'],out);expected=list(map(int,values));expected[0]=bool(expected[0])
   assert list(out)[:3]==expected,(case,tick,list(out),expected)
  counts[tag]+=1
 report={'passed':True,'source_body_ticks':counts['BODY'],'constructor_attempts':counts['SPAWN'],'scope':'All four ground-flame profiles: six-tick startup, 36-tick contact window, six-tick recovery, retirement and forced retirement without reward. Constructor bounds, byte-wrapped player proximity, twentieth eligible attempt and secondary counter persistence. Global scan cadence remains provisional.'}
 (ROOT/'reports/eruption-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
