#include "progress.h"
#include "container.h"
#include "assets.h"
#include "hazard.h"
typedef struct {AnimState animation;u16 segment;u8 id,phase,pending,left;} ContainerState;
static ContainerState containers[MAX_ACTORS];
static u8 container_opened[8],container_collected[8];
ContainerTrap container_traps[MAX_CONTAINER_TRAPS];
u8 container_keys;
void container_actor_restart(void) {u16 i;for(i=0;i<MAX_CONTAINER_TRAPS;i++)container_traps[i].active=0;}
void container_actor_reset(void) {
 u16 i;for(i=0;i<8;i++)container_opened[i]=container_collected[i]=0;
 for(i=0;i<MAX_CONTAINER_TRAPS;i++)container_traps[i].active=0;
}
static void select_clip(AnimState *a,u16 *segment,u16 target) {
 s8 vx=a->vx,vy=a->vy;animation_reset(a);a->vx=vx;a->vy=vy;*segment=target;
}
void container_spawn(u16 slot) {
 Actor *a=&game.actors[slot];ContainerState *s=&containers[slot];
 u16 id=rounds[game.round].spawns[a->source].persistent;
 s->id=id>=33 && id<41?id-33:0;s->pending=0;
 /* The two closed constructors differ only in trap direction. */
 s->left=container_left[a->def];
 a->life=container_content(id);
 s->phase=container_collected[s->id]?3:container_opened[s->id]?2:0;
 animation_reset(&s->animation);
 s->segment=container_roots[s->phase==3?4:s->phase==2?(a->life==5?6:a->life?5:4):0];
}
static void attack_spawn(s16 x,u8 left,const u16 *roots,u8 special) {
 u16 base,i; s16 y=game.cam_y+112;
 for(base=0;base<MAX_CONTAINER_TRAPS;base+=6) {
  for(i=0;i<6 && !container_traps[base+i].active;i++);
  if(i==6)break;
 }
 if(base==MAX_CONTAINER_TRAPS)return;
 for(i=0;i<6;i++,y+=16) {u8 t=terrain(x+8,y+16);if(t==2 || t==3)break;}
 if(i==6)y=PX(game.p.y)+16;
 for(i=0;i<6;i++) {
  ContainerTrap *t=&container_traps[base+i];animation_reset(&t->animation);
  t->segment=roots[i];t->x=x+(i>=3?(left?-24:24):0);t->y=y;
  t->active=1;t->left=left;t->contact=0;t->part=i%3+(special?3:0);
 }
}
void container_ground_spawn(s16 x,u8 left){attack_spawn(x+8,left,container_trap_roots,0);}
void container_wave_spawn(s16 x,u8 left){attack_spawn(x+(left?-32:48),left,container_wave_roots,1);}
void container_step(u16 slot,u8 contact) {
 Actor *a=&game.actors[slot];ContainerState *s=&containers[slot];u16 tries;
 if(s->pending) {
  u8 effect=s->pending;s->pending=0;
  select_clip(&s->animation,&s->segment,container_roots[effect==CONTAINER_COLLECT?7:a->life==0?1:a->life==5?3:2]);
 }
 for(tries=0;tries<4;tries++) {
  const ContainerSegment *seg=&container_segments[s->segment];
  if(animation_tick(&s->animation,seg->clip))break;
  if(seg->event==0) {attack_spawn(PX(a->x)+8,s->left,container_trap_roots,0);s->phase=3;game.sound=SND_HIT;}
  else if(seg->event==1 || seg->event==2) {s->phase=2;game.sound=SND_COIN;}
  else return;
  select_clip(&s->animation,&s->segment,seg->next);
 }
 if(contact && (game.frame&1) && (s->phase==0 || s->phase==2)) {
  ContainerContact c;u8 effect;
  c.coins=game.coins;c.invincible=game.p.invincible;c.keys=container_keys;c.hp=game.p.hp;
  c.max_hp=progress_max_hp;
  c.opened=container_opened[s->id];c.collected=container_collected[s->id];
  effect=container_contact(a->life,&c);if(!effect)return;
  container_keys=c.keys;game.coins=c.coins;game.p.hp=c.hp;game.p.invincible=c.invincible;
  container_opened[s->id]=c.opened;container_collected[s->id]=c.collected;
  s->pending=effect;s->phase=effect==CONTAINER_COLLECT?3:1;
  if(effect==CONTAINER_COLLECT)game.sound=SND_COIN;
 }
}
const AnimFrame *container_frame(u16 slot) {
 ContainerState *s=&containers[slot];return animation_current(&s->animation,container_segments[s->segment].clip);
}
void container_traps_tick(void) {
 u16 i;for(i=0;i<MAX_CONTAINER_TRAPS;i++) {
  ContainerTrap *t=&container_traps[i];u16 tries;if(!t->active)continue;
  for(tries=0;tries<4;tries++) {
   const ContainerSegment *seg=&container_segments[t->segment];
   if(animation_tick(&t->animation,seg->clip)) {
    t->x+=t->animation.vx;
    if(!small_actor_axis_active(t->x-game.cam_x,0)){t->active=0;break;}
    t->y+=t->animation.vy;
    if(!small_actor_axis_active(t->y-game.cam_y,1))t->active=0;
    break;
   }
   if(seg->event==3)t->x+=t->left?-48:48;
   else if(seg->event==4)t->contact=1;
   else if(seg->event==5)game.sound=SND_HIT;
   else {t->active=0;break;}
   select_clip(&t->animation,&t->segment,seg->next);
  }
 }
}
u8 container_trap_contact(u16 slot) {
 ContainerTrap *t=&container_traps[slot];
 return t->active && t->contact && !(game.frame&1) && player_contact(t->x,t->y,4,16)?(t->part>=3?2:1):0;
}
const AnimFrame *container_trap_frame(u16 slot) {
 ContainerTrap *t=&container_traps[slot];return t->active && t->animation.remaining?animation_current(&t->animation,container_segments[t->segment].clip):0;
}
