#include "zombie.h"
#include "assets.h"
#include "loot.h"
typedef struct {AnimState animation;u16 segment;u8 left,cycles,fraction,vulnerable,pending;} ZombieState;
static ZombieState zombies[MAX_ACTORS];
static u8 spawn_delay[160];
void zombie_reset(void) {u16 i;for(i=0;i<160;i++)spawn_delay[i]=0;}
u8 zombie_prepare(u16 row,s16 *x,s16 *y) {
 u16 i;u8 count=0;
 if (++spawn_delay[row]!=30) return 0;
 spawn_delay[row]=0;
 for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && zombie_kinds[game.actors[i].def])count++;
 if(count>=3)return 0;
 *x=game.cam_x+zombie_spawn_x[(loot_random>>9)&7];*y=game.cam_y+112;
 for(i=0;i<5;i++,*y+=16) {u8 t=terrain(*x+16,*y+32);if(t==2 || t==3)return 1;}
 return 0;
}
static u8 ground(u16 slot,s16 dx,s16 dy) {
 Actor *a=&game.actors[slot];u8 t=terrain(PX(a->x)+dx,PX(a->y)+dy);
 return t==2 || t==3;
}
static void select_segment(ZombieState *s,u16 segment) {
 s8 vx=s->animation.vx,vy=s->animation.vy;
 animation_reset(&s->animation);s->animation.vx=vx;s->animation.vy=vy;s->segment=segment;
}
void zombie_spawn(u16 slot) {
 ZombieState *s=&zombies[slot];animation_reset(&s->animation);s->segment=zombie_roots[0];
 s->left=s->fraction=s->vulnerable=s->pending=0;s->cycles=zombie_lifetime;
 game.actors[slot].state=0;game.actors[slot].hp=1;
}
u8 zombie_vulnerable(u16 slot) {return zombies[slot].vulnerable && !game.actors[slot].state;}
u8 zombie_hit(u16 slot,u8 damage) {
 Actor *a=&game.actors[slot];
 if (!zombie_kinds[a->def]) return 0;
 if (!a->state && damage>=a->hp) {a->state=1;zombies[slot].pending=1;zombies[slot].vulnerable=0;game.score+=zombie_score;}
 return 1;
}
static u16 face(u16 slot) {
 ZombieState *s=&zombies[slot];s->left=PX(game.actors[slot].x)>=PX(game.p.x);
 return zombie_roots[s->left?2:1];
}
static u16 fall(u16 slot) {
 ZombieState *s=&zombies[slot];u16 v;
 if (ground(slot,16,32)) return face(slot);
 v=(u16)((u8)s->animation.vy)*256+s->fraction+64;
 if ((v>>8)==5) v=1280;
 s->animation.vy=v>>8;s->fraction=v&255;
 return zombie_roots[s->left?6:5];
}
void zombie_step(u16 slot) {
 Actor *a=&game.actors[slot];ZombieState *s=&zombies[slot];u16 tries;
 if (s->pending) {s->pending=0;select_segment(s,zombie_roots[8]);game.kills++;}
 for (tries=0;tries<12;tries++) {
  const SkeletonSegment *seg=&zombie_segments[s->segment];u16 target=seg->next;
  if (animation_tick(&s->animation,seg->clip)) {
   a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;a->y+=a->vy;return;
  }
  switch(seg->event) {
  case 0:s->vulnerable=0;break;
  case 1:s->vulnerable=1;break;
  case 2:target=face(slot);break;
  case 3:
   if (!--s->cycles) {s->vulnerable=0;target=zombie_roots[7];}
   else if (!ground(slot,16,32)) {s->animation.vx=s->animation.vy=s->fraction=0;target=fall(slot);}
   else if (ground(slot,s->left?0:32,16)) target=zombie_roots[s->left?4:3];
   break;
  case 4:target=fall(slot);break;
  case 5:game.sound=SND_KILL;loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));break;
  default:a->active=0;game.spawned[a->source]=0;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *zombie_frame(u16 slot) {
 ZombieState *s=&zombies[slot];return s->animation.remaining?animation_current(&s->animation,zombie_segments[s->segment].clip):0;
}
