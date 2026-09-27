#include "attract.h"
#include "frontend.h"
#include "high_score.h"
#include "assets.h"
#include "attract_data.inc"
/* Source display replay has no access to game logic, credits or SRAM writes.
   Stream records add sparse byte deltas to native display state. */
u16 attract_frame;
u8 attract_running,attract_credit;
volatile u8 attract_decoding;
static u8 ready,shown_credit;
static u16 bg_dirty;
static u32 text_dirty,shown_score;
static const u8 *stream;
static u8 *workspace,flags,bits,copy_left;
/* The gameplay sprite lookup is idle on title screens. Reuse its storage
   instead of taking 8 KiB from the DMA heap and 68000 stack. */
#define dictionary (*(u8 (*)[4096])(workspace))
#define attract_state (*(u8 (*)[ATTRACT_STATE_SIZE])(workspace+4096))
#define shown_sprite (*(u16 (*)[64])(workspace+7430))
static u16 head,distance;

#define BG 6
#define FG 1030
#define SP 2822
static void decoder(const u8 *p){stream=p;head=bits=copy_left=0;}
static inline __attribute__((always_inline)) u8 byte(void){
 u8 v;
 if(!copy_left){
  if(!bits){flags=*stream++;bits=8;}
  if(flags&1){v=*stream++;flags>>=1;bits--;dictionary[head++&4095]=v;return v;}
  distance=((u16)stream[0]<<4)|(stream[1]>>4);distance++;
  copy_left=(stream[1]&15)+3;stream+=2;flags>>=1;bits--;
 }
 v=dictionary[(head-distance)&4095];dictionary[head++&4095]=v;copy_left--;return v;
}
static u16 word(u16 at){return *(const u16*)(attract_state+at);}
static void decode_frame(void){
 attract_decoding=1;
 for(;;){
  u16 at=(u16)byte()<<8;at|=byte();if(at==65535){__asm__ volatile("" ::: "memory");attract_decoding=0;return;}
  u16 n=byte(),end=at+n,row,last;
  if(at<FG && end>BG){
   row=at<BG?0:(at-BG)>>6;last=(end>FG?FG-1:end-1)-BG;last>>=6;
   while(row<=last)bg_dirty|=1<<row++;
  }
  if(at<SP && end>FG){
   row=at<FG?0:(at-FG)>>6;last=(end>SP?SP-1:end-1)-FG;last>>=6;
   while(row<=last)text_dirty|=1UL<<row++;
  }
  while(n--)attract_state[at++]+=byte();
 }
}
static void restart(void){
 attract_decoding=1;bg_dirty=65535;text_dirty=0x0fffffff;
 memcpy(attract_state,attract_credit?attract_credit_state:attract_initial,sizeof attract_state);
 decoder(attract_stream);attract_frame=0;attract_decoding=0;
}
u8 attract_active(void){return game.mode==TITLE && frontend.mode==0 && frontend.page==1;}
void attract_reset(void){attract_running=ready=0;}
void attract_step(void){
 if(!attract_active()){attract_reset();return;}
 workspace=video_attract_workspace();
 u8 credit=frontend.credits!=0;
 if(!attract_running || credit!=attract_credit){attract_credit=credit;attract_running=1;if(ready)restart();return;}
 if(!ready || attract_credit)return;
 attract_decoding=1;
 if(++attract_frame>=ATTRACT_FRAMES)restart();else decode_frame();
}
static void load(void){

 extern volatile u16 video_reload_count;video_reload_count++;
 SYS_disableInts();VDP_setEnable(FALSE);DMA_flushQueue();
 VDP_setWindowVPos(FALSE,0);VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
 VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);
 PAL_setColors(0,attract_palette,32,CPU);PAL_setColors(32,object_palette,32,CPU);
 VDP_loadTileData(attract_patterns,16,ATTRACT_PATTERN_COUNT,DMA);
 memset(shown_sprite,255,sizeof shown_sprite);
 ui_attract_version();restart();ready=1;
 /* Leave display off for the initial full plane upload. */
}
static void number(u16 *row,u8 x,u8 n,u32 value,const u16 *chars){
 while(n){row[x+--n]=chars['0'-32+value%10];value/=10;if(!value){while(n)row[x+--n]=chars[0];break;}}
}
static void saved_row(u16 *row,u8 y){
 if(y==1)number(row,12,8,high_score,attract_chars7);
 if(y==27)row[31]=attract_chars0['0'-32+frontend.credits];
 if(attract_state[4] && y>=16 && y<=24 && !(y&1)){
  u8 i=(y-16)/2,j;const HighScoreEntry *e=&high_scores[i];
  /* Keep original default records until a named score has been recorded. */
  u8 defaults=high_scores[0].score==20000 && high_scores[0].initials[0]=='-' && !high_scores[1].score;
  if(!defaults){
   number(row,13,e->score>9999999?8:7,e->score,attract_chars7);
   if(e->score<=9999999)row[20]=attract_chars0[0];
   for(j=0;j<3;j++)row[21+j]=attract_chars0[e->initials[j]-32];
  }
 }
 if(attract_credit && y==14){
  const char *prompt="PUSH A BUTTON";u8 i;
  for(i=0;i<32;i++)row[i]=attract_chars0[0];
  for(i=0;prompt[i];i++)row[9+i]=attract_chars0[prompt[i]-32];
 }
}
void attract_video(void){
 u16 y,x,i,n=0;u8 initial=!ready;
 if(initial)load();
 if(shown_score!=high_score){shown_score=high_score;text_dirty|=2;}
 if(shown_credit!=frontend.credits){shown_credit=frontend.credits;text_dirty|=1UL<<27;}
 /* 32x16 metatile ring, uploaded only when an original cell changes. */
 for(y=0;y<16;y++){
  if(bg_dirty&(1<<y)){
   u16 top[64],bottom[64];
   for(x=0;x<32;x++){
    u16 q=word(BG+(y*32+x)*2);const u16 *p=attract_quads+q*4;
    top[x*2]=p[0];top[x*2+1]=p[1];bottom[x*2]=p[2];bottom[x*2+1]=p[3];
   }
   VDP_setTileMapDataRow(BG_B,top,y*2,0,64,initial?CPU:DMA_QUEUE_COPY);
   VDP_setTileMapDataRow(BG_B,bottom,y*2+1,0,64,initial?CPU:DMA_QUEUE_COPY);
  }
 }
 bg_dirty=0;
 for(y=0;y<28;y++)if(text_dirty&(1UL<<y)){
  u16 row[32];for(x=0;x<32;x++)row[x]=word(FG+(y*32+x)*2);
  saved_row(row,y);
  if(y==27){row[0]=0x6000|1278;row[1]=0x6000|1279;}
  VDP_setTileMapDataRow(BG_A,row,y,0,32,initial?CPU:DMA_QUEUE_COPY);
 }
 text_dirty=0;
 VDP_setHorizontalScrollVSync(BG_B,-word(0));VDP_setVerticalScrollVSync(BG_B,word(2));
 if(attract_state[5])for(i=0;i<128 && n<64;i++){
  const u8 *p=attract_state+SP+i*4;u16 code=p[0]|((u16)(p[1]&224)<<3);s16 sx=p[3]-((p[1]&16)<<4),sy=p[2]-16;
  if(sx<=-16 || sx>=256 || sy<=-16 || sy>=224)continue;
  u16 key=code+(u16)(p[1]&7)*2048;
  if(key!=shown_sprite[n]){video_attract_piece(key,1280+n*4);shown_sprite[n]=key;}
  VDP_setSpriteFull(n,sx,sy,SPRITE_SIZE(2,2),TILE_ATTR_FULL((p[1]&7)?PAL3:PAL2,FALSE,FALSE,p[1]&8,1280+n*4),n+1);n++;
 }
 if(n)VDP_setSpriteLink(n-1,0);else VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);
 VDP_updateSprites(n?n:1,initial?DMA:DMA_QUEUE);
 if(initial){DMA_flushQueue();VDP_setEnable(TRUE);SYS_enableInts();}
}
