#include "crawler.h"
#include "assets.h"
#include "progress.h"
#include "loot.h"
typedef struct {AnimState animation;u16 segment;u8 fraction,left,mode,pending;} CrawlerState;
static CrawlerState crawlers[MAX_ACTORS];
static const u16 *roots(Actor *a) {return crawler_roots+13*(crawler_kinds[a->def]-1);}
static void select_segment(CrawlerState *s,u16 target) {
 s8 vx=s->animation.vx,vy=s->animation.vy;animation_reset(&s->animation);
 s->animation.vx=vx;s->animation.vy=vy;s->segment=target;
}
void crawler_spawn(u16 slot,u8 part) {
 Actor *a=&game.actors[slot];CrawlerState *s=&crawlers[slot];
 animation_reset(&s->animation);s->fraction=s->left=s->pending=0;s->mode=part?8:11;
 a->hp=1;a->life=crawler_health[crawler_kinds[a->def]-1];a->state=0;select_segment(s,roots(a)[part?9+part:0]);
}
u8 crawler_vulnerable(u16 slot) {return !(crawlers[slot].mode&1) && !game.actors[slot].state;}
u8 crawler_contact(u16 slot) {return !(crawlers[slot].mode&2) && !game.actors[slot].state;}
u8 crawler_hit(u16 slot,u8 damage) {
 CrawlerState *s=&crawlers[slot];Actor *a=&game.actors[slot];
 if(!crawler_vulnerable(slot) || !damage)return 0;
 s->pending=damage;s->mode=11;a->state=1;return 1;
}
void crawler_screen_attack(u16 slot) {
 Actor *a=&game.actors[slot];CrawlerState *s=&crawlers[slot];
 if(!a->state){a->life=1;s->pending=200;s->mode=11;a->state=1;}
}
static u8 ground(Actor *a,s16 x,s16 y) {u8 t=terrain(PX(a->x)+x,PX(a->y)+y);return t==2 || t==3;}
static void gravity(CrawlerState *s) {
 u16 v=((u16)(u8)s->animation.vy<<8)+s->fraction+64;if((v>>8)==5)v=1280;
 s->fraction=v;s->animation.vy=v>>8;
}
static u16 choose(Actor *a,CrawlerState *s) {
 u8 choice=crawler_choices[(loot_random>>8)&15],left=s->left;
 if(choice<2)return roots(a)[(choice==0?left:!left)?4:5];
 s->animation.vy=-3;s->fraction=0;
 if(choice==2 && !ground(a,8,0))return crawler_jump_roots[2];
 if(choice==4 && !ground(a,8,0))left=!left;
 return crawler_jump_roots[left?0:1];
}
static u16 face(Actor *a,CrawlerState *s) {
 s->left=(u16)PX(a->x)>=(u16)PX(game.p.x);return crawler_kinds[a->def]==4?choose(a,s):roots(a)[s->left?4:5];
}
__attribute__((noinline)) static void crawler_transition(u16 slot) {
 Actor *a=&game.actors[slot];CrawlerState *s=&crawlers[slot];u16 tries;
 if(s->pending) {
  u8 damage=s->pending;s->pending=0;
  if(a->life>damage){a->life-=damage;a->state=1;select_segment(s,roots(a)[8]);game.sound=SND_HIT;}
  else {a->state=2;select_segment(s,roots(a)[9]);progress_score(crawler_scores[crawler_kinds[a->def]-1]);game.kills++;game.sound=SND_KILL;}
 }
 for(tries=0;tries<8;tries++) {
  const CrawlerSegment *seg=&crawler_segments[s->segment];u16 target=seg->next;
  if(animation_step(&s->animation,seg->clip)) {
   a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;actor_motion(a,a->vx,a->vy,8);return;
  }
  switch(seg->event) {
  case 0:target=roots(a)[(u16)(PX(a->x)-game.cam_x)<256 && (u8)(PX(game.p.x)+80-PX(a->x))<160?1:0];break;
  case 1:game.spawned[a->source]|=2;
  case 2:if(!ground(a,8,16)){gravity(s);target=roots(a)[2];}break;
  case 3: {
   u16 i;u8 part=1;for(i=0;i<MAX_ACTORS && part<3;i++)if(!game.actors[i].active) {
    game.actors[i]=*a;crawler_spawn(i,part++);
   }
   target=roots(a)[3];break;
  }
  case 4:
   s->mode=8;
   /* A spent body must finish its hit/death sequence. Following the normal
      terrain/jump branch here can leave a moving, permanently harmless ghost. */
   if(a->state)target=roots(a)[9];
   break;
  case 5:
   if(!ground(a,8,16)) {
    s->animation.vx=s->animation.vy=s->fraction=0;gravity(s);target=roots(a)[7];
   }else if(ground(a,crawler_kinds[a->def]==4?8:s->left?0:16,8))target=roots(a)[6];
   break;
  case 6:target=face(a,s);break;
  case 7:if(ground(a,8,16))target=face(a,s);else{gravity(s);target=roots(a)[7];}break;
  case 10:target=choose(a,s);break;
  case 11:if(ground(a,8,16))target=crawler_jump_roots[3];else gravity(s);break;
  default:a->active=0;game.spawned[a->source]&=254;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *crawler_frame(u16 slot) {
 CrawlerState *s=&crawlers[slot];return s->animation.remaining?animation_current(&s->animation,crawler_segments[s->segment].clip):0;
}

/* Held frames avoid the transition interpreter's large register frame. */
void crawler_step(u16 slot) {
 CrawlerState *s=&crawlers[slot];
 if(!s->pending && animation_hold_step(&s->animation,crawler_segments[s->segment].clip)) {
  Actor *a=&game.actors[slot];a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;
  actor_motion(a,a->vx,(s16)s->animation.vy*FX,8);return;
 }
 crawler_transition(slot);
}
