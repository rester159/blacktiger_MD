#!/usr/bin/env python3
"""Compile production sparse-terrain C and check every unaffected/replaced map cell."""
import ctypes as C,json,subprocess,tempfile,re,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
open_collision=Source().read(4,0xb63a,1)[0]
contract=json.loads((ROOT/'reference/hidden.json').read_text())
oracle=json.loads((ROOT/'reports/hidden-oracle.json').read_text())
assert hashlib.sha256((ROOT/'reference/hidden_oracle_events.txt').read_bytes()).hexdigest()==oracle['trace_sha256']
assert hashlib.sha256((ROOT/'tools/hidden_oracle.lua').read_bytes()).hexdigest()==oracle['lua_sha256']
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp);(tmp/'genesis.h').write_text('/* Host-only SGDK include stub; game.h supplies fixed-width types. */\n')
 resources=re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M)
 decl=(ROOT/'inc/assets.h').read_text();stubs=['#include "assets.h"','#include "world.h"','Game game;','u16 bonus_word(u16 x,u16 y,u16 original){return original;}']
 for name in resources:
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''void convert(u8 level,u8 mask,const u16 *map,const u8 *col,u16 *out,u8 *collision) {
 game.round=level;world_reset();world_opened=mask;
 u16 w=rounds[level].width>>3,h=rounds[level].height>>3;
 for(u16 y=0;y<h;y++) for(u16 x=0;x<w;x++) out[y*w+x]=world_word(x,y,map[y*w+x]);
 for(u16 i=0;i<8192;i++) collision[i]=world_collision(i,col[i]);
}''')
 (tmp/'stubs.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/world.c'),str(ROOT/'src/progress.c'),str(ROOT/'src/animation.c'),str(ROOT/'src/data.c'),str(tmp/'stubs.c'),'-o',str(tmp/'world.dylib')],check=True)
 lib=C.CDLL(str(tmp/'world.dylib'));cases=0
 for level,patches in enumerate(contract['rounds']):
  w=128 if level==2 else 256;h=256 if level==2 else 128
  raw=(ROOT/f'res/generated/map{level}.bin').read_bytes();values=[int.from_bytes(raw[i:i+2],'big') for i in range(0,len(raw),2)]
  col=(ROOT/f'res/generated/collision{level}.bin').read_bytes()
  source=(C.c_uint16*len(values))(*values);collision=(C.c_uint8*8192).from_buffer_copy(col);out=(C.c_uint16*len(values))();cout=(C.c_uint8*8192)()
  line=re.search(r'const u16 open_tile'+str(level)+r'\[\]=\{([^}]+)\}',(ROOT/'src/data.c').read_text())[1];opened=list(map(int,line.split(',')))
  for mask in [0,*[1<<i for i in range(len(patches))],(1<<len(patches))-1]:
   lib.convert(level,mask,source,collision,out,cout);expected=values.copy();ecol=bytearray(col)
   for i,p in enumerate(patches):
    if mask&(1<<i):
     for dy in range(4):
      for dx in range(2):expected[(p['y']//8+dy)*w+p['x']//8+dx]=opened[(dy%2)*2+dx]
     ecol[p['cell']]=open_collision;ecol[p['cell']+w//2]=open_collision
   assert list(out)==expected,(level,mask,'map mutation outside patch')
   assert bytes(cout)==ecol,(level,mask,'collision mutation outside patch')
   cases+=1
report={'passed':True,'map_and_collision_states':cases,'source_patch_cases':oracle['patch_cases'],'source_reward_cases':oracle['reward_cases'],'scope':'Production C sparse terrain: exact changed cells and all unchanged cells, each patch separately and combined.'}
(ROOT/'reports/world-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
