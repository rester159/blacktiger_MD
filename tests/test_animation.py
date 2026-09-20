#!/usr/bin/env python3
"""Compare the production native animation routine to original-ROM execution traces."""
import ctypes as C,subprocess,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from extract_animation import compile_clip
class Frame(C.Structure):_fields_=[('code',C.c_uint16),('duration',C.c_uint8),('palette',C.c_uint8),('flip',C.c_uint8),('hold',C.c_uint8),('vx',C.c_int8),('vy',C.c_int8)]
class Clip(C.Structure):_fields_=[('frames',C.POINTER(Frame)),('count',C.c_uint16),('loop',C.c_uint16)]
class State(C.Structure):_fields_=[('frame',C.c_uint16),('remaining',C.c_uint16),('vx',C.c_int8),('vy',C.c_int8),('finished',C.c_uint8)]
def signed(x):return x if x<128 else x-256

def main():
 build=ROOT/'out/host';build.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-DHOST_TEST','-I'+str(ROOT/'inc'),'-shared','-fPIC',str(ROOT/'src/animation.c'),'-o',str(build/'animation.dylib')],check=True)
 lib=C.CDLL(str(build/'animation.dylib'));lib.animation_reset.argtypes=[C.POINTER(State)];lib.animation_tick.argtypes=[C.POINTER(State),C.POINTER(Clip)];lib.animation_tick.restype=C.POINTER(Frame)
 oracle=(ROOT/'reference/npc_oracle_events.txt').read_bytes();report=json.loads((ROOT/'reports/npc-oracle.json').read_text());assert hashlib.sha256(oracle).hexdigest()==report['event_sha256']
 lines=[s.split('|') for s in oracle.decode().splitlines()];checked=0
 for entry in ('2fe7','32c7'):
  rows=(Frame*3)(Frame(0x220,2,5,0,0,1,2),Frame(0x222,3,5,1,3,0,0),Frame(0x224,1,5,0,2,-1,0));clip=Clip(rows,3,0);state=State();lib.animation_reset(C.byref(state))
  for v in lines:
   if v[:2]!=['FRAME',entry]:continue
   a=bytes.fromhex(v[3]);display=bytes.fromhex(v[4]);f=lib.animation_tick(C.byref(state),C.byref(clip)).contents
   code=display[0]+((display[1]&224)<<3)
   if entry=='32c7' and display[1]&8:code-=1
   assert (f.code,f.palette,f.flip)==(code,display[1]&7,bool(display[1]&8))
   assert (state.remaining,state.vx,state.vy)==(a[10],signed(a[6]),signed(a[7]));checked+=1
 # Full 402-tick idle loop, compare every sampled original execution snapshot.
 row=(Frame*1)(Frame(0x300,200,4,0,0,0,0));clip=Clip(row,1,0);state=State();lib.animation_reset(C.byref(state));samples={int(v[1]):v for v in lines if v[0]=='IDLE'}
 for tick in range(1,403):
  f=lib.animation_tick(C.byref(state),C.byref(clip)).contents
  if tick in samples:
   a=bytes.fromhex(samples[tick][2]);assert state.remaining==a[10];assert f.code==0x300 and f.palette==4;checked+=1
 # Retire happens on the tick following the final visible frame.
 row=(Frame*1)(Frame(0x304,100,4,0,0,0,0));clip=Clip(row,1,65535);lib.animation_reset(C.byref(state))
 for _ in range(100):assert lib.animation_tick(C.byref(state),C.byref(clip))
 assert not lib.animation_tick(C.byref(state),C.byref(clip)) and state.finished
 # Negative control: common misreading of vx=80 preserves X but incorrectly writes Y.
 bad=(Frame*3)(Frame(0x220,2,5,0,0,1,2),Frame(0x222,3,5,1,1,0,9),Frame(0x224,1,5,0,2,-1,0));clip=Clip(bad,3,0);lib.animation_reset(C.byref(state))
 for _ in range(3):lib.animation_tick(C.byref(state),C.byref(clip))
 assert state.vy==9 and state.vy!=2
 # Compiler must stop at a behavior callback rather than decode its address as a frame.
 class Fixture:
  data=bytes([2,0x20,0x45,1,2,0,0x56,0x94])
  def read(self,b,p,n):return self.data[p:p+n]
  def word(self,b,p):return int.from_bytes(self.read(b,p,2),'little')
 c=compile_clip(Fixture(),0,0);assert len(c['frames'])==1 and c['terminal']=='event' and c['event']['address']==0x9456
 result={'passed':True,'original_trace_comparisons':checked,'checks':['small and medium source frame/flip/velocity/loop agreement','402-tick native NPC loop','100-tick release then retirement','wrong velocity-hold negative rejected','source callback boundary stays out of native data'],'oracle_sha256':hashlib.sha256(oracle).hexdigest()}
 (ROOT/'reports/animation-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
