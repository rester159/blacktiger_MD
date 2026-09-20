#include "statue_shell.h"
#include "assets.h"
StatueShell statue_shells[MAX_STATUE_SHELLS],statue_blasts[MAX_STATUE_SHELLS];
static void select_segment(StatueShell *s,u16 segment) {
 animation_reset(&s->animation);s->segment=segment;
}
static u8 spawn(StatueShell *pool,s16 x,s16 y,u16 root,u8 mode) {
 u16 i;for(i=0;i<MAX_STATUE_SHELLS;i++)if(!pool[i].active) {
  StatueShell *s=&pool[i];s->x=x;s->y=y;s->active=1;s->cycles=s->pending=0;s->mode=mode;
  select_segment(s,statue_roots[root]);return 1;
 }return 0;
}
void statue_shell_reset(void) {
 u16 i;for(i=0;i<MAX_STATUE_SHELLS;i++)statue_shells[i].active=statue_blasts[i].active=0;
}
u8 statue_shell_spawn(s16 x,s16 y,u8 direction) {return spawn(statue_shells,x,y,13+(direction&15),8);}
u8 statue_shell_hit(u16 slot) {
 StatueShell *s=&statue_shells[slot];if(!s->active || (s->mode&1) || s->pending)return 0;
 s->pending=1;return 1;
}
void statue_shell_contact(u16 slot) {
 StatueShell *s=&statue_shells[slot];if(!s->active || (s->mode&2) || s->pending)return;
 if(spawn(statue_blasts,PX(game.p.x),PX(game.p.y),11,9))select_segment(s,statue_roots[12]);
}
static void step(StatueShell *s,u8 small) {
 u16 tries;
 if(s->pending){s->pending=0;select_segment(s,statue_roots[10]);}
 for(tries=0;tries<8;tries++) {
  const StatueSegment *seg=&statue_segments[s->segment];u16 target=seg->next;
  if(animation_tick(&s->animation,seg->clip)) {
   s->x+=s->animation.vx;
   if(small && !small_actor_axis_active(s->x-game.cam_x,0)){s->active=0;return;}
   s->y+=s->animation.vy;
   if(small && !small_actor_axis_active(s->y-game.cam_y,1))s->active=0;
   return;
  }
  switch(seg->event) {
  case 2:if(++s->cycles==13){s->mode=11;target=statue_roots[10];}break;
  case 3:s->mode=8;break;
  case 4:s->mode=9;break;
  case 5:s->mode=11;break;
  case 7:
   if(spawn(statue_blasts,s->x-8,s->y-16,11,9)){game.sound=SND_KILL;target=statue_roots[12];}
   else {s->pending=1;return;}
   break;
  default:s->active=0;return;
  }
  select_segment(s,target);
 }
}
void statue_shell_tick(void) {
 u16 i;for(i=0;i<MAX_STATUE_SHELLS;i++)if(statue_shells[i].active)step(&statue_shells[i],1);
 for(i=0;i<MAX_STATUE_SHELLS;i++)if(statue_blasts[i].active)step(&statue_blasts[i],0);
}
const AnimFrame *statue_shell_frame(const StatueShell *s) {
 return s->active && s->animation.remaining?animation_current(&s->animation,statue_segments[s->segment].clip):0;
}
u8 statue_shell_hit_at(s16 x,s16 y,u8 kind) {
 u16 i;u8 w=kind?dagger_width:4,h=kind?dagger_height:4;
 if(kind && (game.frame&1))return 0;
 for(i=0;i<MAX_STATUE_SHELLS;i++) {
  StatueShell *s=&statue_shells[i];s16 dx=x-s->x,dy=y-s->y;
  if(dx>=-(w+4) && dx<=w+4 && dy>=-(h+4) && dy<=h+4 && statue_shell_hit(i))return 1;
 }return 0;
}
u8 statue_shell_player_contact(u16 slot,u8 blast) {
 StatueShell *s=blast?&statue_blasts[slot]:&statue_shells[slot];s16 dx,dy,w,h;
 if(!s->active || (s->mode&2) || s->pending || (game.frame&1)!=blast)return 0;
 dx=PX(game.p.x)+(blast?0:8)-s->x;dy=PX(game.p.y)+(blast?0:8)-s->y;
 w=(blast?12:4)+contact_player_width;h=(blast?10:4)+contact_player_height;
 return dx>=-w && dx<=w && dy>=-h && dy<=h;
}
