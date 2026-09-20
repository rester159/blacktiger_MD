#include "ending.h"
#include "ending_timeline.inc"
Ending ending;
u8 ending_text[896];
u32 ending_dirty_rows;
static void clear_text(void){
 u16 i;for(i=64;i<896;i++)ending_text[i]=32;
 ending_dirty_rows=0x0ffffffcUL;
}
void ending_reset(void){
 u16 i;ending=(Ending){0};ending.palette=255;
 for(i=0;i<896;i++)ending_text[i]=32;
 ending_dirty_rows=0;
}
void ending_start(void){ending_reset();ending.active=1;ending_dirty_rows=0x0fffffffUL;}
u8 ending_step(void){
 if(ending.complete)return 1;
 while(ending.index<ENDING_EVENTS && ending_events[ending.index].tick==ending.tick){
  const EndingEvent *e=&ending_events[ending.index++];
  switch(e->type){
   case 0:ending_text[e->cell]=e->value;ending_dirty_rows|=1UL<<(e->cell>>5);break;
   case 1:clear_text();break;
   case 2:ending.palette=e->value;break;
   case 3:ending.scene=e->value;break;
   case 4:ending.complete=1;return 1;
  }
 }
 ending.tick++;return 0;
}
