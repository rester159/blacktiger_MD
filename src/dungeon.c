#include "dungeon.h"
#include "frontend.h"
#include "progress.h"
#include "loot.h"
#include "music.h"
Dungeon dungeon;
/* M1 baseline: sixteen explicit source-layout entries, replaced by verified
   chunk assembly at M4. These remain the mandatory generation fallbacks. */
const u8 dungeon_fallback_stages[16]={0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7};
const u16 dungeon_act_drain[4]={256,333,435,563};
static u32 seed_entropy=0x42544c48;
#define CLOCK_UNIT 15360UL
#define CLOCK_CAP (600UL*CLOCK_UNIT)
u32 dungeon_rng(u32 *state){u32 x=*state;if(!x)x=0x6d2b79f5;x^=x<<13;x^=x>>17;x^=x<<5;return *state=x;}
u32 dungeon_mix(u32 seed,u32 tag){u32 x=seed^tag^0x9e3779b9;dungeon_rng(&x);x+=0x7f4a7c15;return dungeon_rng(&x);}
void dungeon_seed(u32 seed){
 static const u32 tags[]={0x4c415954,0x454e4d59,0x42494f4d,0x4d4f4452,0x41464658,0x57495345,0x52454c43,0x44524f50};u8 i;
 dungeon.seed=seed&0x3fffffff;for(i=0;i<8;i++)dungeon.streams[i]=dungeon_mix(dungeon.seed,tags[i]);
}
u16 dungeon_seconds(void){
 static u32 floor,ceiling;static u16 seconds;
 if(dungeon.clock>floor && dungeon.clock<=ceiling)return seconds;
 seconds=(dungeon.clock+CLOCK_UNIT-1)/CLOCK_UNIT;
 ceiling=(u32)seconds*CLOCK_UNIT;floor=seconds?ceiling-CLOCK_UNIT:0;return seconds;
}
void dungeon_reward(u16 seconds){u32 sum=dungeon.clock+(u32)seconds*CLOCK_UNIT;dungeon.clock=sum>CLOCK_CAP?CLOCK_CAP:sum;}
u8 dungeon_spend(u16 seconds){u32 cost=(u32)seconds*CLOCK_UNIT;if(dungeon.clock<=cost){dungeon.clock=0;return 0;}dungeon.clock-=cost;return 1;}
void dungeon_open(void){
 u32 bank=dungeon.banked_xp;u8 rank=dungeon.rank?dungeon.rank:1;
 seed_entropy=dungeon_mix(seed_entropy,game.frame);dungeon=(Dungeon){.active=1,.phase=D_SETUP,.banked_xp=bank,.rank=rank,.revision=1};
 dungeon_seed(seed_entropy);game.mode=DUNGEON_MENU;dungeon_ui_reset();
}
void dungeon_start(u32 seed){
 u32 bank=dungeon.banked_xp;u8 rank=dungeon.rank?dungeon.rank:1;
 game_new();game.frame=0;game.p.lives=99;
 dungeon=(Dungeon){.active=1,.phase=D_STAGE_INTRO,.stage=1,.max_hp=8,.charges=1,.clock=180UL*CLOCK_UNIT,.banked_xp=bank,.rank=rank,.timer=150,.revision=1};
 dungeon_seed(seed);loot_random=(u16)dungeon.streams[7];progress_max_hp=8;game.p.hp=8;
 game.mode=DUNGEON_MENU;dungeon_ui_reset();
}
void dungeon_results(u8 victory){
 dungeon.cleared=victory;dungeon.phase=D_RESULTS;dungeon.freeze=0;
 dungeon.score=(u32)dungeon.stage*10000UL+(u32)dungeon.kills*25UL+(u32)dungeon_seconds()*100UL+(victory?50000UL:0);
 if(!dungeon.banked){dungeon.banked_xp+=dungeon.run_xp;dungeon.banked=1;}
 dungeon.revision++;game.mode=DUNGEON_MENU;dungeon_ui_reset();
}
u8 dungeon_tick(u16 input,u16 pressed){
 if(!dungeon.active)return 0;
 switch(dungeon.phase){
 case D_SETUP:
  seed_entropy=dungeon_mix(seed_entropy,game.frame);
  if(pressed&IN_JUMP){dungeon.active=0;game.mode=TITLE;frontend_return();return 1;}
  if(pressed&IN_START){u32 seed=dungeon.seed;dungeon_start(seed);game.previous_input=input;}
  return 1;
 case D_STAGE_INTRO:
  if(dungeon.timer)--dungeon.timer;
  if(!dungeon.timer){
   progress_max_hp=dungeon.max_hp;game_round(dungeon_fallback_stages[dungeon.stage-1]);
   game.p.lives=99;game.previous_input=input;dungeon.phase=D_STAGE_PLAY;
   dungeon.last_kills=game.kills;dungeon.scene_reload=1;dungeon.revision++;dungeon_ui_reset();
  }
  return 1;
 case D_GATE:
  if(pressed&IN_UP)dungeon.boon=(dungeon.boon+2)%3;
  if(pressed&IN_DOWN)dungeon.boon=(dungeon.boon+1)%3;
  if(pressed&(IN_UP|IN_DOWN))dungeon.revision++;
  if(pressed&IN_START){
   if(!dungeon.boon){dungeon.max_hp+=2;if(dungeon.max_hp>16)dungeon.max_hp=16;}
   else if(dungeon.boon==1)dungeon_reward(60);
   else {u32 coins=(u32)game.coins+15000;game.coins=coins>65535?65535:coins;}
   dungeon.stage++;dungeon.phase=D_STAGE_INTRO;dungeon.timer=150;dungeon.revision++;dungeon_ui_reset();
  }
  return 1;
 case D_RESULTS:
  if(pressed&IN_START){dungeon_open();game.previous_input=input;}
  if(pressed&IN_JUMP){dungeon.active=0;game.mode=TITLE;frontend_return();}
  return 1;
 default:break;
 }
 if(game.kills!=dungeon.last_kills){
  u16 kills=game.kills-dungeon.last_kills;dungeon.last_kills=game.kills;
  dungeon.kills+=kills;dungeon.run_xp+=kills;dungeon_reward(kills*3);dungeon.revision++;
 }
 if(game.mode==CLEAR){
  dungeon_reward(45);
  if(dungeon.stage==16){dungeon_reward(300);dungeon_results(1);return 1;}
  if(!(dungeon.stage&3))dungeon_reward(90);else if((dungeon.stage&3)==2)dungeon_reward(60);
  dungeon.phase=D_GATE;dungeon.boon=0;game.mode=DUNGEON_MENU;dungeon.revision++;dungeon_ui_reset();return 1;
 }
 if(game.mode==DEAD && dungeon.phase!=D_DEATH){
  game.p.lives=2;dungeon.deaths++;dungeon.phase=D_DEATH;dungeon.freeze=0;dungeon.revision++;
  if(!dungeon_spend(60)){dungeon_results(0);return 1;}
 }
 if(game.mode==PLAY){
  if(dungeon.phase==D_DEATH){dungeon.phase=D_STAGE_PLAY;dungeon.scene_reload=1;}
  if(pressed&IN_START)return 0;
  if((pressed&IN_HOURGLASS) && dungeon.charges && !dungeon.freeze){dungeon.charges--;dungeon.freeze=300;dungeon.revision++;}
  if(dungeon.freeze)dungeon.freeze--;
  else {
   u16 drain=dungeon_act_drain[(dungeon.stage-1)>>2];
   if(dungeon.clock<=drain){dungeon.clock=0;dungeon_results(0);return 1;}
   dungeon.clock-=drain;
  }
 }
 /* The run clock supersedes the ordinary per-round timer. */
 game.time=600;game.clock=0;
 return 0;
}
