#!/usr/bin/env python3
"""Deterministic headless Genesis Plus GX frontend; captures actual linked ROM output."""
import os
import argparse,ctypes as C,json,hashlib,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT.parent/'_capcom/black tiger/dist/reports/development/BT-PLAT-001/core_admission_work/source/Genesis-Plus-GX-f2b40ca6c97b2ff7f70d3c00d7ace84200bb31eb/genesis_plus_gx_libretro.dylib'
CORE=Path(os.environ.get('BLACKTIGER_CORE',str(CORE)))
class Info(C.Structure):_fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
class Runner:
 def __init__(self,path,core=CORE):
  self.lib=l=C.CDLL(str(core));self.frame=None;self.mask=0;self.pixel=2;self.frames=0;self.audio=0
  def env(cmd,p):
   if cmd==10:self.pixel=C.cast(p,C.POINTER(C.c_int))[0];return self.pixel in (0,1,2)
   if cmd==17:C.cast(p,C.POINTER(C.c_bool))[0]=False;return True
   if cmd==0x1002f:C.cast(p,C.POINTER(C.c_uint))[0]=3;return True
   return cmd in (8,11,16,18,35,37)
  def video(p,w,h,pitch):
   if not p:return
   raw=C.string_at(p,pitch*h)
   if self.pixel==1:
    a=np.frombuffer(raw,np.uint8).reshape(h,pitch)[:,:w*4].reshape(h,w,4);self.frame=a[:,:,[2,1,0]].copy()
   else:
    a=np.frombuffer(raw,np.uint16).reshape(h,pitch//2)[:,:w].astype(np.uint32)
    if self.pixel==2:r=(a>>11)*255//31;g=((a>>5)&63)*255//63
    else:r=((a>>10)&31)*255//31;g=((a>>5)&31)*255//31
    self.frame=np.stack([r,g,(a&31)*255//31],axis=2).astype(np.uint8)
  def audio(p,n):self.audio+=n;return n
  funcs=[('environment',C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p),env),('video_refresh',C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t),video),('audio_sample',C.CFUNCTYPE(None,C.c_int16,C.c_int16),lambda l,r:None),('audio_sample_batch',C.CFUNCTYPE(C.c_size_t,C.POINTER(C.c_int16),C.c_size_t),audio),('input_poll',C.CFUNCTYPE(None),lambda:None),('input_state',C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint),lambda p,d,i,b: int(p==0 and bool(self.mask&(1<<b))))]
  self.callbacks=[]
  for name,typ,fn in funcs:
   cb=typ(fn);self.callbacks.append(cb);f=getattr(l,'retro_set_'+name);f.argtypes=[typ];f(cb)
  l.retro_init();raw=path.read_bytes();self.buffer=C.create_string_buffer(raw);info=Info(str(path).encode(),C.cast(self.buffer,C.c_void_p),len(raw),None);l.retro_load_game.argtypes=[C.POINTER(Info)];l.retro_load_game.restype=C.c_bool;assert l.retro_load_game(C.byref(info))
  self.ram=(C.c_uint8*65536).in_dll(l,'work_ram');self.symbols={}
  for line in (ROOT/'out/release/symbol.txt').read_text().splitlines():
   v=line.split()
   if len(v)>=3:
    try:self.symbols[v[2]]=int(v[0],16)
    except ValueError:pass
  # GCC LTO may promote file-local storage and suffix its debug symbol. Alias
  # only unambiguous names so RAM fixtures remain independent of optimizer naming.
  aliases={}
  for name,address in self.symbols.items():
   if '.lto_priv.' in name:aliases.setdefault(name.split('.lto_priv.')[0],[]).append(address)
  for name,addresses in aliases.items():
   if len(addresses)==1:self.symbols.setdefault(name,addresses[0])
 def run(self,n,mask=0):
  self.mask=mask
  for _ in range(n):self.lib.retro_run();self.frames+=1
 def read(self,name,n=2):
  a=self.symbols[name]&65535;return bytes(self.ram[(a+i)^1] for i in range(n))
 def write(self,name,offset,data):
  a=(self.symbols[name]+offset)&65535
  for i,v in enumerate(data):self.ram[(a+i)^1]=v
 def capture(self,name):
  assert self.frame is not None;Image.fromarray(self.frame).save(ROOT/'reports'/name)
 def close(self):self.lib.retro_unload_game();self.lib.retro_deinit()

def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=ROOT/'out/release/rom.bin');p.add_argument('--core',type=Path,default=CORE);a=p.parse_args();r=Runner(a.rom,a.core);r.run(120);r.capture('title.png');r.run(2,1<<3);r.run(120);r.capture('start.png');r.run(120,(1<<7)|(1<<1));r.capture('walk.png');r.run(30,(1<<7)|(1<<0)|(1<<1));r.capture('jump.png');print(json.dumps({'frames':r.frames,'audio_samples':r.audio,'sha256':hashlib.sha256(a.rom.read_bytes()).hexdigest(),'game_hex':r.read('game',64).hex(),'cache_faults':r.read('video_cache_faults').hex(),'dma_bytes_last_frame':r.read('video_dma_bytes').hex()},indent=2));r.close()
if __name__=='__main__':main()
