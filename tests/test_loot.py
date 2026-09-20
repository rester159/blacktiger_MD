#!/usr/bin/env python3
"""Production native loot C versus original-ROM selection, movement, rewards and RNG."""
import ctypes as C,json,subprocess,tempfile,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reports/loot-oracle.json').read_text());data=json.loads((ROOT/'reference/loot.json').read_text())
assert hashlib.sha256((ROOT/'reference/loot_oracle_events.txt').read_bytes()).hexdigest()==ref['trace_sha256']
assert hashlib.sha256((ROOT/'tools/loot_oracle.lua').read_bytes()).hexdigest()==ref['lua_sha256']
class Anim(C.Structure):_fields_=[('frame',C.c_uint16),('remaining',C.c_uint16),('vx',C.c_int8),('vy',C.c_int8),('finished',C.c_uint8)]
class Loot(C.Structure):_fields_=[('x',C.c_int16),('y',C.c_int16),('animation',Anim),('active',C.c_uint8),('kind',C.c_uint8)]
with tempfile.TemporaryDirectory() as temp:
 tmp=Path(temp);(tmp/'genesis.h').write_text('/* Host types from game.h. */\n');decl=(ROOT/'inc/assets.h').read_text()
 stubs=['#include "assets.h"','#include "loot.h"','Game game;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''int setup(int category,int sample) {loot_new();game.p.x=game.p.y=1000*256;game.coins=123;return loot_spawn(category,sample,80,80);}
 int collect(void) {game.p.x=80*256;game.p.y=72*256;loot_tick();return game.coins;}
 int graphic(void) {const AnimFrame *f=loot_frame(0);return f?f->code:-1;}
''');(tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/loot.c'),str(ROOT/'src/animation.c'),str(ROOT/'src/data.c'),str(tmp/'stubs.c'),'-o',str(tmp/'loot.dylib')],check=True)
 lib=C.CDLL(str(tmp/'loot.dylib'));pool=(Loot*33).in_dll(lib,'loot');rng=C.c_uint16.in_dll(lib,'loot_random');counts={}
 for line in (ROOT/'reference/loot_oracle_events.txt').read_text().splitlines():
  v=line.split('|');counts[v[0]]=counts.get(v[0],0)+1
  if v[0]=='DROP':
   lib.setup(int(v[1]),int(v[2]));a=bytes.fromhex(v[3]);l=pool[0]
   assert bool(l.active)==bool(a[0])
   if l.active:assert (l.x,l.y,l.kind)==(int.from_bytes(a[1:3],'big'),int.from_bytes(a[3:5],'big'),a[13]-3)
  elif v[0]=='FRAME':
   kind,tick=int(v[1]),int(v[2]);a=bytes.fromhex(v[3]);display=bytes.fromhex(v[4])
   if tick==1:lib.setup(*ref['cases'][kind-1])
   lib.loot_tick();l=pool[0];assert bool(l.active)==bool(a[0]),(kind,tick,'active')
   if l.active:
    signed=lambda n:n if n<128 else n-256
    expected=(int.from_bytes(a[1:3],'big'),int.from_bytes(a[3:5],'big'),signed(a[6]),signed(a[7]),a[10])
    assert (l.x,l.y,l.animation.vx,l.animation.vy,l.animation.remaining)==expected,(kind,tick)
    assert lib.graphic()==display[0]|((display[1]&224)<<3)
  elif v[0]=='COINS':
   kind=int(v[1]);lib.setup(*ref['cases'][kind-1]);assert lib.collect()==int.from_bytes(bytes.fromhex(v[2]),'little')
   assert pool[0].active==2;lib.loot_tick();assert pool[0].active==0;assert lib.collect()==123+data['kinds'][kind-1]['coins']
  elif v[0]=='FULL':
   lib.loot_reset()
   for _ in range(33):assert lib.loot_spawn(1,0,80,80)==1
   assert lib.loot_spawn(1,0,80,80)==0
  elif v[0]=='RNG':
   if int(v[2])==1:rng.value=int(v[1])
   lib.loot_random_tick();assert rng.value==int.from_bytes(bytes.fromhex(v[3]),'little')
report={'passed':True,'original_drop_selections':counts['DROP'],'animation_ticks':counts['FRAME'],'coin_rewards':counts['COINS'],'rng_steps':counts['RNG'],'full_pool_refusal':True,'scope':ref['scope']}
(ROOT/'reports/loot-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
