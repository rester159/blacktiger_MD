"""Actual native generator/controller: deterministic layouts and traversable spines."""
import ctypes as C, hashlib, json, subprocess, tempfile, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_dungeon_chunks import Motion
ref=json.loads((ROOT/'reference/dungeon_chunks.json').read_text())
assert ref['controller_sha256']==hashlib.sha256((ROOT/'src/player_motion.c').read_bytes()).hexdigest()
chunks=ref['chunks'];n=len(chunks)
source=(ROOT/'src/dungeon.c').read_text();rng=source[source.index('u32 dungeon_rng'):source.index('u16 dungeon_seconds')]
stub='''#include "dungeon.h"
#include "dungeon_layout.h"
#include "player_motion.h"
Dungeon dungeon;static u8 collision[8][8192];static u16 maps[8][32768];
const Round rounds[8]={'''+','.join('{.width='+str(1024 if r==2 else 2048)+',.height='+str(2048 if r==2 else 1024)+',.collision=collision['+str(r)+'],.map=maps['+str(r)+']}' for r in range(8))+'''};
'''+rng+'''
void load(int r,const u8 *c,const u16 *m){for(int i=0;i<8192;i++)collision[r][i]=c[i];for(int i=0;i<32768;i++)maps[r][i]=m[i];}
void seed(u32 s){dungeon_seed(s);}
void stage(int s){dungeon.stage=s;dungeon_generate();}
u8 terrain(s16 x,s16 y){return dungeon_terrain(x,y);}
static PlayerMotion p;
void begin(void){p=(PlayerMotion){.scroll_x=(u16)-128,.scroll_y=528,.screen_x=128,.screen_y=144};}
int walk(const u8 *inputs,int n){for(int i=0;i<n;i++)player_motion_step(&p,inputs[i],0);return (s16)(p.scroll_x+p.screen_x);}
int ypos(void){return (s16)(p.scroll_y+p.screen_y);}
'''
class Layout(C.Structure):
 _fields_=[('ready',C.c_uint8),('count',C.c_uint8),('source',C.c_uint8),('ids',C.c_uint8*10),('exit',C.c_uint16)]
with tempfile.TemporaryDirectory() as t:
 t=Path(t);(t/'stub.c').write_text(stub)
 subprocess.run(['cc','-O2','-shared','-fPIC','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/dungeon_layout.c'),str(ROOT/'src/player_motion.c'),str(t/'stub.c'),'-o',str(t/'generation.dylib')],check=True)
 lib=C.CDLL(str(t/'generation.dylib'));lib.load.argtypes=[C.c_int,C.c_void_p,C.c_void_p];lib.walk.argtypes=[C.c_char_p,C.c_int]
 for r in range(8):
  raw=(ROOT/f'res/generated/map{r}.bin').read_bytes();words=(C.c_uint16*32768)(*[int.from_bytes(raw[i:i+2],'big') for i in range(0,len(raw),2)])
  lib.load(r,(ROOT/f'res/generated/collision{r}.bin').read_bytes(),words)
 unique=set();fingerprints=[];checked=0
 # 10,000 seeded runs x all sixteen stages; controller replay on 128 runs.
 for seed in range(10000):
  lib.seed(seed+1)
  for stage in range(1,17):
   lib.stage(stage);d=Layout.in_dll(lib,'dungeon_layout');ids=list(d.ids[:d.count]);signature=(d.source,*ids)
   assert d.count==(6,7,8,10)[(stage-1)//4]
   assert all(chunks[i]['round']==d.source for i in ids)
   assert all(ref['pair_ok'][(a*n+b)//8]>>(a*n+b)%8&1 for a,b in zip(ids,ids[1:]))
   assert all(a!=b for a,b in zip(ids,ids[1:]))
   if stage==1:unique.add(signature)
   if seed<128:
    lib.begin()
    for k,i in enumerate(ids):
     path=bytes(chunks[i]['path']);x=lib.walk(path,len(path));y=lib.ypos()
     # At final boundary the port's terrain intentionally closes the world.
     assert (x==(k+1)*256 or k==len(ids)-1 and x>=d.exit) and y==672,(seed,stage,k,i,x,y)
    checked+=1
   if seed<2:fingerprints.append(signature)
 assert len(unique)>9900,len(unique)
 lib.seed(1)
 for stage in range(1,17):
  lib.stage(stage);d=Layout.in_dll(lib,'dungeon_layout');assert (d.source,*d.ids[:d.count])==fingerprints[stage-1]
report=dict(passed=True,source_chunks=n,pair_replays=ref['pair_checks'],seeded_runs=10000,stages_checked=160000,controller_routes=checked,distinct_first_stages=len(unique),scope=__doc__,limitations='Horizontal spines only; vertical branches, locked doors, full spawn threat budgets and special bosses remain unimplemented.')
(ROOT/'reports/dungeon-generation-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
