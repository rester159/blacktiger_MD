#include "edge_actor.h"
#include "assets.h"
#include "loot.h"
#include "progress.h"
#include "sentry.h"
#include "hazard.h"
typedef struct {AnimState animation;u16 segment;u8 mode,pending,left,fraction,variant,fired,contact,contact_pending;} EdgeState;
static EdgeState edge_actors[MAX_ACTORS];
EdgeShot edge_shots[24];
void edge_shots_reset(void){u16 i;for(i=0;i<24;i++)edge_shots[i].active=0;}
static void select_animation(AnimState *a,u16 *segment,u16 target){s8 vx=a->vx,vy=a->vy;animation_reset(a);a->vx=vx;a->vy=vy;*segment=target;}
static u16 sided(EdgeState *s,u8 at){return edge_roots[at+!s->left];}
void edge_actor_spawn(u16 slot){Actor *a=&game.actors[slot];EdgeState *s=&edge_actors[slot];*s=(EdgeState){0};s->mode=11;s->segment=edge_roots[game.p.face?1:0];a->hp=edge_health;a->life=edge_layers;a->state=0;}
u8 edge_actor_vulnerable(u16 slot){return !(edge_actors[slot].mode&1) && game.actors[slot].state!=2;}
u8 edge_actor_hit(u16 slot,u8 damage){Actor *a=&game.actors[slot];EdgeState *s=&edge_actors[slot];if(!damage || !edge_actor_vulnerable(slot))return 0;if(a->hp>damage)a->hp-=damage;else{s->pending=1;s->mode|=3;a->state=1;}return 1;}
void edge_screen_attack(u16 slot){if(game.actors[slot].state!=2){game.actors[slot].life=1;edge_actors[slot].pending=1;edge_actors[slot].mode|=3;game.actors[slot].state=1;}}
static u8 ground(s16 x,s16 y){u8 t=terrain(x,y);return t==2 || t==3;}
static void gravity(EdgeState *s){u16 v=((u16)(u8)s->animation.vy<<8)+s->fraction+64;if((v>>8)==5)v=1280;s->animation.vy=v>>8;s->fraction=v;}
static u8 player_left(Actor *a){return (u8)(PX(game.p.x)-game.cam_x)<(u8)(PX(a->x)-game.cam_x);}
static u16 choose(Actor *a,EdgeState *s){u16 x=PX(a->x),px=PX(game.p.x);u8 d,choice;s->left=x>=px;d=s->left?x-px:px-x;choice=edge_choices[(d&112)>>4][(loot_random>>9)&15];if(choice<5){s->variant=choice;return sided(s,2+2*choice);}s->contact=37;return edge_roots[player_left(a)?12:13];}
static u16 recoil(Actor *a,EdgeState *s){a->hp=edge_health;return sided(s,18);}
static u16 land(EdgeState *s){s->fired=s->variant=0;return sided(s,24);}
static u16 launch(Actor *a,EdgeState *s,u8 attack,u16 fallback){
 u16 i;u8 direction,profile=attack==2;
 if(attack==3)return fallback;
 direction=aim_direction(PX(a->x)-game.cam_x,PX(a->y)-game.cam_y,PX(game.p.x)-game.cam_x,PX(game.p.y)-game.cam_y);
 if(direction>=17)return fallback;
 for(i=0;i<24 && edge_shots[i].active;i++){}
 if(i==24)return fallback;
 {EdgeShot *p=&edge_shots[i];*p=(EdgeShot){0};p->active=1;p->profile=profile;p->hp=profile?32:24;p->segment=edge_shot_roots[profile*17+direction];p->x=PX(a->x)+8;p->y=PX(a->y)+8;}
 return sided(s,attack==1?28:26);
}
void edge_actor_step(u16 slot){Actor *a=&game.actors[slot];EdgeState *s=&edge_actors[slot];u16 tries;
 if(s->contact_pending){s->contact_pending=0;select_animation(&s->animation,&s->segment,edge_roots[40]);}
 if(s->pending){u16 target;s->pending=0;if(--a->life){a->state=0;target=s->variant?edge_roots[player_left(a)?20:21]:recoil(a,s);}else{a->state=2;loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));game.spawned[a->source]|=2;progress_score(edge_score);game.kills++;target=edge_roots[player_left(a)?22:23];}select_animation(&s->animation,&s->segment,target);}
 for(tries=0;tries<12;tries++){
  const AnimSegment *seg=&edge_segments[s->segment];u16 target=seg->next;
  if(animation_tick(&s->animation,seg->clip)){a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;if(!(s->mode&16) && !small_actor_axis_active(PX(a->x)-game.cam_x,0)){a->active=0;game.spawned[a->source]&=254;return;}a->y+=a->vy;if(!(s->mode&16) && !small_actor_axis_active(PX(a->y)-game.cam_y,1)){a->active=0;game.spawned[a->source]&=254;}return;}
  switch(seg->event){
  case 0:s->mode=8; /* fall through */
  case 1:target=choose(a,s);break;
  case 2:case 3:case 4:case 5:case 6:s->animation.vy=-4;s->fraction=0;break;
  case 7:
   if(!ground(PX(a->x)+16,PX(a->y)+32)){s->animation.vy=s->fraction=0;target=sided(s,14);}
   else if((u8)(PX(a->x)+16-PX(game.p.x))<64){s->contact=0;target=sided(s,16);}
   break;
  case 8:if(ground(PX(a->x)+16,PX(a->y)+32))target=choose(a,s);else gravity(s);break;
  case 9:s->contact=0;target=sided(s,16);break;
  case 11:a->x=(game.cam_x+((loot_random>>8)&1?80:176))*FX;target=edge_roots[0];break;
  case 12:if(ground(PX(a->x)+16,PX(a->y)+32))target=recoil(a,s);break;
  case 13:
   if(s->animation.vy>=0){if(!s->fired){s->fired=1;target=launch(a,s,edge_attacks[(loot_random>>8)&15],target);}if(ground(PX(a->x)+16,PX(a->y)+32)){target=land(s);break;}}
   gravity(s);break;
  case 14:target=land(s);break;
  case 15:target=launch(a,s,0,seg->next);if(ground(PX(a->x)+16,PX(a->y)+32))target=land(s);else gravity(s);break;
  case 16:target=edge_roots[30+s->left*5+s->variant];break;
  default:a->active=0;game.spawned[a->source]&=254;return;
  }
  select_animation(&s->animation,&s->segment,target);
 }
}
u8 edge_actor_contact(u16 slot){EdgeState *s=&edge_actors[slot];if((s->mode&2) || game.actors[slot].state==2)return 0;if(s->contact==37)s->contact_pending=1;return 1;}
const AnimFrame *edge_actor_frame(u16 slot){EdgeState *s=&edge_actors[slot];return s->animation.remaining?animation_current(&s->animation,edge_segments[s->segment].clip):0;}
void edge_shots_step(void){u16 i;for(i=0;i<24;i++){EdgeShot *p=&edge_shots[i];u16 n;if(!p->active)continue;if(p->pending){p->pending=0;select_animation(&p->animation,&p->segment,edge_shot_roots[35+p->profile*2]);}
 for(n=0;n<4;n++){const AnimSegment *seg=&edge_shot_segments[p->segment];u16 target=seg->next;if(animation_tick(&p->animation,seg->clip)){p->x+=p->animation.vx;if(!small_actor_axis_active(p->x-game.cam_x,0)){p->active=0;break;}p->y+=p->animation.vy;if(!small_actor_axis_active(p->y-game.cam_y,1))p->active=0;break;}if(seg->event){p->active=0;break;}if(ground(p->x+8,p->y+8))target=edge_shot_roots[34+p->profile*2];select_animation(&p->animation,&p->segment,target);}
}}
u8 edge_shot_contact(u16 slot){EdgeShot *p=&edge_shots[slot];return p->active && !p->dying && !(game.frame&1) && player_contact(p->x,p->y,p->profile?5:3,p->profile?5:3)?(p->profile?3:1):0;}
u8 edge_shot_hit(s16 x,s16 y,u8 damage,u8 dagger){u16 i;for(i=0;i<24;i++){EdgeShot *p=&edge_shots[i];s16 dx=x-p->x,dy=y-p->y;u8 w=(p->profile?5:3)+(dagger?dagger_width:8),h=(p->profile?5:3)+(dagger?dagger_height:4);if(!p->active || p->dying || (dagger && (game.frame&1)))continue;if(dx>=-(s16)w && dx<=w && dy>=-(s16)h && dy<=h){u8 hit=dagger?(damage>1?damage>>1:1):damage;if(p->hp>hit)p->hp-=hit;else{p->dying=1;p->pending=1;}return 1;}}return 0;}
const AnimFrame *edge_shot_frame(u16 slot){EdgeShot *p=&edge_shots[slot];return p->active && p->animation.remaining?animation_current(&p->animation,edge_shot_segments[p->segment].clip):0;}
