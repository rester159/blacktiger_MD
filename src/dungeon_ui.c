#include "dungeon.h"
#include "frontend.h"
#include <genesis.h>
#include "dungeon_palette_data.inc"
static u8 ready,last_phase=255;
static u16 previous_revision=65535;
void dungeon_ui_reset(void){ready=0;last_phase=255;previous_revision=65535;ui_hud_invalidate();}
static void text(u16 x,u16 y,const char *s){VDP_drawTextEx(BG_A,s,TILE_ATTR(PAL2,TRUE,FALSE,FALSE),x,y,DMA_QUEUE);}
static void number(u16 x,u16 y,u32 value,u8 n){char b[11];u8 i=n;b[n]=0;while(i){b[--i]='0'+value%10;value/=10;}text(x,y,b);}
static void center(u16 y,const char *s){text((32-strlen(s))/2,y,s);}
static void clock_text(u16 x,u16 y){u16 seconds=dungeon_seconds();number(x,y,seconds/60,2);text(x+2,y,":");number(x+3,y,seconds%60,2);}
void dungeon_screen(void){
 if(!ready){
  SYS_disableInts();VDP_setEnable(FALSE);DMA_flushQueue();
  VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);VDP_clearPlane(WINDOW,TRUE);
  VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);VDP_setVerticalScroll(BG_B,0);
  ui_game_init();PAL_setColors(0,dungeon_base_palette,64,CPU);
  VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,DMA);
  VDP_setEnable(TRUE);SYS_enableInts();ready=1;
 }
 if(previous_revision==dungeon.revision && last_phase==dungeon.phase)return;
 previous_revision=dungeon.revision;last_phase=dungeon.phase;
 VDP_clearPlane(BG_A,TRUE);center(2,"THE DUNGEON");center(4,"BLACK TIGER: THE LAST HOUR");
 if(dungeon.phase==D_SETUP){
  char seed[7];u32 value=dungeon.seed;u8 i;static const char alphabet[]="ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  for(i=0;i<6;i++){seed[5-i]=alphabet[value&31];value>>=5;}seed[6]=0;
  text(4,7,"RANK");number(10,7,dungeon.rank,2);text(4,9,"BANKED XP");number(16,9,dungeon.banked_xp,8);
  text(4,12,"SEED");text(16,12,seed);text(4,15,"WEAPON  IRON FLAIL");text(4,17,"ARMOR   LEATHER");text(4,19,"PLAYERS 1");
  center(23,"START TO DESCEND");center(25,"B BACK");
 }else if(dungeon.phase==D_STAGE_INTRO){
  center(9,"STAGE");number(15,11,dungeon.stage,2);center(14,"THE LAST HOUR");clock_text(13,17);center(21,"TIME IS YOUR LIFE");
 }else if(dungeon.phase==D_GATE){
  center(7,"STAGE CLEAR");text(4,10,"XP");number(9,10,dungeon.run_xp,8);clock_text(21,10);
  text(6,14,"+2 MAX VITALITY");text(6,16,"+60 SECONDS");text(6,18,"+15000 ZENNY");text(3,14+dungeon.boon*2,">");center(23,"START TO CHOOSE");
 }else {
  center(7,dungeon.cleared?"THE DUNGEON CONQUERED":"YOUR HOUR HAS ENDED");
  text(4,10,"STAGE");number(22,10,dungeon.stage,2);text(4,12,"RUN XP");number(16,12,dungeon.run_xp,8);
  text(4,14,"BANKED XP");number(16,14,dungeon.banked_xp,8);text(4,16,"KILLS");number(19,16,dungeon.kills,5);
  text(4,18,"SCORE");number(16,18,dungeon.score,8);center(23,"START NEW RUN");center(25,"B BACK");
 }
 center(27,"RESTER159 2026");
}
void dungeon_hud(void){ui_hud();}
