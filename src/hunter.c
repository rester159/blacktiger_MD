#include "hunter.h"
#include "assets.h"
#include "progress.h"
#include "loot.h"
#include "sentry.h"
typedef struct {AnimState animation;u16 segment;u8 mode,pending,boss,direction;} HunterState;
static HunterState hunters[MAX_ACTORS];
static void select_segment(HunterState *s,u16 segment) {
 s8 vx=s->animation.vx,vy=s->animation.vy;animation_reset(&s->animation);
 s->animation.vx=vx;s->animation.vy=vy;s->segment=segment;
}
void hunter_spawn(u16 slot,u8 boss) {
 Actor *a=&game.actors[slot];HunterState *s=&hunters[slot];
 animation_reset(&s->animation);s->boss=boss;s->mode=boss?26:10;s->pending=s->direction=0;
 a->hp=hunter_health[boss];a->life=hunter_layers[boss];a->state=0;select_segment(s,hunter_roots[boss]);
}
u8 hunter_vulnerable(u16 slot) {return !(hunters[slot].mode&1) && !game.actors[slot].state;}
u8 hunter_hit(u16 slot,u8 damage) {
 Actor *a=&game.actors[slot];HunterState *s=&hunters[slot];
 if(!hunter_vulnerable(slot))return 0;
 if(a->hp>damage)a->hp-=damage;
 else {s->pending=1;s->mode|=3;a->state=1;}
 return 1;
}
static u16 choose(Actor *a,HunterState *s) {
 s16 x=PX(a->x)-game.cam_x,y=PX(a->y)-game.cam_y;u8 choice,angle;
 if((u16)x>>8)return hunter_roots[((u16)x>>8)==255?7:6];
 if((u16)y>>8)return hunter_roots[((u16)y>>8)==255?8:9];
 choice=hunter_choices[(loot_random>>8)&15];
 s->direction=aim_direction(x,y,PX(game.p.x)-game.cam_x,PX(game.p.y)-game.cam_y);
 angle=s->direction>>1;
 if(!choice)return hunter_roots[28+angle];
 angle=(angle+3-choice)&15;return hunter_roots[12+angle];
}
/* Body kernel; projectile and boss presentation hooks must precede gameplay dispatch. */
void hunter_step(u16 slot) {
 Actor *a=&game.actors[slot];HunterState *s=&hunters[slot];u16 tries;
 if(s->pending){s->pending=0;select_segment(s,hunter_roots[2+s->boss]);}
 for(tries=0;tries<8;tries++) {
  const HunterSegment *seg=&hunter_segments[s->segment];u16 target=seg->next;
  if(animation_tick(&s->animation,seg->clip)) {
   a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;a->y+=a->vy;return;
  }
  switch(seg->event) {
  case 0:s->mode=(s->mode|11)^3;break;
  case 1:s->mode|=11;break;
  case 2:if((u8)(PX(game.p.x)+80-PX(a->x))<160)target=hunter_roots[5];break;
  case 3:target=choose(a,s);break;
  case 4:case 5:
   if(--a->life) {
    a->hp=hunter_reset_health[s->boss];a->state=0;if(s->boss)s->mode&=24;
    target=hunter_roots[4];game.sound=SND_HIT;
   }else {
    a->state=2;progress_score(hunter_score);game.spawned[a->source]|=2;game.kills++;game.sound=SND_KILL;
    if(!s->boss)loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));
   }break;
  case 6:game.sound=SND_ATTACK;break;
  default:a->active=0;game.spawned[a->source]&=254;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *hunter_frame(u16 slot) {
 HunterState *s=&hunters[slot];return s->animation.remaining?animation_current(&s->animation,hunter_segments[s->segment].clip):0;
}
