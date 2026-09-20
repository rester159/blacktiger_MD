#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reports/emerge-oracle.json').read_text());meta=json.loads((ROOT/'reports/assets.json').read_text())
for name,path in [('trace_sha256','reference/emerge_oracle_events.txt'),('lua_sha256','tools/emerge_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[name]
defs=[next(d['id'] for d in meta['actor_definitions'] if d['bank']==2 and d['address']==pc) for pc in (0x8000,0x81a2)]
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','#include "loot.h"','#include "'+str(ROOT/'src/emerge.c')+'"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''static int definitions[2]={%d,%d};static u16 gate_row;
 void setup(int v){game=(Game){0};loot_new();emerge_reset();game.p.x=game.p.y=1000*256;game.actors[0]=(Actor){.active=1,.def=definitions[v],.x=128*256,.y=96*256};emerge_spawn(0);}
 void tick(int contact,int damage){game.frame++;game.p.x=(contact?120:1000)*256;game.p.y=(contact?88:1000)*256;if(damage && emerge_vulnerable(0))emerge_hit(0,damage);if(game.actors[0].active)emerge_step(0);}
 int active(void){return game.actors[0].active;} int hp(void){return game.actors[0].hp;} int persistent(void){return game.spawned[0];}
 int remaining(void){return emerging[0].animation.remaining;} int contacted(void){return emerge_contact;}
 int graphic(void){const AnimFrame *f=emerge_frame(0);return f?f->code:-1;}
 void gate_setup(int v,int seen,int dx){setup(v);for(int r=0;r<8;r++)for(int i=0;i<rounds[r].spawn_count;i++)if(rounds[r].spawns[i].def==definitions[v]){game.round=r;gate_row=i;game.p.x=(rounds[r].spawns[i].x+dx)*256;emerge_seen[i]=seen;emerge_delay[i]=0;return;}}
 int gate(void){return emerge_spawn_ready(gate_row);}
'''%tuple(defs));(tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/s) for s in ('loot.c','hazard.c','player_death.c','armor_break.c','animation.c','data.c')],str(ROOT/'src/progress.c'),str(tmp/'stubs.c'),'-o',str(tmp/'emerge.dylib')],check=True)
 lib=C.CDLL(str(tmp/'emerge.dylib'));ticks=gates=0
 for line in (ROOT/'reference/emerge_oracle_events.txt').read_text().splitlines():
  v=line.split('|')
  if v[0]=='TICK':
   case,tick=map(int,v[1:3]);c=ref['cases'][case];a=bytes.fromhex(v[3]);display=bytes.fromhex(v[4]);persistent=bytes.fromhex(v[5])
   if tick==1:lib.setup(c['variant'])
   damage=(1 if tick==35 else 100) if c['damage'] and tick in (10,35,40) else 0
   lib.tick(c['contact'] and 30<=tick<=34,damage)
   assert bool(lib.active())==bool(a[0]),(case,tick,'active')
   assert lib.hp()==a[14],(case,tick,'hp')
   assert bool(lib.persistent())==bool(persistent[0]&2),(case,tick,'persistent')
   assert lib.contacted()==int(v[6]),(case,tick,'contact')
   if a[0]:
    assert lib.remaining()==a[10],(case,tick,'countdown')
    assert lib.graphic()==display[0]|((display[1]&224)<<3),(case,tick,'graphic')
    assert bool(lib.emerge_vulnerable(0))==((a[12]&3)==0),(case,tick,'vulnerability')
   ticks+=1
  elif v[0]=='SPAWN':
   variant,seen,dx,attempt,active=map(int,v[1:6])
   if attempt==1:lib.gate_setup(variant,seen,dx)
   assert bool(lib.gate())==bool(active),(variant,seen,dx,attempt)
   gates+=1
report={'passed':True,'actor_ticks':ticks,'constructor_attempts':gates,'scope':'Two variants: emerge/expose/contact extension/hide/death, vulnerability, health, animation countdown, persistence and constructor call gates. Global spawn scanner cadence and player damage timing remain provisional.'}
(ROOT/'reports/emerge-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
