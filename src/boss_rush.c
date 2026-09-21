#include "boss_rush.h"
#include "assets.h"
#include "boss.h"
#include "hunter.h"
#include "waveboss.h"
#include "dragon.h"
#include "music.h"
#include "progress.h"
#include "ending.h"
BossRush boss_rush;
/* Boss definitions in arcade round order, reusing their complete native routines. */
static const u8 roster[]={15,25,39,44,49,55,62,65};
void boss_rush_prepare(void){
 Actor *a=&game.actors[0];u16 i;
 for(i=0;i<160;i++)game.spawned[i]=2;
 game.cam_x=RUSH_CAMERA_X;game.cam_y=RUSH_Y;game.time=180;
 game.p.x=RUSH_START_X*FX;game.p.y=(RUSH_FLOOR-32)*FX;
 game.p.vx=game.p.vy=0;game.p.climb=0;game.p.grounded=1;game.p.face=0;
 game.p.hp=progress_max_hp;game.p.invincible=120;
 a->active=1;a->source=159;a->def=roster[boss_rush.stage];a->hp=actor_defs[a->def].hp;
 a->face=-1;a->x=(RUSH_START_X+(dragon_kinds[a->def]?72:136))*FX;
 a->y=(RUSH_FLOOR-(dragon_kinds[a->def]?96:waveboss_kinds[a->def]?64:32))*FX;
 if(layered_boss_kinds[a->def])boss_spawn(0);
 else if(hunter_kinds[a->def])hunter_spawn(0,1);
 else if(waveboss_kinds[a->def])waveboss_spawn(0);
 else dragon_spawn(0,dragon_kinds[a->def]-1);
 music_request=music_boss_commands[boss_rush.stage];boss_rush.shopping=0;
}
void boss_rush_win(void){
 u32 total;if(boss_rush.shopping)return;
 boss_rush.shopping=1;boss_rush.reward=1000+500*boss_rush.stage;
 total=(u32)game.coins+boss_rush.reward;game.coins=total>65535?65535:total;
 game.p.hp=progress_max_hp;game.mode=SHOP;game.shop_item=0;game.previous_input=0;
}
void boss_rush_shop_exit(void){
 if(!boss_rush.active || !boss_rush.shopping)return;
 if(++boss_rush.stage==8){boss_rush.active=0;boss_rush.complete=1;game.mode=ENDING;ending_start();ending_step();}
 else game_round(7);
}

/* Arcade steering uses an 8-bit viewport. In the wider Home arena, distant
   bosses continue their animation but travel toward the player in world space.
   Clamp live bodies to the hall, not to the scrolling camera. */
void boss_rush_actor_bounds(Actor *a,s32 previous_x){
 u8 dragon=dragon_kinds[a->def],wave=waveboss_kinds[a->def],hunter=hunter_kinds[a->def]==2;
 s16 width=dragon?128:wave?64:32,height=dragon || wave?64:32;
 s32 left=RUSH_X*FX,right=(RUSH_X+RUSH_WIDTH-width)*FX;
 if(!a->active || a->state==2 || !(dragon || wave || hunter || layered_boss_kinds[a->def]))return;
 if(game.p.x-previous_x>224*FX)a->x=previous_x+2*FX;
 else if(previous_x-game.p.x>224*FX)a->x=previous_x-2*FX;
 if(a->x<left)a->x=left;
 if(a->x>right)a->x=right;
 /* The two-legged wave bosses walk; their 64-pixel art reaches row 63. */
 if(wave){a->y=(RUSH_FLOOR-64)*FX;a->vy=0;}
 else if(dragon || hunter){
  s32 top=(RUSH_Y+8)*FX,bottom=(RUSH_FLOOR-height)*FX;
  if(a->y<top)a->y=top;
  if(a->y>bottom)a->y=bottom;
 }
}
