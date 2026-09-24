#include "arena_video.h"
#include "game.h"
#include "assets.h"
#include "boss_rush.h"
#include "backdrop.h"
#include "arena_parallax_data.inc"
u8 arena_video_active;
static u8 shop_rows;
static const Backdrop *backdrop;
static s16 previous_x;
static u16 wall(s16 x,s16 y){return x<72 || x>=169 || y<8 || y>=37?0:arena_near[(y-8)*97+x-72];}
static u16 scroll_x=65535,scroll_y=65535;
const u16 *arena_video_map(void){return arena_walls;}
const u32 *arena_video_pattern(u16 tile){return arena_patterns+(u32)tile*8;}
static void scroll(void){
 s16 near[28],far[28];u16 y;
 if(scroll_x==game.cam_x && scroll_y==game.cam_y)return;
 scroll_x=game.cam_x;scroll_y=game.cam_y;
 for(y=0;y<28;y++){
  near[y]=-(s16)game.cam_x;
  far[y]=y>=5 && y<(shop_rows?14:25)?-(s16)(game.cam_x/2):0;
 }
 VDP_setHorizontalScrollTile(BG_B,0,near,28,DMA_QUEUE_COPY);
 VDP_setHorizontalScrollTile(BG_A,0,far,28,DMA_QUEUE_COPY);
 VDP_setVerticalScrollVSync(BG_B,game.cam_y);VDP_setVerticalScrollVSync(BG_A,0);
}
void arena_video_restore(u8 shop){
 u16 y,x,row[64];shop_rows=shop;scroll_x=scroll_y=65535;
 for(y=5;y<(shop?14:25);y++){
  for(x=0;x<64;x++)row[x]=backdrop?backdrop->map[(y-5)*64+x]:arena_far[(y-5)*16+(x&15)];
  VDP_setTileMapDataRow(BG_A,row,y,0,64,DMA_QUEUE_COPY);
 }
 scroll();
}
/* Far scenery occupies fixed, shared patterns above the terrain cache. */
static void cave_hud_edge(void);
void arena_video_init(void){
 u16 y,i,row[33];s16 x=(s16)game.cam_x>>3;
 arena_video_active=1;shop_rows=0;previous_x=x;backdrop=backdrop_for_round(game.round);
 if(boss_rush.active){
  VDP_loadTileData(arena_near_patterns,16,ARENA_NEAR_TILES,DMA);
  for(y=8;y<37;y++){
   for(i=0;i<33;i++)row[i]=wall(x+i,y);
   VDP_setTileMapDataRow(BG_B,row,y&31,x&63,33,CPU);
  }
 }
 VDP_setScrollingMode(HSCROLL_TILE,VSCROLL_PLANE);
 if(backdrop)VDP_loadTileData(backdrop->far,game.round==3?656:700,backdrop->far_tiles,DMA);
 else {VDP_loadTileData(arena_far_patterns,884,ARENA_FAR_TILES,DMA);
 VDP_loadTileData(arena_columns,844,ARENA_COLUMN_TILES,DMA);}
 VDP_setBackgroundColor(game.round==7?21:0);
 if(game.round==3){VDP_setBackgroundColor(4);VDP_loadTileData(backdrop_hud_patterns(),756,256,DMA);cave_hud_edge();}
 arena_video_restore(0);
}
void arena_video_reset(void){
 arena_video_active=0;VDP_setBackgroundColor(0);VDP_setScrollingMode(HSCROLL_PLANE,VSCROLL_PLANE);
 VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);
}
static void cave_hud_edge(void){
 backdrop_hud_edge_load(game.cam_x/2+248,748);
}
void arena_video_frame(void){
 s16 x=(s16)game.cam_x>>3;u16 i,column[29];
 if(boss_rush.active && x!=previous_x){
  s16 add=x>previous_x?x+32:x;
  for(i=0;i<29;i++)column[i]=wall(add,8+i);
  VDP_setTileMapDataColumn(BG_B,column,add&63,8,29,1,DMA_QUEUE_COPY);
  previous_x=x;
 }
 if(game.round==3 && (scroll_x!=game.cam_x || scroll_y==65535))cave_hud_edge();
 scroll();
}
u16 arena_video_text_x(u16 x,u16 y){
 return arena_video_active && game.mode!=SHOP && y>=5 && y<25?(x+(game.cam_x/2)/8)&63:x;
}

/* Resident column templates are rebuilt only when vertical camera placement
   changes. Actors precede decoration in the SAT, so hardware scanline overflow
   drops decoration first; the global SAT limit is enforced here as well. */
static u8 *line_budget;
static u8 available_decoration(u16 first,u16 last){
 u8 maximum=0;
 for(;first<last;first++)if(line_budget[first]>maximum)maximum=line_budget[first];
 return 16-maximum;
}
#include "cave_sprite_geometry.inc"
__attribute__((noinline)) static u16 cave_hud(u16 count){
 u16 band,i,shift=(game.cam_x/2>>3)&28;
 const typeof(cave_geometry[0][0]) *geometry=cave_geometry[(game.cam_x/2)&31];
 static const u16 bases[3]={756,884,916},ys[3]={128,160,328};
 static const u8 heights[3]={4,1,3},first[3]={0,4,25},last[3]={4,5,28};
 for(band=0;band<3;band++){
  u8 available=band==2 && shop_rows?0:available_decoration(first[band],last[band]);
  u16 height=heights[band],base=bases[band],y=ys[band];
  for(i=0;i<9 && count<63;i++){
   u8 units=geometry[i].units;
   VDPSprite *sprite;
   if(!units || available<units)continue;
   available-=units;sprite=&vdpSpriteCache[count];
   sprite->x=geometry[i].x;sprite->y=y;
   sprite->size=geometry[i].size+height-1;
   sprite->attribut=base+((geometry[i].column+shift)&31)*height;
   sprite->link=++count;
  }
 }
 return count;
}
__attribute__((noinline)) u16 arena_video_columns(u16 count,u8 *lines){
 line_budget=lines;
 if(arena_video_active && game.round==3)return cave_hud(count);
 return count;
}
