#include "intro.h"
#include "music.h"
#include <genesis.h>
typedef struct {u16 cell,value;} IntroWrite;
typedef struct {u16 tick,kind,index;} IntroEvent;
#include "intro_data.inc"
u16 intro_tick;
static u16 next_event,shown_event,sprite_block;
static u8 ready;
void intro_start(void){intro_tick=next_event=shown_event=0;ready=0;sprite_block=65535;music_request=0x30;game.mode=INTRO;}
u8 intro_step(u16 pressed){
 if(++intro_tick>=INTRO_DURATION || (intro_tick>30 && (pressed&IN_START)))return 1;
 return 0;
}
void intro_video(void){
 if(!ready){
  SYS_disableInts();VDP_setEnable(FALSE);DMA_flushQueue();
  VDP_setWindowVPos(FALSE,0);VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
  VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);
  VDP_setHorizontalScroll(BG_B,0);VDP_setVerticalScroll(BG_B,0);
  VDP_loadTileData(intro_bg,16,INTRO_BG_TILES,DMA);
  VDP_loadTileData(intro_font,640,INTRO_FONT_TILES,DMA);
  VDP_setTileMapDataRectEx(BG_B,intro_map,0,0,0,32,28,32,CPU);
  VDP_setTileMapDataRectEx(BG_A,intro_text,0,0,0,32,28,32,CPU);
  VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,DMA);
  PAL_setColors(0,intro_palettes,64,CPU);ready=1;
  VDP_setEnable(TRUE);SYS_enableInts();
 }
 while(next_event<INTRO_EVENTS && intro_events[next_event].tick<=intro_tick)next_event++;
 while(shown_event<next_event){
  const IntroEvent *e=&intro_events[shown_event++];
  if(e->kind==0)PAL_setColors(0,intro_palettes+e->index*64,64,DMA_QUEUE);
  else if(e->kind==1){
   const u16 *p=intro_blocks+intro_offsets[e->index];u16 n=*p++,i;
   const u16 *old=sprite_block==65535?0:intro_blocks+intro_offsets[sprite_block];
   for(i=0;i<n;i++,p+=4){
    u16 slot=1024+i*4;
    if(!old || i>=*old || old[1+i*4+2]!=p[2])VDP_loadTileData(intro_sprites+(u32)p[2]*32,slot,4,DMA_QUEUE);
    VDP_setSpriteFull(i,(s16)p[0],(s16)p[1],SPRITE_SIZE(2,2),TILE_ATTR_FULL(PAL1,FALSE,FALSE,p[3],slot),i+1<n?i+1:0);
   }
   if(!n)VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);
   VDP_updateSprites(n?n:1,DMA_QUEUE);sprite_block=e->index;
  }else{
   const IntroWrite *w=&intro_writes[e->index];
   VDP_setTileMapData(VDP_getBGAAddress(),&w->value,(w->cell/32)*64+w->cell%32,1,2,DMA_QUEUE);
  }
 }
}
