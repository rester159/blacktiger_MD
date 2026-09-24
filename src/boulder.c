#include "progress.h"
#include "boulder.h"
#include "assets.h"
typedef struct {AnimState animation;u16 segment;u8 fraction,bounced,damage,pending;} BoulderState;
static BoulderState boulders[MAX_ACTORS];
static void select_segment(BoulderState *s,u16 segment) {
 s8 vx=s->animation.vx,vy=s->animation.vy;animation_reset(&s->animation);
 s->animation.vx=vx;s->animation.vy=vy;s->segment=segment;
}
void boulder_spawn(u16 slot) {
 BoulderState *s=&boulders[slot];animation_reset(&s->animation);
 s->segment=boulder_roots[0];s->fraction=s->bounced=s->pending=0;s->damage=boulder_initial_damage;
}
u8 boulder_damage(u16 slot) {return game.actors[slot].state?0:boulders[slot].damage;}
u8 boulder_hit(u16 slot,u8 damage) {
 Actor *a=&game.actors[slot];if(!boulder_kinds[a->def])return 0;
 if(!a->state) {
  if(a->hp>damage)a->hp-=damage;
  else {a->state=1;boulders[slot].pending=1;progress_score(boulder_weapon_score);}
 }
 return 1;
}
__attribute__((noinline)) static void boulder_transition(u16 slot) {
 Actor *a=&game.actors[slot];BoulderState *s=&boulders[slot];u16 tries;
 if(s->pending){s->pending=0;select_segment(s,boulder_roots[4]);}
 for(tries=0;tries<8;tries++) {
  const BoulderSegment *seg=&boulder_segments[s->segment];u16 target=seg->next[0];
  if(animation_step(&s->animation,seg->clip)) {
   a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;a->y+=a->vy;return;
  }
  switch(seg->event) {
  case 0:
   if((u8)(PX(game.p.x)+64-PX(a->x))<128) {
    s->animation.vy=0;s->fraction=0;game.spawned[a->source]=2;game.sound=SND_ATTACK;target=seg->next[1];
   }
   break;
  case 1: {
   u8 tile=terrain(PX(a->x)+16,PX(a->y)+32);
   if(s->animation.vy>=0 && (tile==2 || tile==3)) {
    if(!s->bounced) {
     s->bounced=1;s->damage=boulder_bounce_damage;s->animation.vy=-3;
     s->animation.vx=(u8)PX(game.p.x)<(u8)PX(a->x)?-1:1;
    } else s->animation.vy=-2;
    s->fraction=0;game.sound=SND_HIT;target=seg->next[1];
   } else {
    u16 v=((u16)(u8)s->animation.vy<<8)+s->fraction+48;
    if((v>>8)==5)v=1280;
    s->animation.vy=v>>8;s->fraction=v&255;
   }
   break;
  }
  case 2:a->state=1;break;
  case 3:a->active=0;if(game.spawned[a->source]!=2)game.spawned[a->source]=0;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *boulder_frame(u16 slot) {
 BoulderState *s=&boulders[slot];return s->animation.remaining?animation_current(&s->animation,boulder_segments[s->segment].clip):0;
}

/* Keep ordinary held-frame motion outside the transition interpreter. */
void boulder_step(u16 slot) {
 BoulderState *s=&boulders[slot];
 if(!s->pending && animation_hold_step(&s->animation,boulder_segments[s->segment].clip)){
  Actor *a=&game.actors[slot];a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;a->y+=a->vy;return;
 }
 boulder_transition(slot);
}
