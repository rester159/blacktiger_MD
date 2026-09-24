#!/usr/bin/env python3
"""Differentially check optimized strip walkers against scalar v23 pinning."""
import json, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def function(source, name):
    start=source.index(name+'(');start=source.rfind('\n',0,start)+1
    end=source.index('{',start)+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]

source=(ROOT/'src/video.c').read_text()
code=r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;typedef uint16_t u16;typedef int16_t s16;
static u16 visible[1800],visible_words[2048],terrain_width,terrain_height,terrain_shift;
static u16 map_data[32768],remap0[2048],remap1[2048];
static const u16 *terrain_map=map_data;
static u8 world_opened,world_rows[256],bonus_rows[128];
static struct {const u16 *remap0,*remap1;} backdrop={remap0,remap1},*terrain_backdrop;
static u8 wrap_y;
#define WORLD_WRAP_Y wrap_y
static unsigned rng=521;
static unsigned random_word(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
/* Distinct dynamic results test both coordinates and conditional resolution. */
static u16 world_word(u16 x,u16 y,u16 word){return (word&0xf800)|(16+(x*7+y*11+(word&2047))%1800);}
'''
for name in ('backdrop_word','dynamic_word','pin_column','pin_row'):
    code+=function(source,name)+'\n'
code+=r'''
static void scalar_pin(s16 x,s16 y,s16 delta){
 u16 at=((y&31)<<6)|(x&63),word,v;
 if(delta>0){
  if(wrap_y)y=(u16)y&(terrain_height-1);
  if((u16)y>=terrain_height)word=0;
  else {
   u16 mx=(u16)x&(terrain_width-1);
   word=terrain_map[((u16)y<<terrain_shift)+mx];
   if((world_opened&world_rows[y]) || bonus_rows[y>>1])word=world_word(mx,y,word);
   word=backdrop_word(word);
  }
  visible_words[at]=word;
 }else word=visible_words[at];
 v=word&2047;if(v>=16 && v<1816)visible[v-16]+=delta;
}
int main(void){
 unsigned trial,i;static u16 initial[2048],expected_words[2048],expected_counts[1800];
 for(i=0;i<32768;i++)map_data[i]=(random_word()&0xf800)|(random_word()%1816);
 for(i=0;i<2048;i++){remap0[i]=random_word()%1816;remap1[i]=random_word()%1816;}
 for(i=0;i<256;i++)world_rows[i]=random_word()&7;
 for(i=0;i<128;i++)bonus_rows[i]=(random_word()&3)==0;
 for(trial=0;trial<20000;trial++){
  s16 x=(s16)(random_word()%8192)-4096,y,delta=(trial&1)?1:-1;
  u8 column=trial&2;
  terrain_width=(trial&4)?256:128;terrain_height=32768/terrain_width;
  terrain_shift=(trial&4)?8:7;wrap_y=(trial&16)!=0;
  terrain_backdrop=(trial&8)?&backdrop:0;world_opened=random_word()&7;
  y=(s16)(random_word()%(terrain_height+80))-40;
  for(i=0;i<2048;i++)initial[i]=(random_word()&0xf800)|(random_word()%2048);
  memcpy(visible_words,initial,sizeof initial);memset(visible,0,sizeof visible);
  for(i=0;i<(column?29:33);i++)scalar_pin(x+(column?0:i),y+(column?i:0),delta);
  memcpy(expected_words,visible_words,sizeof expected_words);memcpy(expected_counts,visible,sizeof expected_counts);
  memcpy(visible_words,initial,sizeof initial);memset(visible,0,sizeof visible);
  if(column)pin_column(x,y,delta);else pin_row(x,y,delta);
  if(memcmp(expected_words,visible_words,sizeof expected_words) || memcmp(expected_counts,visible,sizeof expected_counts)){
   fprintf(stderr,"strip mismatch trial %u x %d y %d delta %d column %d\n",trial,x,y,delta,column);return 1;
  }
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    c=Path(directory)/'strips.c';binary=Path(directory)/'strips';c.write_text(code)
    subprocess.run(['cc','-O2','-fsanitize=undefined,address',str(c),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
report=dict(passed=True,cases=20000,scope='Actual C row/column walkers versus scalar v23 pinning: ring and horizontal/vertical world wrap, invalid Y, dynamic rows, backdrop remaps, pin/unpin counts; address and undefined-behavior sanitizers enabled.')
(ROOT/'reports/terrain-strip-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
