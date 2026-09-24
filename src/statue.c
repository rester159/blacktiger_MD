#include "statue.h"
#include "assets.h"
#include "loot.h"
#include "progress.h"
#include "statue_shell.h"
#include "sentry.h"
typedef struct {AnimState animation;u16 segment;u8 pending,left,vulnerable,contact;} StatueState;
static StatueState statues[MAX_ACTORS];
static void select_segment(StatueState *s,u16 target) {
 animation_reset(&s->animation);s->segment=target;
}
void statue_spawn(u16 slot) {
 Actor *a=&game.actors[slot];StatueState *s=&statues[slot];
 s->pending=s->left=0;s->vulnerable=s->contact=1;
 a->hp=statue_health;a->life=statue_layers;a->state=0;select_segment(s,statue_roots[0]);
}
u8 statue_contact(u16 slot) {return statues[slot].contact;}
u8 statue_vulnerable(u16 slot) {return statues[slot].vulnerable && !game.actors[slot].state;}
u8 statue_hit(u16 slot,u8 damage) {
 Actor *a=&game.actors[slot];StatueState *s=&statues[slot];
 if(!statue_vulnerable(slot))return 0;
 if(a->hp>damage)a->hp-=damage;
 else {s->pending=1;s->vulnerable=0;a->state=1;}
 return 1;
}

void statue_screen_attack(u16 slot) {
 Actor *a=&game.actors[slot];StatueState *s=&statues[slot];
 if(!a->state){a->life=1;s->pending=1;s->vulnerable=0;a->state=1;}
}
__attribute__((noinline)) static void statue_transition(u16 slot) {
 Actor *a=&game.actors[slot];StatueState *s=&statues[slot];u16 tries;
 if(s->pending){s->pending=0;select_segment(s,statue_roots[9]);}
 for(tries=0;tries<8;tries++) {
  const StatueSegment *seg=&statue_segments[s->segment];u16 target=seg->next;
  if(animation_step(&s->animation,seg->clip))return;
  switch(seg->event) {
  case 0:
   s->left=(u16)PX(a->x)>=(u16)PX(game.p.x);
   target=statue_roots[(statue_choices[(loot_random>>8)&15]?1:3)+s->left];break;
  case 1:
   if(statue_shell_spawn(PX(a->x)+8,PX(a->y)+8,
     aim_direction(PX(a->x)-game.cam_x,PX(a->y)-game.cam_y,PX(game.p.x)-game.cam_x,PX(game.p.y)-game.cam_y)>>1))game.sound=SND_ATTACK;
   break;
  case 3:s->vulnerable=s->contact=1;break;
  case 4:s->vulnerable=0;s->contact=1;break;
  case 5:s->vulnerable=s->contact=0;break;
  case 6:
   if(--a->life) {a->hp=statue_reset_health;a->state=0;target=statue_roots[5+s->left];game.sound=SND_HIT;}
   else {
    a->state=2;s->vulnerable=s->contact=0;target=statue_roots[7+s->left];
    progress_score(statue_score);game.kills++;game.spawned[a->source]=2;
    loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));game.sound=SND_KILL;
   }
   break;
  default:a->active=0;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *statue_frame(u16 slot) {
 StatueState *s=&statues[slot];return s->animation.remaining?animation_current(&s->animation,statue_segments[s->segment].clip):0;
}

/* Keep ordinary held-frame motion outside the transition interpreter. */
void statue_step(u16 slot) {
 StatueState *s=&statues[slot];
 if(!s->pending && animation_hold_step(&s->animation,statue_segments[s->segment].clip)){
  return;
 }
 statue_transition(slot);
}
