#include "statue_shell.h"
#include "assets.h"
/* Both source families use the same shell -> independent medium-blast pipeline.
   Pools stay separate from body actors; original global pool contention is pending. */
StatueShell statue_shells[MAX_STATUE_SHELLS],statue_blasts[MAX_STATUE_SHELLS];
StatueShell hunter_shells[MAX_STATUE_SHELLS],hunter_blasts[MAX_STATUE_SHELLS];
static const AnimSegment *segments(u8 hunter) {return hunter?hunter_segments:statue_segments;}
static const u16 *roots(u8 hunter) {return hunter?hunter_roots:statue_roots;}
static void select_segment(StatueShell *s,u16 segment) {
 animation_reset(&s->animation);s->segment=segment;
}
static u8 spawn(StatueShell *pool,s16 x,s16 y,u16 root,u8 mode,u8 hunter) {
 u16 i;for(i=0;i<MAX_STATUE_SHELLS;i++)if(!pool[i].active) {
  StatueShell *s=&pool[i];s->x=x;s->y=y;s->active=1;s->cycles=s->pending=0;s->mode=mode;
  select_segment(s,roots(hunter)[root]);return 1;
 }return 0;
}
void statue_shell_reset(void) {
 u16 i;for(i=0;i<MAX_STATUE_SHELLS;i++) {
  statue_shells[i].active=statue_blasts[i].active=0;
  hunter_shells[i].active=hunter_blasts[i].active=0;
 }
}
u8 statue_shell_spawn(s16 x,s16 y,u8 direction) {return spawn(statue_shells,x,y,13+(direction&15),8,0);}
u8 hunter_shell_spawn(s16 x,s16 y,u8 direction,u8 boss) {return spawn(hunter_shells,x,y,44+(direction&15),boss?9:8,1);}
static u8 hit(StatueShell *s) {
 if(!s->active || (s->mode&1) || s->pending)return 0;
 s->pending=1;return 1;
}
u8 statue_shell_hit(u16 slot) {return hit(&statue_shells[slot]);}
u8 hunter_shell_hit(u16 slot) {return hit(&hunter_shells[slot]);}
static void contact(StatueShell *s,StatueShell *blasts,u8 hunter) {
 u8 spawned;if(!s->active || (s->mode&2) || s->pending)return;
 spawned=spawn(blasts,PX(game.p.x),PX(game.p.y),11,9,hunter);
 if(hunter)s->pending=2;
 else if(spawned)select_segment(s,statue_roots[12]);
}
void statue_shell_contact(u16 slot) {contact(&statue_shells[slot],statue_blasts,0);}
void hunter_shell_contact(u16 slot) {contact(&hunter_shells[slot],hunter_blasts,1);}
static void step(StatueShell *s,StatueShell *blasts,u8 small,u8 hunter) {
 u16 tries;
 if(s->pending==2){s->active=0;return;}
 if(s->pending){s->pending=0;select_segment(s,roots(hunter)[10]);}
 for(tries=0;tries<8;tries++) {
  const AnimSegment *seg=&segments(hunter)[s->segment];u16 target=seg->next;
  if(animation_tick(&s->animation,seg->clip)) {
   s->x+=s->animation.vx;
   if(small && !small_actor_axis_active(s->x-game.cam_x,0)){s->active=0;return;}
   s->y+=s->animation.vy;
   if(small && !small_actor_axis_active(s->y-game.cam_y,1))s->active=0;
   return;
  }
  if(hunter) {
   switch(seg->event) {
   case 7: {
    u8 tile=terrain(s->x+8,s->y+8);
    if(tile==2 || tile==3 || ++s->cycles==8){s->cycles=0;target=hunter_roots[10];}
    break;
   }
   case 8:spawn(blasts,s->x-8,s->y-16,11,9,1);break;
   default:s->active=0;return;
   }
  }else switch(seg->event) {
   case 2:if(++s->cycles==13){s->mode=11;target=statue_roots[10];}break;
   case 3:s->mode=8;break;
   case 4:s->mode=9;break;
   case 5:s->mode=11;break;
   case 7:
    if(spawn(blasts,s->x-8,s->y-16,11,9,0)){game.sound=SND_KILL;target=statue_roots[12];}
    else {s->pending=1;return;}
    break;
   default:s->active=0;return;
  }
  select_segment(s,target);
 }
}
static u8 tick_pools(StatueShell *shells,StatueShell *blasts,u8 hunter) {
 u8 occupied=0;u16 i;
 for(i=0;i<MAX_STATUE_SHELLS;i++)if(shells[i].active){occupied=1;step(&shells[i],blasts,1,hunter);}
 for(i=0;i<MAX_STATUE_SHELLS;i++)if(blasts[i].active){occupied=1;step(&blasts[i],blasts,0,hunter);}
 return occupied;
}
u8 statue_shell_tick(void) {return tick_pools(statue_shells,statue_blasts,0);}
u8 hunter_shell_tick(void) {return tick_pools(hunter_shells,hunter_blasts,1);}
static const AnimFrame *frame(const StatueShell *s,u8 hunter) {
 return s->active && s->animation.remaining?animation_current(&s->animation,segments(hunter)[s->segment].clip):0;
}
const AnimFrame *statue_shell_frame(const StatueShell *s) {return frame(s,0);}
const AnimFrame *hunter_shell_frame(const StatueShell *s) {return frame(s,1);}
static u8 hit_at(StatueShell *pool,s16 x,s16 y,u8 kind,u8 hunter) {
 u16 i;u8 w=(kind?dagger_width:8)+(hunter?2:4),h=(kind?dagger_height:4)+(hunter?2:4);
 if(kind && (game.frame&1))return 0;
 for(i=0;i<MAX_STATUE_SHELLS;i++) {
  StatueShell *s=&pool[i];s16 dx,dy;
  if(!s->active || (s->mode&1) || s->pending)continue;
  dx=x-s->x;dy=y-s->y;
  if(dx>=-w && dx<=w && dy>=-h && dy<=h && hit(s))return 1;
 }return 0;
}
u8 statue_shell_hit_at(s16 x,s16 y,u8 kind) {return hit_at(statue_shells,x,y,kind,0);}
u8 hunter_shell_hit_at(s16 x,s16 y,u8 kind) {return hit_at(hunter_shells,x,y,kind,1);}
static u8 player_contact(StatueShell *s,u8 blast,u8 hunter) {
 s16 dx,dy,w,h;
 if(!s->active || (s->mode&2) || s->pending || (game.frame&1)!=blast)return 0;
 dx=PX(game.p.x)+(blast?0:8)-s->x;dy=PX(game.p.y)+(blast?0:8)+(game.player_low?10:0)-s->y;
 w=(game.player_low?3:blast?12:hunter?2:4)+contact_player_width;h=(game.player_low?3:blast?(hunter?12:10):hunter?2:4)+contact_player_height;
 return dx>=-w && dx<=w && dy>=-h && dy<=h;
}
u8 statue_shell_player_contact(u16 slot,u8 blast) {return player_contact(blast?&statue_blasts[slot]:&statue_shells[slot],blast,0);}
u8 hunter_shell_player_contact(u16 slot,u8 blast) {return player_contact(blast?&hunter_blasts[slot]:&hunter_shells[slot],blast,1);}
