#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/shop_oracle.json').read_text());data=json.loads((ROOT/'reference/shop.json').read_text())
for key,path in [('trace_sha256','reference/shop_oracle_events.txt'),('lua_sha256','tools/shop_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
class Inventory(C.Structure):
 _fields_=[('coins',C.c_uint16),('invincible',C.c_uint16)]+[(k,C.c_uint8) for k in ('weapon','armor','keys','antidotes','poison')]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 (tmp/'stub.c').write_text('#include "assets.h"\n#include "frontend.h"\nFrontend frontend;Game game;u8 container_keys;\nconst u8 shop_default_difficulty=4;\nconst u16 shop_prices[2][8][4]='+str(data['prices']).replace('[','{').replace(']','}')+';\nconst u16 shop_key_price=30,shop_antidote_price=150;\n'+'''#include "shop.h"
void buy(int item,int difficulty,int coins,int weapon,int armor,int keys,int antidotes,int poison) {
 game=(Game){0};game.coins=coins;game.p.weapon=weapon+1;game.p.armor=armor;game.p.invincible=1;
 container_keys=keys;shop_antidotes=antidotes;shop_poison=poison;shop_difficulty=difficulty;shop_buy(item);
}
int sound_count(void){return game.sound_count;} int sound_at(int i){return game.sound_commands[i];}
''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/shop.c'),str(ROOT/'src/status.c'),str(tmp/'stub.c'),'-o',str(tmp/'s.dylib')],check=True)
 lib=C.CDLL(str(tmp/'s.dylib'));lib.shop_purchase.argtypes=[C.c_uint8,C.c_uint8,C.POINTER(Inventory)];lib.shop_purchase.restype=C.c_uint8;count=0
 for line in (ROOT/'reference/shop_oracle_events.txt').read_text().splitlines():
  if line=='COMPLETE':break
  if line.startswith('CONFIG|'):continue
  if line.startswith('SOUND|'):
   _,case,raw=line.split('|');c=ref['cases'][int(case)]
   lib.buy(*[c[k] for k in ('item','difficulty','coins','weapon','armor','keys','antidotes','poison')])
   assert bytes(lib.sound_at(i) for i in range(lib.sound_count()))==bytes.fromhex(raw),(c,'sound',raw)
   continue
  _,case,*values=line.split('|');c=ref['cases'][int(case)];expected=list(map(int,values))
  s=Inventory(coins=c['coins'],invincible=1,**{k:c[k] for k in ('weapon','armor','keys','antidotes','poison')})
  ok=lib.shop_purchase(c['item'],c['difficulty'],C.byref(s))
  assert [ok,s.coins,s.weapon,s.armor,s.keys,s.antidotes,s.poison,s.invincible]==expected,(c,expected)
  count+=1
 report={'passed':True,'source_purchase_cases':count,'default_difficulty':ref['default_difficulty'],'scope':'All ten goods and eight difficulty price schedules; funds threshold, owned equipment refusal, caps, antidote storage/cure. Successful purchase and refusal sound output match the original command queue. Source presentation/tasks are bypassed. Native poison onset and countdown remain unported.'}
 (ROOT/'reports/shop-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
