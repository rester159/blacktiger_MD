#!/usr/bin/env python3
"""Native stream timing and looping under regular and missed display frames."""
import ctypes as C,json,subprocess,tempfile,sys
from pathlib import Path
from fractions import Fraction
assert abs(Fraction(308939,61461)-Fraction(3579545*3420*313,14328*53203424))<Fraction(1,10**9)
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from extract_music import convert
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'stub.c').write_text('''#include "music.h"
 unsigned int events[8192],count;
 void music_write(u8 p,u8 r,u8 v){events[count++]=((u32)p<<16)|((u16)r<<8)|v;}
 void clear(void){count=0;}
 ''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/music.c'),str(tmp/'stub.c'),'-o',str(tmp/'music.dylib')],check=True)
 lib=C.CDLL(str(tmp/'music.dylib'));buf=(C.c_uint32*8192).in_dll(lib,'events');count=C.c_uint32.in_dll(lib,'count');tick=C.c_uint16.in_dll(lib,'music_tick');checks=0
 def output():return list(buf[:count.value])
 for round in range(8):
  raw,m=convert(0x21+round);events={};pos=0
  while pos<len(raw):
   t=int.from_bytes(raw[pos:pos+2],'big');n=raw[pos+2];pos+=3;events[t]=[int.from_bytes(raw[pos+3*i:pos+3*i+3],'big') for i in range(n)];pos+=3*n
  for pal in (0,1):
   lib.clear();lib.music_start(round)
   assert output()==[0x2800|c for c in (0,1,2,4,5,6)]+[(p<<16)|((0xb4+c)<<8)|0xc0 for p in range(2) for c in range(3)]+events.get(0,[])
   t=0;fraction=0;total=0;frame=0;denom=61461 if pal else 1791
   while total<m['end_tick']+(m['end_tick']-m['loop_tick'])*2:
    advance=(1,1,2,1,3)[frame%5];frame+=1;expect=[]
    for _ in range(advance):
     fraction+=308939 if pal else 7467
     while fraction>=denom:
      fraction-=denom;t+=1;total+=1
      if t==m['end_tick']:t=m['loop_tick']
      expect+=events.get(t,[])
    lib.clear();lib.music_advance(advance,pal)
    assert output()==expect and tick.value==t,(round,pal,frame,t,tick.value)
    checks+=1
   lib.music_stop();lib.clear();lib.music_advance(10,pal);assert not output()
 report=dict(passed=True,tracks=8,clock_loop_checks=checks,source_data_bytes=sum(convert(c)[1]['bytes'] for c in range(0x21,0x29)),scope='Native register sequencing, intro plus two loop wraps, all eight tracks, NTSC/PAL clocks and missed-frame batches. Does not prove timbral equivalence of different sound chips.')
 (ROOT/'reports/music-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
