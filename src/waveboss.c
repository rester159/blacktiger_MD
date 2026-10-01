#include "waveboss.h"
/* Conservative render occupancy: allocation sets it, updates refresh it. */
u8 waveboss_seeds_occupied;
#include "assets.h"
#include "loot.h"
#include "progress.h"
#include "shop.h"
typedef struct {AnimState animation;u16 segment;u8 mode,pending,left,profile,engaged;} WaveBossState;
static WaveBossState wavebosses[MAX_ACTORS];
WaveBossSeed waveboss_seeds[MAX_WAVEBOSS_SEEDS];
void waveboss_reset(void){u16 i;waveboss_seeds_occupied=0;for(i=0;i<MAX_WAVEBOSS_SEEDS;i++)waveboss_seeds[i].active=0;}
static void select_segment(AnimState *a,u16 *segment,u16 target){s8 vx=a->vx,vy=a->vy;animation_reset(a);a->vx=vx;a->vy=vy;*segment=target;}
void waveboss_spawn(u16 slot){
 Actor *a=&game.actors[slot];WaveBossState *s=&wavebosses[slot];
 animation_reset(&s->animation);s->mode=24;s->pending=s->engaged=0;s->left=1;s->profile=waveboss_kinds[a->def]-1;
 a->hp=waveboss_health[s->profile];a->life=waveboss_layers[s->profile];a->state=0;s->segment=waveboss_roots[0];
}
u8 waveboss_present(void){u16 i;for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && waveboss_kinds[game.actors[i].def])return 1;return 0;}
u8 waveboss_locked(void){u16 i;for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && waveboss_kinds[game.actors[i].def] && game.actors[i].state==2)return 1;return 0;}
u8 waveboss_contact(u16 slot){return !(wavebosses[slot].mode&2) && game.actors[slot].state!=2;}
u8 waveboss_vulnerable(u16 slot){return !(wavebosses[slot].mode&1) && !game.actors[slot].state;}
u8 waveboss_hit(u16 slot,u8 damage){
 Actor *a=&game.actors[slot];WaveBossState *s=&wavebosses[slot];if(!waveboss_vulnerable(slot))return 0;
 if(a->hp>damage)a->hp-=damage;else {s->pending=1;s->mode|=3;a->state=1;}return 1;
}
void waveboss_screen_attack(u16 slot){Actor *a=&game.actors[slot];if(!a->state){a->life=1;a->hp=1;wavebosses[slot].pending=1;wavebosses[slot].mode|=3;a->state=1;}}
static u16 activate(Actor *a,WaveBossState *s){s->engaged=1;s->mode=24;a->hp=s->profile?40:16;return waveboss_roots[2];}
static u16 action(WaveBossState *s,u8 choice){return waveboss_roots[6+choice*2+s->left];}
static u16 choose(Actor *a,WaveBossState *s){
 s16 x=PX(a->x)-game.cam_x,px=PX(game.p.x)-game.cam_x;u16 shifted=(u16)x+32;
 s->left=(u16)(shifted+256)>=(u16)(px+256)+(shifted<(u16)x);
 if((u16)x>>8)return waveboss_roots[((u16)x>>8)==255?5:4];
 return action(s,waveboss_choices[s->profile][(loot_random>>8)&15]);
}
static u8 seed_spawn(Actor *a,WaveBossState *s){
 u16 i;for(i=0;i<MAX_WAVEBOSS_SEEDS;i++)if(!waveboss_seeds[i].active){
  WaveBossSeed *p=&waveboss_seeds[i];animation_reset(&p->animation);p->segment=waveboss_roots[16+s->left];
  p->x=PX(a->x)+(s->left?48:0);p->y=PX(a->y)+4;p->left=s->left;p->profile=s->profile;p->active=1;waveboss_seeds_occupied=1;return 1;
 }return 0;
}
void waveboss_step(u16 slot){
 Actor *a=&game.actors[slot];WaveBossState *s=&wavebosses[slot];u16 tries;
 if(s->pending){s->pending=0;select_segment(&s->animation,&s->segment,waveboss_roots[s->engaged?3:1]);}
 for(tries=0;tries<8;tries++){
  const WaveBossSegment *seg=&waveboss_segments[s->segment];u16 target=seg->next[0];
  if(animation_step(&s->animation,seg->clip)){a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;a->y+=a->vy;return;}
  switch(seg->event){
  case 0:if((u8)(PX(game.p.x)+64-PX(a->x))<128)target=activate(a,s);break;
  case 1:s->mode=24;break;
  case 2:target=choose(a,s);break;
  case 3:if(!seed_spawn(a,s))target=choose(a,s);break;
  case 6:
   if(--a->life){a->hp=waveboss_health[s->profile];a->state=0;s->mode=24;target=waveboss_roots[12+s->left];}
   else {a->state=2;game.boss_dead=1;shop_poison=0;game.spawned[a->source]|=2;game.kills++;progress_score(waveboss_scores[s->profile]);target=waveboss_roots[14+s->left];}
   break;
  case 7:break; /* The original schedules a separate death-flash presentation task. */
  case 8:game_boss_clear();return;
  case 9:target=activate(a,s);break;
  case 10:case 11:case 12:target=action(s,seg->event-10);break;
  default:a->active=0;game.spawned[a->source]^=1;return;
  }
  select_segment(&s->animation,&s->segment,target);
 }
}
const AnimFrame *waveboss_frame(u16 slot){WaveBossState *s=&wavebosses[slot];return s->animation.remaining?animation_current(&s->animation,waveboss_segments[s->segment].clip):0;}
u8 waveboss_seeds_tick(void){u8 occupied=0;
 u16 i,tries;for(i=0;i<MAX_WAVEBOSS_SEEDS;i++){WaveBossSeed *p=&waveboss_seeds[i];if(!p->active)continue;occupied=1;
  for(tries=0;tries<8;tries++){
   const WaveBossSegment *seg=&waveboss_segments[p->segment];u16 target=seg->next[0];
   if(animation_step(&p->animation,seg->clip)){
    p->x+=p->animation.vx;if(!small_actor_axis_active(p->x-game.cam_x,0)){p->active=0;break;}
    p->y+=p->animation.vy;if(!small_actor_axis_active(p->y-game.cam_y,1))p->active=0;break;
   }
   if(seg->event==4){if(p->profile)container_wave_spawn(p->x,p->left);else container_ground_spawn(p->x,p->left);}
   else if(seg->event==5){u8 t=terrain(p->x+8,p->y+8);if(t==2 || t==3)target=seg->next[1];}
   else {p->active=0;break;}
   select_segment(&p->animation,&p->segment,target);
  }
 }
waveboss_seeds_occupied=occupied;return occupied;
}
const AnimFrame *waveboss_seed_frame(u16 slot){WaveBossSeed *p=&waveboss_seeds[slot];return p->active && p->animation.remaining?animation_current(&p->animation,waveboss_segments[p->segment].clip):0;}
u8 waveboss_player_contact(u16 slot){
 Actor *a=&game.actors[slot];return large_player_contact(&waveboss_shapes[wavebosses[slot].profile],PX(a->x)-game.cam_x,PX(a->y)-game.cam_y,PX(game.p.x)-game.cam_x,PX(game.p.y)-game.cam_y,contact_player_width,contact_player_height,game.player_low);
}
u8 waveboss_weapon_contact(u16 slot,s16 x,s16 y,u8 dagger){
 Actor *a=&game.actors[slot];if(!waveboss_vulnerable(slot))return 0;
 return large_weapon_contact(&waveboss_shapes[wavebosses[slot].profile],PX(a->x)-game.cam_x,PX(a->y)-game.cam_y,x-game.cam_x,y-game.cam_y,dagger?dagger_width:8,dagger?dagger_height:4,dagger);
}
