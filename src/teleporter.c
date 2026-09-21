#include "teleporter.h"
#include "assets.h"
#include "loot.h"
#include "progress.h"
#include "container.h"
typedef struct {AnimState animation;u16 segment;u8 mode,pending,left,phase,cycles;} TeleporterState;
static TeleporterState teleporters[MAX_ACTORS];
static u8 teleporter_once[160],teleporter_delay[160];
void teleporter_reset(void){u16 i;for(i=0;i<160;i++)teleporter_once[i]=teleporter_delay[i]=0;}
u8 teleporter_prepare(u16 row,s16 *x,s16 *y) {
 u8 sample;
 if(teleporter_once[row]){if(++teleporter_delay[row]!=45)return 0;teleporter_delay[row]=0;}
 else teleporter_once[row]=1;
 sample=(loot_random>>8)&7;*x=game.cam_x+teleporter_positions[sample][0];*y=game.cam_y+teleporter_positions[sample][1];return 1;
}
u8 teleporter_contact(u16 slot){return !(teleporters[slot].mode&2) && !game.actors[slot].state;}
void teleporter_screen_attack(u16 slot){Actor *a=&game.actors[slot];TeleporterState *s=&teleporters[slot];if(!a->state){a->life=1;s->pending=200;s->mode|=3;a->state=1;}}
static void select_segment(TeleporterState *s,u16 target) {animation_reset(&s->animation);s->segment=target;}
static const u16 *roots(const Actor *a){return teleporter_roots+14*(teleporter_kinds[a->def]-1);}
static u16 facing(Actor *a,TeleporterState *s,u8 root) {
 s->left=(u8)(PX(game.p.x)-game.cam_x)<(u8)(PX(a->x)-game.cam_x);
 return roots(a)[root+s->left];
}
void teleporter_spawn(u16 slot) {
 Actor *a=&game.actors[slot];TeleporterState *s=&teleporters[slot];
 s->mode=3;s->pending=s->left=s->phase=s->cycles=0;a->life=teleporter_health[teleporter_kinds[a->def]-1];a->hp=1;a->state=0;
 select_segment(s,roots(a)[0]);
}
u8 teleporter_vulnerable(u16 slot) {return !(teleporters[slot].mode&1) && !game.actors[slot].state;}
u8 teleporter_hit(u16 slot,u8 damage) {
 Actor *a=&game.actors[slot];TeleporterState *s=&teleporters[slot];
 if(!damage || !teleporter_vulnerable(slot))return 0;
 s->pending=damage;s->mode|=3;a->state=1;return 1;
}

void teleporter_step(u16 slot) {
 Actor *a=&game.actors[slot];TeleporterState *s=&teleporters[slot];u16 tries;
 if(s->pending) {
  u8 damage=s->phase?s->pending>>1:s->pending;s->pending=0;
  if(a->life>damage) {
   a->life-=damage;a->hp=1;a->state=0;game.sound=SND_HIT;
   select_segment(s,s->phase?roots(a)[7+s->left]:facing(a,s,1));
  }else {
   a->state=2;game.sound=SND_KILL;game.spawned[a->source]|=2;game.kills++;progress_score(teleporter_score);
   loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));
   select_segment(s,roots(a)[11+s->left]);
  }
 }
 for(tries=0;tries<8;tries++) {
  const AnimSegment *seg=&teleporter_segments[s->segment];u16 target=seg->next;
  if(animation_tick(&s->animation,seg->clip)) {
   a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;actor_motion(a,a->vx,a->vy,s->mode);return;
  }
  switch(seg->event) {
  case 0:target=facing(a,s,1);break;
  case 1:s->phase=1;break;
  case 2:s->mode=8;break;
  case 3:target=facing(a,s,3);break;
  case 4:if(teleporter_kinds[a->def]==1)container_wave_spawn(PX(a->x),s->left);else container_ground_spawn(PX(a->x),s->left);if(++s->cycles==5)target=roots(a)[9+s->left];break;
  case 5: {
   u8 sample=(loot_random>>8)&7;a->x=(game.cam_x+teleporter_positions[sample][0])*FX;a->y=(game.cam_y+teleporter_positions[sample][1])*FX;
   target=facing(a,s,5);break;
  }
  case 6:s->mode=11;break;
  default:a->active=0;game.spawned[a->source]&=254;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *teleporter_frame(u16 slot) {
 TeleporterState *s=&teleporters[slot];return s->animation.remaining?animation_current(&s->animation,teleporter_segments[s->segment].clip):0;
}
