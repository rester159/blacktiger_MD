#include "progress.h"
#include "zombie.h"
#include "assets.h"
#include "loot.h"
#include "missile.h"
#include "sentry.h"
typedef struct {AnimState animation;u16 segment;u8 left,cycles,fraction,vulnerable,pending,thrown;} ZombieState;
static ZombieState zombies[MAX_ACTORS];
static u8 spawn_delay[160];
void zombie_reset(void) {u16 i;for(i=0;i<160;i++)spawn_delay[i]=0;}
u8 zombie_prepare(u16 row,s16 *x,s16 *y) {return zombie_prepare_variant(row,0,x,y);}
u8 zombie_prepare_variant(u16 row,u8 variant,s16 *x,s16 *y) {
 u16 i;u8 count=0;
 if (++spawn_delay[row]!=30) return 0;
 spawn_delay[row]=0;
 for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && zombie_kinds[game.actors[i].def]==variant+1)count++;
 if(count>=3)return 0;
 *x=game.cam_x+(variant==2?spitter_spawn_x:variant?thrower_spawn_x:zombie_spawn_x)[(loot_random>>9)&7];*y=game.cam_y+112;
 for(i=0;i<5;i++,*y+=16) {u8 t=terrain(*x+16,*y+32);if(t==2 || t==3)return 1;}
 return 0;
}
static u8 variant(u16 slot) {return zombie_kinds[game.actors[slot].def]-1;}
static u16 root(u16 slot,u8 index) {return (variant(slot)==2?spitter_roots:variant(slot)?thrower_roots:zombie_roots)[index];}
static const SkeletonSegment *segment(u16 slot) {return &(variant(slot)==2?spitter_segments:variant(slot)?thrower_segments:zombie_segments)[zombies[slot].segment];}
static u8 ground(u16 slot,s16 dx,s16 dy) {
 Actor *a=&game.actors[slot];u8 t=terrain(PX(a->x)+dx,PX(a->y)+dy);
 return t==2 || t==3;
}
static void select_segment(ZombieState *s,u16 segment) {
 s8 vx=s->animation.vx,vy=s->animation.vy;
 animation_reset(&s->animation);s->animation.vx=vx;s->animation.vy=vy;s->segment=segment;
}
void zombie_spawn(u16 slot) {
 ZombieState *s=&zombies[slot];animation_reset(&s->animation);s->segment=root(slot,0);
 s->left=s->fraction=s->vulnerable=s->pending=s->thrown=0;s->cycles=variant(slot)==2?spitter_lifetime:variant(slot)?thrower_lifetime:zombie_lifetime;
 game.actors[slot].state=0;game.actors[slot].hp=variant(slot)==2?spitter_health:variant(slot)?thrower_health:1;
}
u8 zombie_vulnerable(u16 slot) {return zombies[slot].vulnerable && !game.actors[slot].state;}
u8 zombie_hit(u16 slot,u8 damage) {
 Actor *a=&game.actors[slot];
 if (!zombie_kinds[a->def]) return 0;
 if (!a->state && damage>=a->hp) {a->state=1;zombies[slot].pending=1;zombies[slot].vulnerable=0;progress_score(variant(slot)==2?spitter_score:variant(slot)?thrower_score:zombie_score);}
 else if(!a->state && a->hp>damage)a->hp-=damage;
 return 1;
}
static u16 face(u16 slot,u8 choose) {
 ZombieState *s=&zombies[slot];s16 x=PX(game.actors[slot].x),px=PX(game.p.x);
 if(variant(slot) && choose && !s->thrown && !((loot_random>>8)&3)) {
  if(variant(slot)==2) {
   game.actors[slot].life=aim_direction(x-game.cam_x,PX(game.actors[slot].y)-game.cam_y,px-game.cam_x,PX(game.p.y)-game.cam_y);
   if(((game.actors[slot].life+4)&15)<9)return root(slot,(u16)x<(u16)px?9:10);
  } else return root(slot,x<px?9:10);
 }
 s->left=x>=px;
 if(s->thrown){s->fraction=0;return root(slot,s->left?12:11);}
 return root(slot,s->left?2:1);
}
static u16 hide(u16 slot) {zombies[slot].vulnerable=0;return root(slot,zombies[slot].thrown?15:7);}
static void gravity(ZombieState *s) {
 u16 v=(u16)((u8)s->animation.vy)*256+s->fraction+64;
 if ((v>>8)==5)v=1280;
 s->animation.vy=v>>8;s->fraction=v&255;
}
static u16 jump(u16 slot) {
 ZombieState *s=&zombies[slot];
 if(s->animation.vy>=0 && ground(slot,16,32)) {
  u8 old=s->cycles;s->cycles-=3;
  return old<3?hide(slot):face(slot,0);
 }
 gravity(s);return root(slot,s->left?14:13);
}
static u16 fall(u16 slot) {
 ZombieState *s=&zombies[slot];
 if (ground(slot,16,32)) return face(slot,1);
 gravity(s);return root(slot,s->left?6:5);
}
__attribute__((noinline)) static void zombie_transition(u16 slot) {
 Actor *a=&game.actors[slot];ZombieState *s=&zombies[slot];u16 tries;
 if (s->pending) {s->pending=0;select_segment(s,root(slot,8));game.kills++;}
 for (tries=0;tries<12;tries++) {
  const SkeletonSegment *seg=segment(slot);u16 target=seg->next;
  if (animation_step(&s->animation,seg->clip)) {
   a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;a->y+=a->vy;return;
  }
  switch(seg->event) {
  case 0:s->vulnerable=0;break;
  case 1:s->vulnerable=1;break;
  case 2:target=face(slot,1);break;
  case 3:
   if (!--s->cycles) {target=hide(slot);}
   else if (!ground(slot,16,32)) {s->animation.vx=s->animation.vy=s->fraction=0;target=fall(slot);}
   else if (ground(slot,s->left?0:32,16)) target=root(slot,s->left?4:3);
   break;
  case 4:target=fall(slot);break;
  case 5:game.sound=SND_KILL;loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));
   if(variant(slot))target=root(slot,s->thrown?17:16);
   break;
  case 7:
   if(variant(slot)==2) {
    if(missile_spawn(PX(a->x),PX(a->y),spitter_segments[root(slot,18+(a->life&31))].clip,
       spitter_segments[root(slot,50)].clip,spitter_shot_damage,spitter_shot_width,spitter_shot_height,spitter_shot_health))s->thrown=1;
   } else if(missile_spawn(PX(a->x),PX(a->y),thrower_segments[root(slot,PX(game.p.x)<PX(a->x)?18:19)].clip,
       thrower_segments[root(slot,21)].clip,thrower_shot_damage,thrower_shot_width,thrower_shot_height,thrower_shot_health))s->thrown=1;
   target=face(slot,0);break;
  case 8:s->animation.vy=-4;target=jump(slot);break;
  case 9:target=jump(slot);break;
  default:a->active=0;game.spawned[a->source]=0;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *zombie_frame(u16 slot) {
 ZombieState *s=&zombies[slot];return s->animation.remaining?animation_current(&s->animation,segment(slot)->clip):0;
}

/* Held frames avoid the transition interpreter's large register frame. */
void zombie_step(u16 slot) {
 ZombieState *s=&zombies[slot];
 if(!s->pending && animation_hold_step(&s->animation,segment(slot)->clip)) {
  Actor *a=&game.actors[slot];a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;
  a->x+=a->vx;a->y+=a->vy;return;
 }
 zombie_transition(slot);
}
