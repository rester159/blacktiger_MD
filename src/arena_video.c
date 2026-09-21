#include "arena_video.h"
#include "game.h"
#include "boss_rush.h"
#include "arena_parallax_data.inc"
u8 arena_video_active;
static s16 previous_x;
static u8 shop_rows;
static u16 scroll_x=65535;
static u16 wall(s16 x,s16 y){return x<72 || x>=169 || y<8 || y>=37?0:arena_walls[(y-8)*97+x-72];}
static void scroll(void){
 s16 near[28],far[28];u16 y;
 if(scroll_x==game.cam_x)return;
 scroll_x=game.cam_x;
 for(y=0;y<28;y++){
  near[y]=-(s16)game.cam_x;
  far[y]=y>=5 && y<(shop_rows?14:25)?-(s16)(game.cam_x/2):0;
 }
 VDP_setHorizontalScrollTile(BG_B,0,near,28,DMA_QUEUE_COPY);
 VDP_setHorizontalScrollTile(BG_A,0,far,28,DMA_QUEUE_COPY);
 VDP_setVerticalScrollVSync(BG_B,RUSH_Y);VDP_setVerticalScrollVSync(BG_A,0);
}
void arena_video_restore(u8 shop){
 u16 y,x,row[64];shop_rows=shop;scroll_x=65535;
 for(y=5;y<(shop?14:25);y++){
  for(x=0;x<64;x++)row[x]=arena_far[(y-5)*16+(x&15)];
  VDP_setTileMapDataRow(BG_A,row,y,0,64,DMA_QUEUE_COPY);
 }
 scroll();
}
void arena_video_init(void){
 u16 y,i,row[33];s16 x=game.cam_x>>3;
 arena_video_active=1;previous_x=x;shop_rows=0;
 VDP_setScrollingMode(HSCROLL_TILE,VSCROLL_PLANE);
 VDP_loadTileData(arena_patterns,16,ARENA_TILES,DMA);
 for(y=8;y<37;y++){
  for(i=0;i<33;i++)row[i]=wall(x+i,y);
  VDP_setTileMapDataRow(BG_B,row,y&31,x&63,33,CPU);
 }
 arena_video_restore(0);
}
void arena_video_reset(void){
 arena_video_active=0;VDP_setScrollingMode(HSCROLL_PLANE,VSCROLL_PLANE);
 VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);
}
void arena_video_frame(void){
 s16 x=game.cam_x>>3;u16 i,column[29];
 if(x!=previous_x){
  s16 add=x>previous_x?x+32:x;
  for(i=0;i<29;i++)column[i]=wall(add,8+i);
  VDP_setTileMapDataColumn(BG_B,column,add&63,8,29,1,DMA_QUEUE_COPY);
  previous_x=x;
 }
 scroll();
}
u16 arena_video_text_x(u16 x,u16 y){
 return arena_video_active && game.mode!=SHOP && y>=5 && y<25?(x+(game.cam_x/2)/8)&63:x;
}
