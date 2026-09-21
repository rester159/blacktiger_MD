#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,re,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
from actor_contract import load
ref=json.loads((ROOT/'reports/pickup-oracle.json').read_text());data=json.loads((ROOT/'reference/pickup.json').read_text())
for name,path in [('trace_sha256','reference/pickup_oracle_events.txt'),('lua_sha256','tools/pickup_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[name]
meta=json.loads((ROOT/'reports/assets.json').read_text());defs=[next(d['id'] for d in meta['actor_definitions'] if d['bank']==4 and d['address']==pc) for pc in (0xb4af,0xb515)]
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','#include "pickup.h"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void setup(int definition){game=(Game){0};game.mode=PLAY;game.time=80;game.coins=123;game.p.x=game.p.y=1000*256;game.actors[0]=(Actor){.active=1,.def=definition,.x=128*256,.y=96*256};}
 int tick(int collect){game.sound_count=0;if(collect){game.p.x=120*256;game.p.y=88*256;}return pickup_step(0);}
 int sound_count(void){return game.sound_count;} int sound_at(int i){return game.sound_commands[i];}
 int active(void){return game.actors[0].active;} int persistent(void){return game.spawned[0];}
 int seconds(void){return game.time;} int coins(void){return game.coins;} int score(void){return game.score;}
''');(tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/s) for s in ('pickup.c','hazard.c','player_death.c','armor_break.c','animation.c','data.c')],str(tmp/'stubs.c'),'-o',str(tmp/'pickup.dylib')],check=True)
 lib=C.CDLL(str(tmp/'pickup.dylib'));items=targets=0
 for line in (ROOT/'reference/pickup_oracle_events.txt').read_text().splitlines():
  v=line.split('|')
  if v[0]=='ITEM':
   kind,tick=map(int,v[1:3]);a=bytes.fromhex(v[3]);time=bytes.fromhex(v[5])
   if tick==1:lib.setup(defs[kind-1])
   if lib.active():effect=lib.tick(tick==202)
   else:effect=0
   assert bool(lib.active())==bool(a[0]),(kind,tick,'active')
   bcd=lambda n:(n>>4)*10+(n&15)
   assert lib.seconds()==bcd(time[1])*60+bcd(time[0]),(kind,tick,'time')
   assert bool(lib.persistent())==bool(int(v[6],16)&2)
   assert lib.coins()==123 and lib.score()==0
   assert bool(effect)==(kind==2 and tick==202)
   items+=1
  elif v[0]=='SOUND':
   actual=bytes(lib.sound_at(i) for i in range(lib.sound_count()))
   assert actual==bytes.fromhex(v[3]),('pickup sound',v,actual)
  elif v[0]=='TARGET':
   size,contact,active,hp,layers=map(int,v[1:]);expected=contact in data['screen_contacts'].get(str(size),[])
   assert (active==64)==expected,(size,contact,active)
   assert layers==(1 if expected else 100)
   assert hp==(1 if expected and size==48 else 100)
   targets+=1
  elif v[0]=='COMPOUND':
   variant,phase,part=map(int,v[1:4]);a=bytes.fromhex(v[4])
   assert a[0]==64 and a[14]==1 and a[21]==(1 if phase==0 else 0),(variant,phase,part,a.hex())
 compiled=(C.c_uint8*len(meta['actor_definitions'])).in_dll(lib,'screen_attack_targets');contracts=load(Source())
 for d in meta['actor_definitions']:assert bool(compiled[d['id']])==bool(contracts[(d['bank'],d['address'])]['screen_attack_target'])
report={'passed':True,'item_ticks':items,'source_target_cases':targets,'compiled_actor_filters':len(compiled),'scope':'Both placed items including source sound output, time extension, no coin/score reward, retirement/persistence, and source small/medium/large target filters. Forced health/layer collapse and pending stacked-part death callbacks are also checked; unported enemy death effects and shared-pool contention remain gaps.'}
(ROOT/'reports/pickup-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
