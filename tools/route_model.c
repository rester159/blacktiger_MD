#include "player_motion.h"
#include "bonus.h"
#include "assets.h"
#include "route_data.inc"
Game game;PlayerMotion player_motion;
typedef struct {PlayerMotion p;u16 saved_x,saved_y;u8 entered,consumed,clock,phases[4];} RouteState;
static u8 cells[8192];static int width,height;
#include "route_contact.inc"
u8 terrain(s16 x,s16 y){if(x<0 || x>=width || y<0)return 3;if(y>=height)return 0;u16 cell=(y/16)*(width/16)+x/16;return bonus_collision(cell,cells[cell]);}
int state_size(void){return sizeof(RouteState);}
void setup(const u8 *map,int w,int h,int level){width=w;height=h;game.round=level;for(int i=0;i<8192;i++)cells[i]=map[i];bonus_reset(0);}
void start(RouteState *s,int x,int y){*s=(RouteState){0};s->p=(PlayerMotion){.scroll_x=x-128,.scroll_y=y-144,.screen_x=128,.screen_y=144};}
int advance(RouteState *s,int input,int ticks){
 player_motion=s->p;bonus_entered=s->entered;bonus_consumed=s->consumed;bonus_clock=s->clock;bonus_saved_x=s->saved_x;bonus_saved_y=s->saved_y;for(int i=0;i<4;i++)bonus_phases[i]=s->phases[i];
 for(int i=0;i<ticks;i++){
  bonus_tick();player_motion_step(&player_motion,input,0);
  int x=(s16)(player_motion.scroll_x+player_motion.screen_x),y=(s16)(player_motion.scroll_y+player_motion.screen_y);
  if(x<0 || x>width-32 || y<0 || y>=height)return 0;
  game.p.x=x*256;game.p.y=y*256;game.player_low=player_motion.low && !player_motion.jumping;
  if(bonus_contact()){
   u16 x=player_motion.scroll_x,y=player_motion.scroll_y;
   bonus_destination(game.round,bonus_entered,&x,&y,&bonus_saved_x,&bonus_saved_y);
   bonus_entered=1;bonus_animation_reset();player_motion.scroll_x=x;player_motion.scroll_y=y;
  }
 }
 s->p=player_motion;s->entered=bonus_entered;s->consumed=bonus_consumed;s->clock=bonus_clock;s->saved_x=bonus_saved_x;s->saved_y=bonus_saved_y;for(int i=0;i<4;i++)s->phases[i]=bonus_phases[i];return 1;
}
