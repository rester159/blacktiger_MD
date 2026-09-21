#include "frontend.h"
#include "boss_rush.h"
#include "container.h"
#include "shop.h"
#include "progress.h"
#include <genesis.h>
#include "ui_data.inc"
static u8 title_ready,title_page=255,title_revision=255,title_message=255;
static u32 hud_score=0xffffffff;
static u16 hud_coins=65535,hud_time=65535;
static u8 hud_stats[12];
static void draw(const char *s,u16 x,u16 y){VDP_drawTextEx(title_ready?BG_A:WINDOW,s,TILE_ATTR(PAL3,TRUE,FALSE,FALSE),x,y,DMA_QUEUE);}
static void number(u16 x,u16 y,u32 value,u8 count){char b[9];u8 n=count;b[count]=0;while(n){b[--n]='0'+value%10;value/=10;}draw(b,x,y);}
static void center(u16 y,const char *text){draw(text,(32-strlen(text))/2,y);}
void ui_game_init(void){
 u16 i;title_ready=0;
 VDP_loadTileData(hud_font,TILE_FONT_INDEX,96,DMA);
 VDP_loadTileData(hud_icons,7,9,DMA);
 VDP_setWindowVPos(FALSE,4);
 for(i=0;i<4;i++)VDP_fillTileMapRect(WINDOW,TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,TILE_FONT_INDEX),0,i,32,1);
 hud_score=0xffffffff;hud_coins=hud_time=65535;memset(hud_stats,255,sizeof hud_stats);
}
void ui_hud(void){
 u8 stats[]={game.p.hp,progress_max_hp,game.p.armor,game.p.weapon,game.p.lives,
  container_keys,shop_antidotes,frontend.credits,game.round,boss_rush.active,boss_rush.stage,boss_rush.shopping};
 u8 changed=memcmp(stats,hud_stats,sizeof stats)!=0;
 if(!changed && hud_score==game.score && hud_coins==game.coins && hud_time==game.time)return;
 VDP_setTextPlane(WINDOW);VDP_setTextPalette(PAL3);
 if(hud_score!=game.score || hud_time!=game.time || changed){
  draw("SCORE          TIME       R",1,0);
  number(7,0,game.score,8);number(21,0,game.time,3);number(28,0,game.round+1,1);
  hud_score=game.score;hud_time=game.time;
 }
 if(changed){
  u16 bars[8],i;
  draw("ENERGY",1,1);draw("ARMOR",16,1);
  for(i=0;i<5;i++)bars[i]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,i>=progress_max_hp?9:i<game.p.hp?7:8);
  VDP_setTileMapDataRow(WINDOW,bars,1,8,5,DMA_QUEUE_COPY);
  for(i=0;i<8;i++)bars[i]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,i<game.p.armor?7:8);
  VDP_setTileMapDataRow(WINDOW,bars,1,22,8,DMA_QUEUE_COPY);
  draw("KEY     WPN    LIFE    ANT",1,2);
  number(5,2,container_keys,2);number(12,2,game.p.weapon,1);number(20,2,game.p.lives,1);number(27,2,shop_antidotes,2);
  draw("ZENNY       CR              ",1,3);number(16,3,frontend.credits,2);
  if(boss_rush.active){draw("BOSS",21,3);number(26,3,boss_rush.stage+1,1);draw("/8",27,3);}
  memcpy(hud_stats,stats,sizeof stats);
 }
 if(changed || hud_coins!=game.coins){number(7,3,game.coins,5);hud_coins=game.coins;}
 VDP_setTextPlane(BG_A);
}
static void title_load(void){
 SYS_disableInts();VDP_setEnable(FALSE);DMA_flushQueue();
 VDP_setWindowVPos(FALSE,0);
 VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
 VDP_setHorizontalScroll(BG_B,0);VDP_setVerticalScroll(BG_B,0);
 VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);
 PAL_setColors(0,title_palette,64,CPU);
 VDP_loadTileData(title_tiles,16,TITLE_TILE_COUNT,DMA);
 VDP_loadTileData(title_font,TILE_FONT_INDEX,96,DMA);
 VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,DMA);
 VDP_setEnable(TRUE);SYS_enableInts();title_ready=1;title_page=255;
}
void ui_title(void){
 static const char *const coinage[]={"4 COINS 1 CREDIT","3 COINS 1 CREDIT","2 COINS 1 CREDIT","1 COIN  1 CREDIT","1 COIN  2 CREDITS","1 COIN  3 CREDITS","1 COIN  4 CREDITS","1 COIN  5 CREDITS"};
 u8 page=frontend.page,home=frontend.mode,message=frontend.message!=0;
 GameSettings *s=&settings[home];
 if(!title_ready)title_load();
 if(title_page==page && title_revision==frontend.revision && title_message==message)return;
 if(title_page!=page){
  VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
  if(page!=2)VDP_setTileMapDataRectEx(BG_B,title_map,0,0,0,32,28,32,CPU);
 }
 title_page=page;title_revision=frontend.revision;title_message=message;
 VDP_setTextPlane(BG_A);VDP_setTextPalette(PAL3);VDP_setTextPriority(TRUE);
 if(page==2){
  u8 i,last=home?7:6;static const char *const labels[]={"LIVES","DIFFICULTY","COINAGE","CONTINUE","MUSIC","SOUND FX","CREDITS"};
  center(3,home?"HOME OPTIONS":"DIP SWITCHES");
  for(i=0;i<=last;i++){
   u8 y=6+i*2;draw(i==frontend.option?">":" ",1,y);
   if(i==last){draw("BACK",3,y);continue;}
   draw(labels[i],3,y);
   switch(i){
    case 0:number(25,y,frontend_lives(),1);break;
    case 1:number(25,y,s->difficulty+1,1);break;
    case 2:draw(coinage[s->coinage],14,y);break;
    case 3:draw(s->continues?"YES":"NO ",23,y);break;
    case 4:draw(s->music?"ON ":"OFF",23,y);break;
    case 5:draw(s->sfx?"ON ":"OFF",23,y);break;
    case 6:number(24,y,s->credits,2);break;
   }
  }
  center(24,"LEFT / RIGHT TO CHANGE");center(26,"B BACK");
 }else{
  u8 i,count=page==0?2:home?3:2;
  VDP_clearTextArea(0,16,32,10);
  if(page==1)center(16,home?"HOME":"ARCADE");
  for(i=0;i<count;i++){
   const char *label=page==0?(i?"HOME":"ARCADE"):i==0?"PLAY":home?(i==1?"BOSS RUSH":"OPTIONS"):"DIP SWITCHES";
   center(18+i*2,label);draw(i==frontend.selected?">":" ",7,18+i*2);
  }
  if(page==0)center(24,"START TO SELECT");
  else if(!home)center(24,message?"INSERT COIN":"SELECT COIN  START PLAY");
  else {draw("CREDIT LIMIT",8,24);number(22,24,s->credits,2);}
  draw("CREDIT",22,27);number(29,27,home && page==1?s->credits:frontend.credits,2);
 }
}
