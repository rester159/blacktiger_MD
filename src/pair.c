#include "progress.h"
#include "pair.h"
#include "assets.h"
#include "loot.h"
#include "sentry.h"
typedef struct {AnimState animation;u16 segment;u8 cycles,vulnerable,pending;} PairState;
static PairState pairs[MAX_ACTORS];
static void select_segment(PairState *s,u16 segment) {
 s8 vx=s->animation.vx,vy=s->animation.vy;animation_reset(&s->animation);
 s->animation.vx=vx;s->animation.vy=vy;s->segment=segment;
}
u8 pair_ready(s16 x,s16 y) {
 u16 i,free=0;
 if((u16)(x-game.cam_x)>=256 || (u16)(y-game.cam_y)>=256)return 0;
 if((u8)(PX(game.p.x)+64-x)>=128 || (u8)(PX(game.p.y)+64-y)>=128)return 0;
 for(i=0;i<MAX_ACTORS;i++)if(!game.actors[i].active)free++;
 return free>=2;
}
static void init(u16 slot,u8 part) {
 PairState *s=&pairs[slot];animation_reset(&s->animation);s->segment=pair_roots[part];s->cycles=s->vulnerable=s->pending=0;
}
void pair_spawn(u16 slot) {
 u16 i;init(slot,0);
 for(i=0;i<MAX_ACTORS;i++)if(!game.actors[i].active) {
  game.actors[i]=game.actors[slot];init(i,1);break;
 }
}
u8 pair_vulnerable(u16 slot){return pairs[slot].vulnerable && !game.actors[slot].state;}
u8 pair_hit(u16 slot,u8 damage) {
 Actor *a=&game.actors[slot];if(!pair_kinds[a->def])return 0;
 if(!a->state) {
  if(a->hp>damage)a->hp-=damage;
  else {a->state=1;pairs[slot].pending=1;progress_score(pair_score);game.kills++;}
 }
 return 1;
}
void pair_step(u16 slot) {
 Actor *a=&game.actors[slot];PairState *s=&pairs[slot];u16 tries;
 if(s->pending){s->pending=0;select_segment(s,pair_roots[2]);}
 for(tries=0;tries<8;tries++) {
  const PairSegment *seg=&pair_segments[s->segment];u16 target=seg->next;
  if(animation_tick(&s->animation,seg->clip)) {
   a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;
   if(!small_actor_axis_active(PX(a->x)-game.cam_x,0)){a->active=0;return;}
   a->y+=a->vy;
   if(!small_actor_axis_active(PX(a->y)-game.cam_y,1))a->active=0;
   return;
  }
  switch(seg->event) {
  case 0:s->vulnerable=1;
  /* fall through */
  case 1:
   if(++s->cycles==16)target=pair_roots[20+((loot_random>>8)&7)];
   else {
    u8 action=pair_choices[(loot_random>>8)&15];
    if(!action)target=pair_roots[3];
    else {
     static const s8 offset[]={0,0,-1,-2,1,2};
     u8 angle=aim_direction(PX(a->x)-game.cam_x,PX(a->y)-game.cam_y,PX(game.p.x)-game.cam_x,PX(game.p.y)-game.cam_y);
     target=pair_roots[4+(((angle>>1)+offset[action])&15)];
    }
   }
   break;
  case 2:game.sound=SND_KILL;break;
  default:a->active=0;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *pair_frame(u16 slot) {
 PairState *s=&pairs[slot];return s->animation.remaining?animation_current(&s->animation,pair_segments[s->segment].clip):0;
}
