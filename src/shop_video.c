#include <genesis.h>
#include "shop.h"
#include "assets.h"
#include "container.h"
#include "frontend.h"
#include "shop_visual_data.inc"
static u8 selection,result;
static u16 coins;
static const u8 columns[7]={3,7,12,17,23,27,31};
static void label(u16 x,u16 y,const char *text){
 u16 words[28],n=0;while(*text && n<28){u8 c=*text++;words[n++]=shop_font[c>=32 && c<=90?c-32:0];}
 VDP_setTileMapDataRow(BG_A,words,y,x,n,DMA_QUEUE_COPY);
}
static void price(u16 x,u16 y,u16 value,u8 width){
 char digits[6],text[7];u8 i=5,j=0;if(width>6)width=6;digits[5]=0;
 do{digits[--i]='0'+value%10;value/=10;}while(value && i);
 while(i<5 && j<width)text[j++]=digits[i++];
 while(j<width)text[j++]=' ';
 text[j]=0;label(x,y,text);
}
void shop_video_init(void){
 u16 i;
 DMA_flushQueue();SYS_disableInts();VDP_setEnable(FALSE);
 VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
 PAL_setColors(0,shop_backdrop_palette,32,CPU);
 VDP_loadTileData(shop_backdrop_tiles,16,SHOP_BACKDROP_TILES,DMA);
 VDP_setTileMapDataRect(BG_B,shop_backdrop_map,0,0,32,28,32,DMA);
 VDP_setHorizontalScroll(BG_B,0);VDP_setVerticalScroll(BG_B,0);
 VDP_loadTileData(shop_tiles,1088,SHOP_TILES,DMA);
 VDP_setTileMapDataRect(BG_A,shop_map,0,14,32,11,32,DMA);
 for(i=0;i<10;i++){
  u16 tile=1088+SHOP_TILES+i*4,words[4]={tile+0xe000,tile+2+0xe000,tile+1+0xe000,tile+3+0xe000};
  VDP_loadTileData(shop_icons+i*32,tile,4,DMA);
  VDP_setTileMapDataRect(BG_A,words,columns[i%5],18+(i/5)*3,2,2,2,CPU);
 }
 VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,DMA);
 ui_shop_cursor_init();ui_hud_invalidate();ui_hud();DMA_flushQueue();
 shop_result=0;selection=result=255;coins=65535;
 VDP_setEnable(TRUE);SYS_enableInts();
}
void shop_video_frame(void){
 u16 i;u8 item=shop_grid[game.shop_item];
 static const char *const names[]={"","WEAPON 2","WEAPON 3","WEAPON 4","WEAPON 5","ARMOR 1","ARMOR 2","ARMOR 3","ARMOR 4","KEY","ANTIDOTE","LEAVE SHOP"};
 ui_hud();
 if(selection==game.shop_item && result==shop_result && coins==game.coins)return;
 selection=game.shop_item;result=shop_result;coins=game.coins;
 /* Original horizontal rows: weapons/key above armor/antidote/exit. */
 for(i=0;i<12;i++){
  u8 good=shop_grid[i],col=i%6,row=i/6;
  if(!good)continue;
  if(good!=11)price(columns[col],20+row*3,shop_price(good,shop_difficulty),columns[col+1]-columns[col]);
  label(columns[col]-1,18+row*3," ");
 }
 ui_shop_cursor(selection);
 label(2,15,"                            ");label(2,16,"                            ");
 label(3,15,names[item]);
 label(3,16,result==1?"THANK YOU!":result==2?"NOT ENOUGH ZENNY":result==3?"ALREADY EQUIPPED":result==4?"CANNOT CARRY MORE":(frontend.mode?"A BUY   B / START EXIT":"A BUY   B EXIT"));
}

/* Original six-sprite blue frame, fixed 6828 and position table 6E45. */
void ui_shop_cursor_init(void){VDP_loadTileData(shop_cursor_tiles,(1088+SHOP_TILES+40),24,DMA);}
void ui_shop_cursor(u16 selected){
 const u8 *box=shop_cursor_positions+selected*4;u16 i;
 for(i=0;i<6;i++)VDP_setSpriteFull(i,box[0]+(i%3)*box[1],box[2]-16+(i/3)*box[3],SPRITE_SIZE(2,2),TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,(1088+SHOP_TILES+40)+i*4),i==5?0:i+1);
 VDP_updateSprites(6,DMA_QUEUE);
}
