#include "reinforcement_body.h"
/* Conservative render occupancy: allocation sets it, updates refresh it. */
u8 reinforcement_shots_occupied;
#include "assets.h"
#include "loot.h"
#include "progress.h"
#include "hazard.h"
typedef struct {AnimState animation;u16 segment;u8 mode,pending,left,profile,fraction,low;} ReinforcementState;
static ReinforcementState fighters[MAX_ACTORS];
ReinforcementShot reinforcement_shots[24];
u8 reinforcement_player_low;
void reinforcement_shots_reset(void){u16 i;reinforcement_shots_occupied=0;for(i=0;i<24;i++)reinforcement_shots[i].active=0;}
static u16 root(ReinforcementState *s,u8 n){return reinforcement_roots[s->profile][n];}
static u16 sided(ReinforcementState *s,u8 n){return root(s,n+!s->left);}
static void select_segment(ReinforcementState *s,u16 n){s8 vx=s->animation.vx,vy=s->animation.vy;animation_reset(&s->animation);s->animation.vx=vx;s->animation.vy=vy;s->segment=n;}
void reinforcement_body_spawn(u16 slot){
 Actor *a=&game.actors[slot];ReinforcementState *s=&fighters[slot];
 *s=(ReinforcementState){0};s->profile=reinforcement_kinds[a->def]-1;s->mode=11;s->segment=root(s,0);
 a->hp=reinforcement_health[s->profile];a->life=reinforcement_layers[s->profile];a->state=0;
}
u8 reinforcement_body_vulnerable(u16 slot){return !(fighters[slot].mode&1) && !game.actors[slot].state;}
u8 reinforcement_body_contact(u16 slot){return !(fighters[slot].mode&2) && !game.actors[slot].state;}
u8 reinforcement_body_hit(u16 slot,u8 damage){if(!damage || !reinforcement_body_vulnerable(slot))return 0;if(game.actors[slot].hp>damage){game.actors[slot].hp-=damage;return 1;}fighters[slot].pending=damage;fighters[slot].mode|=3;game.actors[slot].state=1;return 1;}
void reinforcement_screen_attack(u16 slot){if(!game.actors[slot].state){game.actors[slot].life=1;fighters[slot].pending=200;fighters[slot].mode|=3;game.actors[slot].state=1;}}
static u8 ground(Actor *a,s16 x,s16 y){u8 t=terrain(PX(a->x)+x,PX(a->y)+y);return t==2 || t==3;}
static void gravity(ReinforcementState *s){u16 v=((u16)(u8)s->animation.vy<<8)+s->fraction+64;if((v>>8)==5)v=1280;s->animation.vy=v>>8;s->fraction=v;}
static u16 choose(Actor *a,ReinforcementState *s);
static u16 fall(Actor *a,ReinforcementState *s,u8 type){
 if((!type || s->animation.vy>=0) && ground(a,16,32))return type?sided(s,15):choose(a,s);
 gravity(s);return sided(s,type==1?6:type==2?9:17);
}
static u16 fall_start(Actor *a,ReinforcementState *s){s->animation.vx=s->animation.vy=s->fraction=0;return fall(a,s,0);}
static u8 distance(Actor *a,ReinforcementState *s){u16 x=PX(a->x),px=PX(game.p.x);s->left=x>=px;return s->left?x-px:px-x;}
static u16 choose(Actor *a,ReinforcementState *s){
 u8 d=distance(a,s),choice=reinforcement_choices[s->profile][(d&112)>>4][(loot_random>>9)&15];
 switch(choice){
 case 0:if(!ground(a,16,32))return fall_start(a,s);s->low=s->profile && reinforcement_player_low;return sided(s,s->low?23:1);
 case 1:return sided(s,3);
 /* Both source routines unconditionally select the right-facing windup. */
 case 2:return root(s,5);
 case 3:return root(s,8);
 default:return sided(s,11);
 }
}
static u8 launch(Actor *a,ReinforcementState *s,u8 left){
 u16 i,j;for(i=0;i<24;i+=6){for(j=0;j<6 && !reinforcement_shots[i+j].active;j++){}if(j==6)break;}
 if(i==24)return 0;
 for(j=0;j<6;j++){ReinforcementShot *p=&reinforcement_shots[i+j];animation_reset(&p->animation);p->active=1;reinforcement_shots_occupied=1;p->part=j+(left?0:6);p->x=PX(a->x)+(left?-13:29);p->y=PX(a->y)+(s->low?8:0);}
 game.sound=SND_ATTACK;return 1;
}
__attribute__((noinline)) static void reinforcement_body_transition(u16 slot){
 Actor *a=&game.actors[slot];ReinforcementState *s=&fighters[slot];u16 tries;
 if(s->pending){u8 damage=s->pending;s->pending=0;game.sound=SND_HIT;
  if(a->hp>damage){a->hp-=damage;a->state=0;s->mode=8;select_segment(s,choose(a,s));}
  else if(--a->life){a->hp=s->profile?reinforcement_health[s->profile]:3;a->state=0;select_segment(s,root(s,19+(game.p.face?1:0)));}
  else{a->state=2;progress_score(reinforcement_scores[s->profile]);game.kills++;loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));game.sound=SND_KILL;select_segment(s,root(s,(u8)(PX(game.p.x)-game.cam_x)<(u8)(PX(a->x)-game.cam_x)?21:22));}
 }
 for(tries=0;tries<8;tries++){
  const AnimSegment *seg=&reinforcement_segments[s->segment];u16 target=seg->next;
  if(animation_step(&s->animation,seg->clip)){a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;actor_motion(a,a->vx,a->vy,s->mode);return;}
  switch(seg->event){
  case 0:s->mode=8;
  case 1:target=choose(a,s);break;
  case 2:case 3:if(!launch(a,s,seg->event==3))target=fall(a,s,1);break;
  case 4:{u16 x=PX(a->x),px=PX(game.p.x);u8 d=x>=px?x-px:px-x;s->animation.vy=-4;s->fraction=0;s->animation.vx=(s->left?-1:1)*(d<64?1:2);target=sided(s,6);break;}
  case 5:s->animation.vy=-4;s->fraction=128;s->animation.vx=s->left?-1:1;target=sided(s,9);break;
  case 6:
   if(!ground(a,16,32))target=fall_start(a,s);
   else if(ground(a,s->left?0:32,16)){
    if(ground(a,s->left?0:32,-16))target=sided(s,13);
    else{s->animation.vx=s->left?-1:1;s->animation.vy=-5;s->fraction=0;target=fall(a,s,1);}
   }break;
  case 7:target=fall(a,s,1);break;
  case 8:target=fall(a,s,2);break;
  case 9:target=fall(a,s,0);break;
  default:a->active=0;game.spawned[a->source]&=254;return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *reinforcement_body_frame(u16 slot){ReinforcementState *s=&fighters[slot];return s->animation.remaining?animation_current(&s->animation,reinforcement_segments[s->segment].clip):0;}
u8 reinforcement_shots_step(void){u8 occupied=0;u16 i;for(i=0;i<24;i++){ReinforcementShot *p=&reinforcement_shots[i];if(!p->active)continue;occupied=1;if(!animation_step(&p->animation,reinforcement_clips[p->part])){p->active=0;continue;}p->x+=p->animation.vx;if(!small_actor_axis_active(p->x-game.cam_x,0)){p->active=0;continue;}p->y+=p->animation.vy;if(!small_actor_axis_active(p->y-game.cam_y,1))p->active=0;}reinforcement_shots_occupied=occupied;return occupied;
}
u8 reinforcement_shot_contact(u16 slot){ReinforcementShot *p=&reinforcement_shots[slot];return p->active && p->part%6==2 && !(game.frame&1) && player_contact(p->x,p->y,40,4);}
const AnimFrame *reinforcement_shot_frame(u16 slot){ReinforcementShot *p=&reinforcement_shots[slot];return p->active && p->animation.remaining?animation_current(&p->animation,reinforcement_clips[p->part]):0;}

/* Keep ordinary held-frame motion outside the transition interpreter. */
void reinforcement_body_step(u16 slot) {
 ReinforcementState *s=&fighters[slot];
 if(!s->pending && animation_hold_step(&s->animation,reinforcement_segments[s->segment].clip)){
  Actor *a=&game.actors[slot];a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;actor_motion(a,a->vx,a->vy,s->mode);return;
 }
 reinforcement_body_transition(slot);
}
