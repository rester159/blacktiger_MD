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
class Geometry(C.Structure):_fields_=[('base_width',C.c_uint),('base_height',C.c_uint),('max_width',C.c_uint),('max_height',C.c_uint),('aspect_ratio',C.c_float)]
class Timing(C.Structure):_fields_=[('fps',C.c_double),('sample_rate',C.c_double)]
class AVInfo(C.Structure):_fields_=[('geometry',Geometry),('timing',Timing)]
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
  def audio(p,n):
   self.audio+=n
   if getattr(self,'audio_capture',None) is not None:self.audio_capture.append(C.string_at(p,n*4))
   return n
  funcs=[('environment',C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p),env),('video_refresh',C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t),video),('audio_sample',C.CFUNCTYPE(None,C.c_int16,C.c_int16),lambda l,r:None),('audio_sample_batch',C.CFUNCTYPE(C.c_size_t,C.POINTER(C.c_int16),C.c_size_t),audio),('input_poll',C.CFUNCTYPE(None),lambda:None),('input_state',C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint),lambda p,d,i,b: int(p==0 and bool(self.mask&(1<<b))))]
  self.callbacks=[]
  for name,typ,fn in funcs:
   cb=typ(fn);self.callbacks.append(cb);f=getattr(l,'retro_set_'+name);f.argtypes=[typ];f(cb)
  l.retro_init();raw=path.read_bytes();self.buffer=C.create_string_buffer(raw);info=Info(str(path).encode(),C.cast(self.buffer,C.c_void_p),len(raw),None);l.retro_load_game.argtypes=[C.POINTER(Info)];l.retro_load_game.restype=C.c_bool;assert l.retro_load_game(C.byref(info))
  l.retro_set_controller_port_device(0,513) # Six-button pad: libretro Select is Genesis Mode.
  av=AVInfo();l.retro_get_system_av_info.argtypes=[C.POINTER(AVInfo)];l.retro_get_system_av_info(C.byref(av));self.sample_rate=av.timing.sample_rate
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
 def start_game(self,frames=3):
  if "frontend" in self.symbols:
   self.run(3,32);self.run(2);self.run(3,8);self.run(2)
  self.run(frames,8)
  if "intro_tick" in self.symbols:
   for _ in range(1000):
    if int.from_bytes(self.read("intro_tick"),"big")>=842:break
    self.run(1)
   else:raise AssertionError("Intro did not finish")
   self.run(max(0,frames-1))
 def read(self,name,n=2):
  a=self.symbols[name]&65535;return bytes(self.ram[(a+i)^1] for i in range(n))
 def write(self,name,offset,data):
  # Raw diagnostic pool edits must invalidate the native occupancy cache just
  # as the public allocation routines do. A conservative positive is enough:
  # the next normal update rebuilds it, including for an all-zero injection.
  pool_flags={'missiles':('missiles_occupied',0),'skeletons':('skeleton_weapons_occupied',0),
   'statue_shells':('shell_pools_occupied',0),'statue_blasts':('shell_pools_occupied',0),
   'hunter_shells':('shell_pools_occupied',1),'hunter_blasts':('shell_pools_occupied',1),
   'container_traps':('container_traps_occupied',0),'waveboss_seeds':('waveboss_seeds_occupied',0),
   'flailer_weapons':('flailer_weapons_occupied',0),'reinforcement_shots':('reinforcement_shots_occupied',0),
   'edge_shots':('edge_shots_occupied',0),'dragon_shots':('dragon_shots_occupied',0)}
  if name in pool_flags:
   flag,index=pool_flags[name]
   if flag in self.symbols:self.write(flag,index,b'\x01')
  a=(self.symbols[name]+offset)&65535
  for i,v in enumerate(data):self.ram[(a+i)^1]=v
 def capture(self,name):
  assert self.frame is not None;Image.fromarray(self.frame).save(ROOT/'reports'/name)
 def close(self):self.lib.retro_unload_game();self.lib.retro_deinit()

def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=ROOT/'out/release/rom.bin');p.add_argument('--core',type=Path,default=CORE);a=p.parse_args();r=Runner(a.rom,a.core);r.run(120);r.capture('title.png');r.start_game(2);r.run(120);r.capture('start.png');r.run(120,(1<<7)|(1<<1));r.capture('walk.png');r.run(30,(1<<7)|(1<<0)|(1<<1));r.capture('jump.png');print(json.dumps({'frames':r.frames,'audio_samples':r.audio,'sha256':hashlib.sha256(a.rom.read_bytes()).hexdigest(),'game_hex':r.read('game',64).hex(),'cache_faults':r.read('video_cache_faults').hex(),'dma_bytes_last_frame':r.read('video_dma_bytes').hex()},indent=2));r.close()
if __name__=='__main__':main()
