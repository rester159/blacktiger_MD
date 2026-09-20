#include "dragon_shot.h"
#include "assets.h"
#include "hazard.h"
DragonShot dragon_shots[24];
static void select_segment(DragonShot *p,u16 n){s8 vx=p->animation.vx,vy=p->animation.vy;animation_reset(&p->animation);p->animation.vx=vx;p->animation.vy=vy;p->segment=n;}
void dragon_shots_reset(void){u16 i;for(i=0;i<24;i++)dragon_shots[i].active=0;}
static u8 spawn(u8 kind,u8 direction,s16 x,s16 y,u8 profile,u8 left){
 u16 i,first=kind==2?16:0,end=kind==2?24:16;
 for(i=first;i<end;i++)if(!dragon_shots[i].active){DragonShot *p=&dragon_shots[i];*p=(DragonShot){0};p->active=1;p->kind=kind;p->mode=kind==0?8:kind==1?11:25;p->profile=profile;p->left=left;p->x=x;p->y=y;p->segment=dragon_shot_roots[kind==0?direction:kind==1?16+left:19];return 1;}
 return 0;
}
void dragon_projectile_spawn(u8 kind,u8 direction,s16 x,s16 y,u8 profile,u8 left){if(kind<2 && (kind || direction<16))spawn(kind,direction,x,y,profile,left);}
u8 dragon_shot_hit_slot(u16 slot,u8 damage){DragonShot *p=&dragon_shots[slot];if(!damage || !p->active || (p->mode&1))return 0;p->pending=1;p->mode|=3;return 1;}
void dragon_shots_step(void){
 u16 i;for(i=0;i<24;i++){DragonShot *p=&dragon_shots[i];u16 tries;if(!p->active)continue;
  if(p->pending==2){p->active=0;continue;}
  if(p->pending){p->pending=0;select_segment(p,dragon_shot_roots[18]);}
  for(tries=0;tries<6;tries++){
   const DragonSegment *seg=&dragon_shot_segments[p->segment];u16 target=seg->next[0];
   if(animation_tick(&p->animation,seg->clip)){
    p->x+=p->animation.vx;if(!(p->mode&16) && !small_actor_axis_active(p->x-game.cam_x,0)){p->active=0;break;}
    p->y+=p->animation.vy;if(!(p->mode&16) && !small_actor_axis_active(p->y-game.cam_y,1))p->active=0;break;
   }
   switch(seg->event){
   case 0:{u8 t=terrain(p->x+8,p->y+8);if(t==2 || t==3){p->mode=11;target=dragon_shot_roots[18];}break;}
   case 1:if(spawn(2,0,p->x-8,p->y-16,p->profile,p->left)){target=dragon_shot_roots[20];game.sound=SND_HIT;}break;
   case 2:p->mode=9;break;
   case 3:p->mode=27;break;
   case 4:{u8 t=terrain(p->x+8,p->y+8);if(t==2 || t==3)dragon_wave_spawn(p->x,p->left,p->profile==2);else target=seg->next[1];break;}
   default:p->active=0;break;
   }
   if(!p->active)break;
   select_segment(p,target);
  }
 }
}
u8 dragon_shot_contact(u16 slot){
 DragonShot *p=&dragon_shots[slot];u8 medium=p->kind==2;
 if(!p->active || (p->mode&2) || (game.frame&1) || !player_contact(p->x+(medium?8:0),p->y+(medium?8:0),medium?12:6,medium?12:6))return 0;
 if(medium)return 1;
 if(game.p.invincible || p->pending)return 0;
 /* Source contact 41 creates the damaging explosion at the player's origin. */
 spawn(2,0,PX(game.p.x),PX(game.p.y),p->profile,p->left);
 /* Retire next tick, preserving this frame. On pool exhaustion, discard the orb
    instead of following the source's misaligned animation pointer. */
 p->pending=2;return 0;
}
const AnimFrame *dragon_shot_frame(u16 slot){DragonShot *p=&dragon_shots[slot];return p->active && p->animation.remaining?animation_current(&p->animation,dragon_shot_segments[p->segment].clip):0;}
u8 dragon_shot_hit(s16 x,s16 y,u8 damage,u8 dagger){u16 i;if(dagger && (game.frame&1))return 0;for(i=0;i<16;i++){DragonShot *p=&dragon_shots[i];s16 dx=x-p->x,dy=y-p->y;u8 w=6+(dagger?dagger_width:4),h=6+(dagger?dagger_height:4);if(p->active && !(p->mode&1) && dx>=-(s16)w && dx<=w && dy>=-(s16)h && dy<=h)return dragon_shot_hit_slot(i,damage);}return 0;}
