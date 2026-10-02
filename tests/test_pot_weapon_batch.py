"""Pot weapon batching retains scalar collision semantics."""
from pathlib import Path
import tempfile,subprocess,ctypes as C,json
root=Path(__file__).resolve().parents[1];candidate=(root/'src/pots.c').read_text();original=(root/'tests/reference/pot_weapon_scalar.c').read_text()
ca=candidate.index('void pots_prepare_weapons(');cb=candidate.index('const AnimFrame *pot_frame',ca)
code='''#include <string.h>
#include "pots.h"
Game game;Pot pots[MAX_POTS];u8 pots_end;
const u8 dagger_width=4,dagger_height=2;
static Pot *weapon_pots[MAX_POTS];static u8 weapon_pot_count;
'''+original+candidate[ca:cb]+'''
static unsigned rng;
static unsigned next(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
int compare(unsigned seed){
 Pot saved[MAX_POTS],expected[MAX_POTS];s16 xs[17],ys[17];u8 daggers[17];unsigned i,reference=0,actual=0;
 rng=seed+1;memset(&game,0,sizeof(game));game.frame=next()&1;game.cam_x=next();game.cam_y=next();pots_end=next()%34;
 for(i=0;i<MAX_POTS;i++){
  pots[i]=(Pot){0};pots[i].active=next()&1;pots[i].phase=next()%3;pots[i].pending=next()%4==0;
  pots[i].x=game.cam_x+(int)(next()%400)-64;pots[i].y=game.cam_y+(int)(next()%400)-64;
 }
 for(i=0;i<17;i++){xs[i]=game.cam_x+(int)(next()%400)-64;ys[i]=game.cam_y+(int)(next()%400)-64;daggers[i]=i>=7;}
 memcpy(saved,pots,sizeof(pots));
 for(i=0;i<17;i++)reference=reference*33+reference_weapon(xs[i],ys[i],daggers[i]);
 memcpy(expected,pots,sizeof(pots));memcpy(pots,saved,sizeof(pots));pots_prepare_weapons();
 for(i=0;i<17;i++)actual=actual*33+pots_weapon(xs[i],ys[i],daggers[i]);
 return reference==actual && !memcmp(pots,expected,sizeof(pots));
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'genesis.h').write_text('');(p/'t.c').write_text(code)
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+td,'-I'+str(root/'inc'),str(p/'t.c'),'-o',str(p/'t.dylib')],check=True)
 lib=C.CDLL(str(p/'t.dylib'))
 for seed in range(100000):assert lib.compare(seed),seed
report=dict(passed=True,batches=100000,scope='Production pot candidate list versus scalar slot scan: wrapped coordinates, both frame parities, hit order, pending flags, inactive and open pots.')
(root/'reports/pot-weapon-batch-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
