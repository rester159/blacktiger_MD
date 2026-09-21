#include "dungeon.h"
#include "frontend.h"
#include <genesis.h>
#include "dungeon_palette_data.inc"
static u8 ready,last_phase=255;
static u16 previous_revision=65535,previous_seconds=65535;
static u32 previous_xp=0xffffffff;
static u16 previous_coins=65535,previous_kills=65535;
static u8 previous_hp=255,previous_frozen=255,previous_pulse=255;
void dungeon_ui_reset(void){ready=0;last_phase=255;previous_revision=65535;previous_seconds=65535;previous_xp=0xffffffff;previous_hp=255;}
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
void dungeon_hud(void){
 u16 seconds=dungeon_seconds();char row[33];u8 i;
 /* Window plane is fixed in screen space and consumes no sprites. */
 VDP_setWindowVPos(FALSE,4);
 if(previous_revision==dungeon.revision && previous_seconds==seconds && previous_xp==dungeon.run_xp && previous_coins==game.coins && previous_kills==dungeon.kills && previous_hp==game.p.hp && previous_frozen==!!dungeon.freeze && previous_pulse==(seconds<30 && (game.frame%50)<25))return;
 previous_seconds=seconds;previous_xp=dungeon.run_xp;previous_revision=dungeon.revision;
 previous_coins=game.coins;previous_kills=dungeon.kills;previous_hp=game.p.hp;previous_frozen=!!dungeon.freeze;previous_pulse=seconds<30 && (game.frame%50)<25;
 for(i=0;i<32;i++)row[i]=' ';row[32]=0;
 VDP_drawTextEx(WINDOW,row,TILE_ATTR(PAL3,TRUE,FALSE,FALSE),0,0,DMA_QUEUE);
 {char b[33]="P1                  CLOCK 00:00";u16 n=seconds/60;b[26]='0'+n/10;b[27]='0'+n%10;b[29]='0'+seconds%60/10;b[30]='0'+seconds%10;
  for(i=0;i<16;i++)b[3+i]=i<game.p.hp?'I':i<dungeon.max_hp?'.':' ';
  VDP_drawTextEx(WINDOW,b,TILE_ATTR(PAL3,TRUE,FALSE,FALSE),0,0,DMA_QUEUE);}
 {char b[33]="XP 00000000  STAGE 00  HG 0     ";u32 value=dungeon.run_xp;for(i=0;i<8;i++){b[10-i]='0'+value%10;value/=10;}b[19]='0'+dungeon.stage/10;b[20]='0'+dungeon.stage%10;b[26]='0'+dungeon.charges;
  VDP_drawTextEx(WINDOW,b,TILE_ATTR(PAL3,TRUE,FALSE,FALSE),0,1,DMA_QUEUE);}
 {char b[33]="ZENNY 00000   KILLS 00000       ";u16 value=game.coins;for(i=0;i<5;i++){b[10-i]='0'+value%10;value/=10;}value=dungeon.kills;for(i=0;i<5;i++){b[24-i]='0'+value%10;value/=10;}
  VDP_drawTextEx(WINDOW,b,TILE_ATTR(PAL3,TRUE,FALSE,FALSE),0,2,DMA_QUEUE);}
 {u16 tiles[5],n=seconds/60;u8 digits[5]={n/10,n%10,10,seconds%60/10,seconds%10};
  for(i=0;i<5;i++)tiles[i]=TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,previous_pulse?TILE_FONT_INDEX+16+digits[i]:1012+digits[i]);
  VDP_setTileMapDataRow(WINDOW,tiles,0,26,5,DMA_QUEUE_COPY);
 }
 VDP_drawTextEx(WINDOW,dungeon.freeze?"HOURGLASS ACTIVE                ":"C HOURGLASS   START PAUSE        ",TILE_ATTR(PAL3,TRUE,FALSE,FALSE),0,3,DMA_QUEUE);
}
