#!/usr/bin/env python3
"""Fast boolean animation advancement must match the full native interpreter."""
import json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
code=r'''
#include <string.h>
#include <stdio.h>
#include "animation.h"
static unsigned seed=821;
static unsigned random_word(void){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
int main(void){
 AnimFrame frames[16];unsigned trial,i,ticks=0;
 for(trial=0;trial<20000;trial++){
  AnimState a={0},b;AnimClip clip={frames,random_word()%17,random_word()%21};
  const AnimClip *p=(trial%13)?&clip:0;
  if(trial&1)clip.loop=ANIM_NO_LOOP;
  for(i=0;i<16;i++)frames[i]=(AnimFrame){i,random_word()%5,0,0,random_word()%4,(s8)random_word(),(s8)random_word()};
  a.frame=random_word()%20;a.remaining=random_word()%258;a.vx=random_word();a.vy=random_word();a.finished=!(trial%11);b=a;
  for(i=0;i<300;i++,ticks++){
   u8 expected=animation_tick(&a,p)!=0,actual=animation_step(&b,p);
   if(expected!=actual || memcmp(&a,&b,sizeof a)){
    fprintf(stderr,"animation mismatch trial %u tick %u\n",trial,i);return 1;
   }
  }
 }
 printf("%u animation step comparisons passed\n",ticks);return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    c=Path(directory)/'animation.c';binary=Path(directory)/'animation';c.write_text(code)
    subprocess.run(['cc','-DHOST_TEST','-O2','-fsanitize=address,undefined','-I'+str(ROOT/'inc'),str(c),str(ROOT/'src/animation.c'),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
report=dict(passed=True,tick_comparisons=6000000,scope=__doc__+' Includes zero-duration frames, loops, holds, null/empty clips, finished and invalid frame states; address/undefined-behavior sanitizers enabled.')
(ROOT/'reports/animation-step-tests.json').write_text(json.dumps(report,indent=2)+'\n')
