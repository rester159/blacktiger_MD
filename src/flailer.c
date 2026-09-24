#include "flailer.h"
/* Conservative render occupancy: allocation sets it, updates refresh it. */
u8 flailer_weapons_occupied;
#include "assets.h"
#include "loot.h"
#include "progress.h"
#include "hazard.h"
typedef struct {AnimState animation;u16 segment;u8 mode,pending,left,profile,fraction,armed,weapon;} FlailerState;
static FlailerState flailers[MAX_ACTORS];
FlailerWeapon flailer_weapons[MAX_ACTORS];
void flailer_reset(void){u16 i;flailer_weapons_occupied=0;for(i=0;i<MAX_ACTORS;i++)flailer_weapons[i].active=0;}
static void select_segment(AnimState *a,u16 *segment,u16 target){s8 vx=a->vx,vy=a->vy;animation_reset(a);a->vx=vx;a->vy=vy;*segment=target;}
static u16 root(FlailerState *s,u8 at){return flailer_roots[s->profile][at];}
static u16 sided(FlailerState *s,u8 at){return root(s,at+!s->left);}
void flailer_spawn(u16 slot){
 Actor *a=&game.actors[slot];FlailerState *s=&flailers[slot];u8 kind=flailer_kinds[a->def]-1;
 animation_reset(&s->animation);s->profile=kind>>1;s->left=!(kind&1);s->mode=8;s->pending=s->fraction=s->armed=0;s->weapon=255;
 a->life=flailer_health[s->profile];a->hp=1;a->state=0;s->segment=root(s,kind&1);
}
u8 flailer_vulnerable(u16 slot){return !(flailers[slot].mode&1) && !game.actors[slot].state;}
u8 flailer_hit(u16 slot,u8 damage){if(!damage || !flailer_vulnerable(slot))return 0;flailers[slot].pending=damage;flailers[slot].mode|=3;game.actors[slot].state=1;return 1;}
void flailer_screen_attack(u16 slot){Actor *a=&game.actors[slot];if(!a->state){a->life=1;flailers[slot].pending=200;flailers[slot].mode|=3;a->state=1;}}
static u8 ground(Actor *a,s16 dx,s16 dy){u8 t=terrain(PX(a->x)+dx,PX(a->y)+dy);return t==2 || t==3;}
static u16 facing(Actor *a,FlailerState *s,u8 at){s->left=(u16)PX(a->x)>=(u16)PX(game.p.x);return sided(s,at);}
static u8 near_x(Actor *a,FlailerState *s,u8 directional){
 u16 base=PX(a->x)+48,offset=directional?(s->left?(u16)-16:16):0,sum=base+offset,player=PX(game.p.x);
 u8 carry=sum<base;u16 delta=sum-player-carry;
 return delta<96+((u32)sum<(u32)player+carry);
}
static u16 falling(Actor *a,FlailerState *s,u8 jump){
 if((!jump || s->animation.vy>=0) && ground(a,16,32))return facing(a,s,5);
 {u16 value=((u16)(u8)s->animation.vy<<8)+s->fraction+64;if((value>>8)==5)value=0x500;s->animation.vy=value>>8;s->fraction=value;}
 return sided(s,jump?13:15);
}
static u16 fall_start(Actor *a,FlailerState *s){s->animation.vx=s->animation.vy=s->fraction=0;return falling(a,s,0);}
static u16 launch(Actor *a,FlailerState *s){
 u16 i;if(!ground(a,16,32))return fall_start(a,s);
 for(i=0;i<MAX_ACTORS;i++)if(!flailer_weapons[i].active){
  FlailerWeapon *p=&flailer_weapons[i];animation_reset(&p->animation);p->profile=s->profile;p->pending=p->dying=0;p->active=1;if(flailer_weapons_occupied<i+1)flailer_weapons_occupied=i+1;
  p->segment=sided(s,9);p->x=PX(a->x)+(s->left?32:-16);p->y=PX(a->y)+8;s->weapon=i;s->armed=1;
  return sided(s,7);
 }return facing(a,s,5);
}
__attribute__((noinline)) static void flailer_transition(u16 slot){
 Actor *a=&game.actors[slot];FlailerState *s=&flailers[slot];u16 tries;
 if(s->pending){u8 damage=s->pending;s->pending=0;
  if(s->armed && s->weapon<MAX_ACTORS && flailer_weapons[s->weapon].active){FlailerWeapon *p=&flailer_weapons[s->weapon];select_segment(&p->animation,&p->segment,root(s,19));}
  if(a->life>damage){a->life-=damage;a->hp=1;a->state=0;s->mode=8;game.sound=SND_HIT;select_segment(&s->animation,&s->segment,facing(a,s,5));}
  else {a->state=2;game.spawned[a->source]|=2;game.kills++;progress_score(flailer_scores[s->profile]);loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));game.sound=SND_KILL;select_segment(&s->animation,&s->segment,root(s,(u8)(PX(game.p.x)-game.cam_x)<(u8)(PX(a->x)-game.cam_x)?17:18));}
 }
 for(tries=0;tries<8;tries++){
  const AnimSegment *seg=&flailer_segments[s->segment];u16 target=seg->next;
  if(animation_step(&s->animation,seg->clip)){a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;actor_motion(a,a->vx,a->vy,s->mode);return;}
  switch(seg->event){
  case 0:target=facing(a,s,3);break;
  case 1:if((u16)(PX(a->y)+8-PX(game.p.y))<16 && near_x(a,s,1))target=facing(a,s,5);break;
  case 2:target=facing(a,s,5);break;
  case 3:target=launch(a,s);break;
  case 4:
   s->armed=0;
   if(near_x(a,s,0))target=launch(a,s);
   else if(!ground(a,16,32))target=fall_start(a,s);
   else if(ground(a,s->left?0:32,16)){
    if(ground(a,s->left?0:32,-16))target=sided(s,11);
    else {s->animation.vy=-4;s->fraction=0;target=sided(s,13);}
   }break;
  case 5:target=falling(a,s,1);break;
  case 6:target=falling(a,s,0);break;
  default:a->active=0;game.spawned[a->source]^=1;return;
  }
  select_segment(&s->animation,&s->segment,target);
 }
}
const AnimFrame *flailer_frame(u16 slot){FlailerState *s=&flailers[slot];return s->animation.remaining?animation_current(&s->animation,flailer_segments[s->segment].clip):0;}
u8 flailer_weapons_tick(void){u8 occupied=0;
 u16 i,tries,end=flailer_weapons_occupied?flailer_weapons_occupied:MAX_ACTORS;for(i=0;i<end;i++){FlailerWeapon *p=&flailer_weapons[i];if(!p->active)continue;occupied=i+1;
  if(p->pending){p->pending=0;p->dying=1;select_segment(&p->animation,&p->segment,flailer_roots[p->profile][20]);}
  for(tries=0;tries<8;tries++){
   const AnimSegment *seg=&flailer_segments[p->segment];
   if(animation_step(&p->animation,seg->clip)){p->x+=p->animation.vx;if(!small_actor_axis_active(p->x-game.cam_x,0)){p->active=0;break;}p->y+=p->animation.vy;if(!small_actor_axis_active(p->y-game.cam_y,1))p->active=0;break;}
   if(seg->event!=8){p->active=0;break;}game.sound=SND_ATTACK;select_segment(&p->animation,&p->segment,seg->next);
  }
 }
flailer_weapons_occupied=occupied;return occupied;
}
u8 flailer_weapon_hit(s16 x,s16 y,u8 kind){
 u16 i;u8 width=8+(kind?dagger_width:8),height=4+(kind?dagger_height:4);
 if(kind && (game.frame&1))return 0;
 for(i=0;i<(flailer_weapons_occupied?flailer_weapons_occupied:MAX_ACTORS);i++){
  FlailerWeapon *p=&flailer_weapons[i];s16 dx,dy;
  if(!p->active || p->pending || p->dying)continue;
  dx=x-p->x;dy=y-p->y;
  if(dx>=-width && dx<=width && dy>=-height && dy<=height){p->pending=1;return 1;}
 }
 return 0;
}
u8 flailer_weapon_contact(u16 slot){FlailerWeapon *p=&flailer_weapons[slot];if(!p->active || p->pending || p->dying || (game.frame&1))return 0;return player_contact(p->x,p->y,8,4)?(p->profile?1:2):0;}
void flailer_weapons_clear_attack(void){u16 i;for(i=0;i<MAX_ACTORS;i++)if(flailer_weapons[i].active)flailer_weapons[i].pending=1;}
const AnimFrame *flailer_weapon_frame(u16 slot){FlailerWeapon *p=&flailer_weapons[slot];return p->active && p->animation.remaining?animation_current(&p->animation,flailer_segments[p->segment].clip):0;}

/* Keep ordinary held-frame motion outside the transition interpreter. */
void flailer_step(u16 slot) {
 FlailerState *s=&flailers[slot];
 if(!s->pending && animation_hold_step(&s->animation,flailer_segments[s->segment].clip)){
  Actor *a=&game.actors[slot];a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;actor_motion(a,a->vx,a->vy,s->mode);return;
 }
 flailer_transition(slot);
}
