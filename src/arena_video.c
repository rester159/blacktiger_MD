#include "arena_video.h"
#include "game.h"
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
 u16 y,i,row[33];s16 x=game.cam_x>>3;
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
 if(game.round==3){VDP_setBackgroundColor(4);VDP_loadTileData(backdrop_hud_patterns(),756,256,DMA);cave_hud_edge();}
 arena_video_restore(0);
}
void arena_video_reset(void){
 arena_video_active=0;VDP_setBackgroundColor(0);VDP_setScrollingMode(HSCROLL_PLANE,VSCROLL_PLANE);
 VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);
}
static void cave_hud_edge(void){
 u32 tiles[64];const u32 *source=backdrop_hud_patterns();
 u16 row,line,x=(game.cam_x/2+248)&255,shift=(x&7)*4;
 for(row=0;row<8;row++){
  u16 band=row<4?0:row==4?1:2,height=band==0?4:band==1?1:3;
  u16 y=band==0?row:band==1?0:row-5,base=band==0?0:band==1?128:160;
  u16 a=base+(x/8)*height+y,b=base+(((x/8)+1)&31)*height+y;
  for(line=0;line<8;line++)tiles[row*8+line]=shift?(source[a*8+line]<<shift)|(source[b*8+line]>>(32-shift)):source[a*8+line];
 }
 VDP_loadTileData(tiles,748,8,DMA_QUEUE_COPY);
}
void arena_video_frame(void){
 s16 x=game.cam_x>>3;u16 i,column[29];
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
static VDPSprite column_template[24];
static u8 column_count;
static u16 column_y=65535;
static s16 column_left,column_right;
static void columns_prepare(void){
 s16 hall,block,cy;u16 start,end,tile,w,col,span;
 column_y=game.cam_y;column_count=0;
 for(hall=0;hall<2;hall++){
  if((hall==0 && game.cam_y>=256) || (hall==1 && (game.cam_y>=640 || game.cam_y+200<=448)))continue;
  column_left=hall?616:552;column_right=hall?1256:1896;
  for(block=0;block<6;block++){
   cy=(hall?448:64)+block*32-game.cam_y;
   if(cy>=200 || cy+32<=40)continue;
   start=cy<40?(40-cy+7)/8:0;end=cy+32>200?(200-cy)/8:4;
   if(end<=start)continue;
   tile=block==0?844:block==5?868:860;w=(block==0 || block==5)?4:2;
   span=(start==0 && end==4)?w:1;
   for(col=0;col<w;col+=span){
    VDPSprite *s=&column_template[column_count++];
    s->x=(w==2?8:0)+col*8;s->y=cy+start*8+128;
    s->size=SPRITE_SIZE(span,end-start);
    s->attribut=TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,tile+col*4+start);
   }
  }
 }
}
static u8 *line_budget;
static u8 available_decoration(u16 first,u16 last){
 u8 maximum=0;
 for(;first<last;first++)if(line_budget[first]>maximum)maximum=line_budget[first];
 return 16-maximum;
}
static VDPSprite cave_template[27];
static u8 cave_bands[27],cave_units[27],cave_count;
static u16 cave_x=65535;
static void cave_prepare(void){
 s16 x,offset=-(s16)(game.cam_x/2 & 31);u16 band,i,tile,height,y,skip,width;
 cave_x=game.cam_x/2;cave_count=0;
 for(band=0;band<3;band++){
  height=band==0?4:band==1?1:3;y=band==0?0:band==1?32:200;
  for(i=0;i<9;i++){
   x=offset+(s16)i*32;
   if(x>=248)continue;
   skip=x<0?(-x)/8:0;width=4-skip;x+=skip*8;
   if(x+width*8>248)width=(248-x+7)/8;
   if(!width)continue;
   tile=756+(band==0?0:band==1?128:160)+(((cave_x>>5)+i)&7)*4*height+skip*height;
   cave_template[cave_count]=(VDPSprite){.x=x+128,.y=y+128,.size=SPRITE_SIZE(width,height),.attribut=tile};
   cave_bands[cave_count]=band;cave_units[cave_count++]=(width+1)>>1;
  }
 }
}
__attribute__((noinline)) static u16 cave_hud(u16 count){
 u8 available[3];u16 i;
 if(cave_x!=game.cam_x/2)cave_prepare();
 available[0]=available_decoration(0,4);available[1]=available_decoration(4,5);
 available[2]=shop_rows?0:available_decoration(25,28);
 for(i=0;i<cave_count && count<63;i++){
  u8 band=cave_bands[i],units=cave_units[i];
  if(available[band]<units)continue;
  available[band]-=units;
  vdpSpriteCache[count]=cave_template[i];vdpSpriteCache[count].link=count+1;count++;
 }
 return count;
}
__attribute__((noinline)) u16 arena_video_columns(u16 count,u8 *lines){
 s16 base;u16 i;u8 available;line_budget=lines;
 if(arena_video_active && game.round==3)return cave_hud(count);
 if(!arena_video_active || game.round!=7 || game.cam_x<384 || game.cam_x>1920)return count;
 if(column_y!=game.cam_y)columns_prepare();
 if(!column_count)return count;
 available=available_decoration(5,25);
 base=(game.cam_y>=256?632:568)-(s16)(game.cam_x+game.cam_x/4);
 while(base < -32)base+=80;
 for(;base<256;base+=80){
  if(base+game.cam_x<column_left || base+game.cam_x+32>column_right)continue;
  if(available<2)break;
  available-=2;
  for(i=0;i<column_count && count<63;i++){
   const VDPSprite *s=&column_template[i];s16 x=base+s->x;
   if(x<=-32 || x>=256)continue;
   vdpSpriteCache[count]=*s;vdpSpriteCache[count].x=x+128;
   vdpSpriteCache[count].link=count+1;count++;
  }
 }
 return count;
}
