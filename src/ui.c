#include "attract.h"
#include "frontend.h"
#include "boss_rush.h"
#include "boss.h"
#include "actor_dispatch.h"
#include "assets.h"
#include "container.h"
#include "shop.h"
#include "progress.h"
#include "high_score.h"
#include <genesis.h>
#include "ui_data.inc"
static u8 title_ready,title_page=255,title_revision=255,title_message=255,title_coin_phase=255;
static u32 title_high_score;
static u16 hud_previous[256];
static u8 hud_invalid=1;
extern volatile u32 pacing_presentations;
u16 debug_fps;
static u32 fps_refresh, fps_presentations;
static u8 hud_fps_visible;
static u16 hud_fps;
static u32 hud_score;
static u16 hud_coins,hud_time;
static u8 hud_boss_present,hud_boss_fill,hud_boss_stage,hud_credit=255,hud_arcade=255;
static u8 hud_hp,hud_weapon,hud_armor,hud_keys,hud_antidotes;
#include "hud_data.inc"
static void draw(const char *s,u16 x,u16 y){VDP_drawTextEx(BG_A,s,TILE_ATTR(PAL3,TRUE,FALSE,FALSE),x,y,DMA_QUEUE);}
#define HOME_CURSOR_TILE (18+TITLE_TILE_COUNT+HOME_MD_TILE_COUNT)
static void cursor(u8 selected,u16 x,u16 y){
 if(selected)VDP_setSpriteFull(0,x*8-2,y*8-4,SPRITE_SIZE(2,2),TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,HOME_CURSOR_TILE),0);
}
static void number(u16 x,u16 y,u32 value,u8 count){char b[9];u8 n=count;b[count]=0;while(n){b[--n]='0'+value%10;value/=10;}draw(b,x,y);}
static void score_number(u16 x,u16 y,u32 value){
 char b[9];u8 n=8;b[8]=0;
 do{b[--n]='0'+value%10;value/=10;}while(value && n);
 while(n)b[--n]=' ';
 draw(b,x,y);
}
static void center(u16 y,const char *text){
 u16 n=strlen(text),i,line,left=0,right=0,x,shift,base,words[32];
 u32 edge=0;
 if(!n)return;
 for(line=0;line<8;line++)edge|=title_font[(text[0]-32)*8+line];
 while(left<8 && !(edge&0xf0000000)){left++;edge<<=4;}
 edge=0;
 for(line=0;line<8;line++)edge|=title_font[(text[n-1]-32)*8+line];
 while(right<8 && !(edge&15)){right++;edge>>=4;}
 /* Center the visible glyph bounds, including their unequal side bearings. */
 x=(256-(n*8-left-right))/2-left;shift=x&7;x>>=3;
 if(!shift){draw(text,x,y);return;}
 base=512+y*32;
 u32 *pixels=DMA_allocateAndQueueDma(DMA_VRAM,base*32,(n+1)*16,2);
 if(!pixels)return;
 for(i=0;i<=n;i++){
  words[i]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,base+i);
  for(line=0;line<8;line++){
   u32 previous=i?title_font[(text[i-1]-32)*8+line]:0;
   u32 current=i<n?title_font[(text[i]-32)*8+line]:0;
   pixels[i*8+line]=(previous<<(32-shift*4))|(current>>(shift*4));
  }
 }
 VDP_setTileMapDataRow(BG_A,words,y,x,n+1,DMA_QUEUE_COPY);
}

void ui_hud_invalidate(void){hud_invalid=1;}
void ui_game_init(void){
 u16 i;title_ready=0;hud_invalid=1;
 fps_refresh=vtimer;fps_presentations=pacing_presentations;debug_fps=0;
 VDP_loadTileData(hud_font,TILE_FONT_INDEX,96,DMA);
 for(i=0;i<ARCADE_HUD_TILES;i++)VDP_loadTileData(arcade_hud_patterns+i*8,arcade_hud_slots[i],1,DMA);
 VDP_setWindowVPos(FALSE,0);
}
static void hud_number(u16 *p,u32 value,u8 count,u8 blue,u8 spaces){
 const u16 *digits=arcade_hud_digits+blue*11;
 while(count){p[--count]=digits[value%10];value/=10;if(spaces && !value){while(count)p[--count]=digits[10];break;}}
}
static void hud_icon(u16 *p,const u16 *icon){p[0]=icon[0];p[1]=icon[1];p[32]=icon[2];p[33]=icon[3];}
/* Fixed arcade 5D6D displays remaining layers, not normalized hit points.
   A hit does not change the row until its source layer-transition callback. */
static u8 boss_health(u8 *remaining) {
 u16 i;*remaining=0;
 if(game.mode!=PLAY && game.mode!=PAUSED && game.mode!=DEAD)return 0;
 for(i=0;i<MAX_ACTORS;i++) {
  Actor *a=&game.actors[i];
  u8 boss;
  if(!a->active)continue;
  if(!(boss=actor_boss_class[a->def]))continue;
  if(boss==2 && !boss_primary(i))continue;
  *remaining=a->life;return 1;
 }
 return 0;
}

void ui_hud(void){
 u16 map[256],i,row;u8 hp=game.p.hp>5?5:game.p.hp;
 u8 boss_fill,boss_stage=boss_rush.active?boss_rush.stage:game.round;
 u8 boss_visible=boss_health(&boss_fill);
 if(boss_stage>7)boss_stage=7;
 if(boss_fill>arcade_boss_counts[boss_stage])boss_fill=arcade_boss_counts[boss_stage];
 u8 fps_visible=frontend.debug_active && frontend.debug_framerate;
 if(fps_visible){
  u32 now=vtimer,elapsed=now-fps_refresh;u16 hz=SYS_isPAL()?50:60;
  if(elapsed>=hz){
   u32 frames=pacing_presentations;
   debug_fps=((frames-fps_presentations)*hz+elapsed/2)/elapsed;
   if(debug_fps>hz)debug_fps=hz;
   fps_refresh=now;fps_presentations=frames;
  }
 }
 if(!hud_invalid && hud_credit==frontend.credits && hud_arcade==frontend.mode && hud_boss_present==boss_visible && hud_boss_fill==boss_fill && hud_boss_stage==boss_stage && hud_fps_visible==fps_visible && (!fps_visible || hud_fps==debug_fps) && hud_score==game.score && hud_coins==game.coins && hud_time==game.time &&
    hud_hp==hp && hud_weapon==game.p.weapon && hud_armor==game.p.armor &&
    hud_keys==container_keys && hud_antidotes==shop_antidotes)return;
 hud_credit=frontend.credits;hud_arcade=frontend.mode;
 hud_boss_present=boss_visible;hud_boss_fill=boss_fill;hud_boss_stage=boss_stage;
 hud_fps_visible=fps_visible;hud_fps=debug_fps;
 hud_score=game.score;hud_coins=game.coins;hud_time=game.time;hud_hp=hp;
 hud_weapon=game.p.weapon;hud_armor=game.p.armor;hud_keys=container_keys;hud_antidotes=shop_antidotes;
 if(game.score>high_score)high_score=game.score;
 memcpy(map,arcade_hud_map,5*64);memcpy(map+160,arcade_hud_map+25*32,3*64);
 hud_number(map+32+2,game.score,7,1,1);hud_number(map+32+13,high_score,7,1,1);
 hud_number(map+3*32+1,game.time/60,1,0,0);hud_number(map+3*32+3,game.time%60,2,0,0);
 for(i=0;i<10;i++)map[3*32+7+i]=0;
 for(i=0;i<hp;i++){u8 color=i>1?2:i;map[3*32+7+i*2]=arcade_hud_vital[color*2];map[3*32+8+i*2]=arcade_hud_vital[color*2+1];}
 hud_number(map+4*32+26,game.coins,5,0,0);
 hud_icon(map+160+11,arcade_hud_weapons+(game.p.weapon?game.p.weapon-1:0)*4);
 hud_icon(map+160+15,arcade_hud_armors+(game.p.armor>8?8:game.p.armor)*4);
 hud_number(map+224+7,container_keys,2,0,0);hud_number(map+224+19,shop_antidotes,2,0,0);
 if(boss_visible){
  const u16 *glyphs=arcade_boss_glyphs+arcade_boss_styles[boss_stage]*4;
  /* Original 59BF hides Zenny while the boss row occupies the HUD. */
  for(i=24;i<31;i++)map[3*32+i]=map[4*32+i]=0;
  for(i=0;i<arcade_boss_counts[boss_stage];i++){
   u8 cell=i<boss_fill?0:2;
   map[4*32+7+i*2]=glyphs[cell];map[4*32+8+i*2]=glyphs[cell+1];
  }
 }

 if(fps_visible){
  const char *label="FPS:";
  for(i=0;i<4;i++)map[25+i]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,TILE_FONT_INDEX+label[i]-32);
  map[29]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,TILE_FONT_INDEX+'0'-32+debug_fps/10);
  map[30]=TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,TILE_FONT_INDEX+'0'-32+debug_fps%10);
 }
 if(game.round==3 && game.mode!=SHOP)for(row=0;row<8;row++)map[row*32+31]=748+row;
 for(row=0;row<8;row++)if(hud_invalid || memcmp(map+row*32,hud_previous+row*32,64)){
  memcpy(hud_previous+row*32,map+row*32,64);
  VDP_setTileMapDataRow(BG_A,map+row*32,row<5?row:row+20,0,32,DMA_QUEUE_COPY);
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
 VDP_loadTileData(home_md_tiles,16+TITLE_TILE_COUNT,HOME_MD_TILE_COUNT,DMA);
 VDP_loadTileData(title_version_tiles,16+TITLE_TILE_COUNT+HOME_MD_TILE_COUNT,2,DMA);
 VDP_loadTileData(home_cursor_tiles,HOME_CURSOR_TILE,4,DMA);
 VDP_loadTileData(title_font,TILE_FONT_INDEX,96,DMA);
 VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,DMA);
 VDP_setEnable(TRUE);SYS_enableInts();title_ready=1;title_page=255;
}
void ui_attract_version(void){VDP_loadTileData(title_version_tiles,1278,2,DMA);}
void ui_title(void){
 if(attract_active()){title_ready=0;attract_video();return;}
 static const char *const coinage[]={"4 COINS:1 CR","3 COINS:1 CR","2 COINS:1 CR","1 COIN:1 CR","1 COIN:2 CR","1 COIN:3 CR","1 COIN:4 CR","1 COIN:5 CR"};
 u8 page=frontend.page,home=frontend.mode,message=frontend.message!=0;
 u8 coin_phase=page==1 && !home && !(game.frame&32),page_changed;
 GameSettings *s=&settings[home];
 if(!title_ready)title_load();
 if(title_page==page && title_revision==frontend.revision && title_message==message && title_coin_phase==coin_phase && title_high_score==high_score)return;
 page_changed=title_page!=page;
 if(page_changed){
  DMA_flushQueue();SYS_disableInts();VDP_setEnable(FALSE);
  VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
  if(page!=2 && page!=4 && page!=5 && page!=6)VDP_setTileMapDataRectEx(BG_B,title_map,0,0,0,32,28,32,CPU);
  if(page==1 && home)VDP_setTileMapDataRectEx(BG_B,home_md_map,0,12,13,8,4,8,CPU);
 }
 VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);
 title_page=page;title_revision=frontend.revision;title_message=message;
 title_coin_phase=coin_phase;title_high_score=high_score;
 VDP_setTextPlane(BG_A);VDP_setTextPalette(PAL3);VDP_setTextPriority(TRUE);
 if(page==5 || page==6){
  u8 i;center(3,page==6?"ENTER INITIALS":"HIGH SCORES");
  if(page==5)center(5,high_score_mode==0?"ARCADE":high_score_mode==1?"HOME":"BOSS RUSH");
  draw("RANK NAME    SCORE   MODE",2,6);
  for(i=0;i<HIGH_SCORE_COUNT;i++){
   const HighScoreEntry *entry=&high_scores[i];u8 y=8+i*3;char name[4];
   name[0]=entry->initials[0];name[1]=entry->initials[1];name[2]=entry->initials[2];name[3]=0;
   number(3,y,i+1,1);draw(name,7,y);
   if(entry->score){score_number(11,y,entry->score);draw(entry->mode==2?"RUSH":entry->mode?"HOME":"ARCD",23,y);}
   else{draw("       -",11,y);draw("----",23,y);}
   draw("   ",7,y+1);
   if(page==6 && high_score_pending==i)draw("-",7+high_score_cursor,y+1);
  }
  if(page==6){center(23,"UP / DOWN LETTER");center(25,"A NEXT / CONFIRM");center(27,"B PREVIOUS LETTER");}
  else center(25,"LEFT / RIGHT TABLE   A / B BACK");
 }else if(page==2){
  u8 i,last=home?8:6;static const char *const labels[]={"LIVES","DIFFICULTY","COINAGE","CONTINUE","MUSIC","SOUND FX","CREDITS","LV7 JUMP"};
  center(3,home?"HOME OPTIONS":"DIP SWITCHES");
  for(i=0;i<=last;i++){
   u8 x=i==8?2:i<4?2:18,y=i==8?21:6+(i&3)*4;
   cursor(i==frontend.option,x-2,y);draw(i==last?"BACK":labels[i],x,y);
   VDP_clearTextArea(x,y+1,14,1);
   if(i==last)continue;
   switch(i){
    case 0:number(x,y+1,frontend_lives(),1);break;
    case 1:number(x,y+1,s->difficulty+1,1);break;
    case 2:draw(coinage[s->coinage],x,y+1);break;
    case 3:draw(s->continues?"YES":"NO",x,y+1);break;
    case 4:draw(s->music?"ON":"OFF",x,y+1);break;
    case 5:draw(s->sfx?"ON":"OFF",x,y+1);break;
    case 6:number(x,y+1,s->credits,2);break;
    case 7:draw(frontend.level7_jump_assist?"ASSIST":"ORIGINAL",x,y+1);break;
   }
  }
  center(23,"UP / DOWN SELECT");center(24,"LEFT / RIGHT CHANGE");center(26,"B BACK");
 }else if(page==4){
  u8 i;static const char *const labels[]={"INVINCIBILITY","INFINITE LIVES","INFINITE TIME","FRAMERATE"};
  center(2,"DEBUG");
  for(i=0;i<4;i++){
   u8 x=i<2?2:18,y=5+(i&1)*4;
   u8 value=i==0?frontend.debug_invincible:i==1?frontend.debug_lives:i==2?frontend.debug_time:frontend.debug_framerate;
   cursor(i==frontend.debug_option,x-2,y);draw(labels[i],x,y);
   draw(value?"ON ":"OFF",x,y+1);
  }
  center(12,"START LEVEL");
  for(i=0;i<8;i++){
   u8 x=i<4?2:18,y=14+(i&3)*2;
   cursor(i+4==frontend.debug_option,x-2,y);draw("LEVEL",x,y);number(x+6,y,i+1,1);
  }
  cursor(frontend.debug_option==12,1,23);draw("INFINITE ZENNY",3,23);draw(frontend.debug_zenny?"YES":"NO ",18,23);
  center(25,"A / START SELECT");center(27,"B BACK");
 }else{
  u8 i,count=page==0?3:home?(frontend.debug_unlocked?4:3):2;
  VDP_clearTextArea(0,16,32,9);
  for(i=0;i<count;i++){
   const char *label=page==0?(i==2?"HIGH SCORES":i?"HOME":"ARCADE"):i==0?"PLAY":home?(i==1?"BOSS RUSH":i==2?"OPTIONS":"DEBUG"):"DIP SWITCHES";
   {u8 y=18+i*2;center(y,label);cursor(i==frontend.selected,(32-strlen(label))/2-3,y);}
  }
  if(page==1 && !home && coin_phase)center(23,"INSERT COIN");
  score_number(13,1,high_score);
  center(25,"(C)CAPCOM 1987");center(26,"RESTER159 2026");
  VDP_setTileMapDataRectEx(BG_A,title_version_map,0,0,27,2,1,2,CPU);
  {u8 credit=home && page==1?s->credits:frontend.credits;
   draw("CREDIT",23,27);number(credit>9?30:31,27,credit,credit>9?2:1);}
 }
 VDP_updateSprites(1,DMA_QUEUE);
 if(page_changed){DMA_flushQueue();VDP_setEnable(TRUE);SYS_enableInts();}
}
