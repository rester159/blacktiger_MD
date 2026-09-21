#include "frontend.h"
#include "dungeon.h"
#include "boss_rush.h"
#include "container.h"
#include "shop.h"
#include "progress.h"
#include <genesis.h>
#include "ui_data.inc"
static u8 title_ready,title_page=255,title_revision=255,title_message=255;
static u32 high_score=20000;
static u16 hud_previous[256];
static u8 hud_invalid=1;
static u32 hud_score,hud_xp;
static u8 hud_max_hp,hud_charges,hud_exit;
static u16 hud_coins,hud_time;
static u8 hud_hp,hud_weapon,hud_armor,hud_keys,hud_antidotes;
#include "hud_data.inc"
static void draw(const char *s,u16 x,u16 y){VDP_drawTextEx(BG_A,s,TILE_ATTR(PAL3,TRUE,FALSE,FALSE),x,y,DMA_QUEUE);}
static void number(u16 x,u16 y,u32 value,u8 count){char b[9];u8 n=count;b[count]=0;while(n){b[--n]='0'+value%10;value/=10;}draw(b,x,y);}
static void center(u16 y,const char *text){draw(text,(32-strlen(text))/2,y);}
void ui_hud_invalidate(void){hud_invalid=1;}
void ui_game_init(void){
 u16 i;title_ready=0;hud_invalid=1;
 VDP_loadTileData(hud_font,TILE_FONT_INDEX,96,DMA);
 for(i=0;i<ARCADE_HUD_TILES;i++)VDP_loadTileData(arcade_hud_patterns+i*8,arcade_hud_slots[i],1,DMA);
 VDP_setWindowVPos(FALSE,0);
}
static void hud_number(u16 *p,u32 value,u8 count,u8 blue,u8 spaces){
 const u16 *digits=arcade_hud_digits+blue*11;
 while(count){p[--count]=digits[value%10];value/=10;if(spaces && !value){while(count)p[--count]=digits[10];break;}}
}
static void hud_icon(u16 *p,const u16 *icon){p[0]=icon[0];p[1]=icon[1];p[32]=icon[2];p[33]=icon[3];}
void ui_hud(void){
 u16 map[256],i,row,seconds=dungeon.active?dungeon_seconds():game.time;
 u8 hp=dungeon.active?(game.p.hp*5+dungeon.max_hp-1)/dungeon.max_hp:(game.p.hp>5?5:game.p.hp);
 u8 exit=dungeon_layout.ready && PX(game.p.x)>=dungeon_layout.exit_x;
 if(!hud_invalid && hud_score==game.score && hud_coins==game.coins && hud_time==seconds &&
    hud_hp==game.p.hp && (!dungeon.active || (hud_xp==dungeon.run_xp && hud_max_hp==dungeon.max_hp && hud_charges==dungeon.charges && hud_exit==exit)) && hud_weapon==game.p.weapon && hud_armor==game.p.armor &&
    hud_keys==container_keys && hud_antidotes==shop_antidotes)return;
 hud_score=game.score;hud_coins=game.coins;hud_time=seconds;hud_hp=game.p.hp;
 hud_xp=dungeon.run_xp;hud_max_hp=dungeon.max_hp;hud_charges=dungeon.charges;hud_exit=exit;
 hud_weapon=game.p.weapon;hud_armor=game.p.armor;hud_keys=container_keys;hud_antidotes=shop_antidotes;
 if(game.score>high_score)high_score=game.score;
 memcpy(map,arcade_hud_map,5*64);memcpy(map+160,arcade_hud_map+25*32,3*64);
 hud_number(map+32+2,game.score,7,1,1);hud_number(map+32+13,high_score,7,1,1);
 if(dungeon.active && seconds>=600)hud_number(map+3*32,seconds/60,2,0,0);
 else hud_number(map+3*32+1,seconds/60,1,0,0);hud_number(map+3*32+3,seconds%60,2,0,0);
 for(i=0;i<10;i++)map[3*32+7+i]=0;
 for(i=0;i<hp;i++){u8 color=i>1?2:i;map[3*32+7+i*2]=arcade_hud_vital[color*2];map[3*32+8+i*2]=arcade_hud_vital[color*2+1];}
 hud_number(map+4*32+26,game.coins,5,0,0);
 hud_icon(map+160+11,arcade_hud_weapons+(game.p.weapon?game.p.weapon-1:0)*4);
 hud_icon(map+160+15,arcade_hud_armors+(game.p.armor>8?8:game.p.armor)*4);
 hud_number(map+224+7,container_keys,2,0,0);hud_number(map+224+19,shop_antidotes,2,0,0);
 if(dungeon.active){
  /* Original arcade top/bottom layout; additions occupy unused cells. */
  const char *label="XP",*glass="HG",*gate=exit?"UP EXIT":"       ";
  for(i=0;i<2;i++){
   map[160+23+i]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,TILE_FONT_INDEX+label[i]-32);
   map[160+1+i]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,TILE_FONT_INDEX+glass[i]-32);
  }
  hud_number(map+192+23,dungeon.run_xp,8,0,0);
  hud_number(map+224+1,dungeon.charges,2,0,0);
  hud_number(map+128+7,game.p.hp,2,0,0);
  map[128+9]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,TILE_FONT_INDEX+'/'-32);
  hud_number(map+128+10,dungeon.max_hp,2,0,0);
  for(i=0;i<7;i++)map[224+24+i]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,TILE_FONT_INDEX+gate[i]-32);
 }
 for(row=0;row<8;row++)if(hud_invalid || memcmp(map+row*32,hud_previous+row*32,64)){
  VDP_setTileMapDataRow(BG_A,map+row*32,row<5?row:row+20,0,32,DMA_QUEUE_COPY);
  memcpy(hud_previous+row*32,map+row*32,64);
 }
 hud_invalid=0;
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
  u8 i,count=page==0?2:home?4:2;
  VDP_clearTextArea(0,16,32,10);
  if(page==1)center(home?15:16,home?"HOME":"ARCADE");
  for(i=0;i<count;i++){
   const char *label=page==0?(i?"HOME":"ARCADE"):i==0?"PLAY":home?(i==1?"BOSS RUSH":i==2?"THE DUNGEON":"OPTIONS"):"DIP SWITCHES";
   center((page==1 && home?16:18)+i*2,label);draw(i==frontend.selected?">":" ",7,(page==1 && home?16:18)+i*2);
  }
  if(page==0)center(24,"START TO SELECT");
  else if(!home)center(24,message?"INSERT COIN":"SELECT COIN  START PLAY");
  else {draw("CREDIT LIMIT",8,24);number(22,24,s->credits,2);}
  draw("RESTER159 2026",1,27);draw("CREDIT",22,27);number(29,27,home && page==1?s->credits:frontend.credits,2);
 }
}

/* Existing font glyphs, recolored to the immutable white clock entry. */
void ui_dungeon_font(void){
 u32 tiles[11*8];u16 i,j;
 for(i=0;i<11;i++)for(j=0;j<8;j++){
  u32 word=hud_font[(i<10?16+i:26)*8+j];tiles[i*8+j]=word&0xeeeeeeeeUL;
 }
 VDP_loadTileData(tiles,1012,11,CPU);
}
