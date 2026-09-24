#include "dragon.h"
#include "assets.h"
#include "loot.h"
#include "progress.h"
#include "sentry.h"
#include "shop.h"
static DragonState dragons[MAX_ACTORS];
static void select_segment(DragonState *s,u16 n){s8 vx=s->animation.vx,vy=s->animation.vy;animation_reset(&s->animation);s->animation.vx=vx;s->animation.vy=vy;s->segment=n;}
void dragon_spawn(u16 slot,u8 profile){Actor *a=&game.actors[slot];DragonState *s=&dragons[slot];*s=(DragonState){0};s->profile=profile;s->mode=24;s->left=1;s->segment=dragon_roots[0];a->hp=dragon_health[profile];a->life=dragon_layers[profile];a->state=0;}
u8 dragon_hit(u16 slot,u8 damage){Actor *a=&game.actors[slot];DragonState *s=&dragons[slot];if(!damage || (s->mode&1) || a->state==2)return 0;if(a->hp>damage)a->hp-=damage;else{s->pending=1;s->mode|=3;a->state=1;}return 1;}
static u16 weighted(DragonState *s,u8 profile){s->alternate=!s->alternate;return dragon_choices[profile][(s->left?0:2)+s->alternate][(loot_random>>8)&15];}
static u16 turn(Actor *a,DragonState *s,u8 profile){
 u16 x=(u16)(PX(a->x)-game.cam_x)+(s->left?0:128),px=PX(game.p.x)-game.cam_x;u8 left=(u16)(x+256)>=(u16)(px+256);
 if(s->profile==2 && profile!=1)s->weak_x=left?-56:56;
 if(left!=s->left){s->left=left;s->alternate=0;return dragon_roots[2+left];}return weighted(s,profile);
}
static u16 choose(Actor *a,DragonState *s,u8 countdown,u8 profile){
 u16 y=PX(a->y)-game.cam_y,x=(u16)(PX(a->x)-game.cam_x)+(s->left?0:128);
 if(countdown && s->recovery && --s->recovery==1)s->mode=24;
 if(y>>8)return dragon_roots[((y>>8)==255?4:6)+s->left];
 if(y>=112)return dragon_roots[6+s->left];
 if(x>>8)return turn(a,s,profile);
 return weighted(s,profile);
}
static u16 aim(Actor *a,DragonState *s){
 u8 d=aim_direction(PX(a->x)-game.cam_x+(s->left?0:112),PX(a->y)-game.cam_y,PX(game.p.x)-game.cam_x,PX(game.p.y)-game.cam_y);
 if(s->left){if(d<10)d=10;else if(d>=18)d=17;s->direction=d;return dragon_aims[8+d-10];}
 if(d>=7)d=d<16?6:31;
 s->direction=d;return dragon_aims[(d+1)&31];
}
static void orb(Actor *a,DragonState *s,DragonLaunch launch){
 u8 n=s->left?s->direction-10:(s->direction+1)&31;
 s->alternate=s->left?(n<3?28:n<5?24:16):(n<3?16:n<5?24:28);
 launch(0,n+(s->left?8:0),PX(a->x)+(s->left?0:112),PX(a->y)+s->alternate,s->profile,s->left);
}
void dragon_step(u16 slot,DragonLaunch launch){
 Actor *a=&game.actors[slot];DragonState *s=&dragons[slot];u16 tries;
 if(s->pending){s->pending=0;select_segment(s,dragon_roots[s->engaged?10:1]);}
 for(tries=0;tries<16;tries++){
  const DragonSegment *seg=&dragon_segments[s->segment];u16 target=seg->next[0];u16 x=PX(a->x)-game.cam_x,y=PX(a->y)-game.cam_y;
  if(animation_step(&s->animation,seg->clip)){a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;a->y+=a->vy;return;}
  switch(seg->event){
  case 0:if((u8)(PX(game.p.x)+48-PX(a->x))<96)target=dragon_roots[1];break;
  case 1:s->mode=24;s->engaged=1;if(s->profile==2)s->weak_x=-56;break;
  case 2:target=choose(a,s,1,s->profile);break;
  case 3:if(!(y>>8) && y>=112)target=choose(a,s,1,s->profile);break;
  case 4:if((u16)(x+(s->left?0:128))>>8)target=turn(a,s,0);break;
  case 5:if(!(y>>8) && y>=16 && y<176 && !((u16)(x+(s->left?0:112))>>8) && ((loot_random>>8)&1))target=aim(a,s);break;
  case 6:orb(a,s,launch);break;
  case 7:
   if(!s->profile){s->alternate=!s->alternate;target=choose(a,s,1,s->profile);}
   else{if(s->left){if(++s->direction>=18)s->direction=17;}else{s->direction=(s->direction+1)&31;if(s->direction>=7)s->direction=5;}orb(a,s,launch);}break;
  case 8:target=s->profile?dragon_roots[8+s->left]:aim(a,s);break;
  case 9:
   if(--a->life){a->hp=dragon_health[s->profile];a->state=0;s->recovery=3;target=dragon_roots[s->left?11:12];}
   else{a->state=2;game.boss_dead=1;shop_poison=0;game.spawned[a->source]|=2;game.kills++;progress_score(dragon_score);target=dragon_roots[s->left?13:14];}break;
  case 10:game.sound=SND_KILL;break;
  case 11:if((u8)y>=112)target=seg->next[1];break;
  case 12:game_boss_clear();return;
  case 13:case 15:{u8 px=PX(game.p.x)-game.cam_x,ax=x,d=px>=ax?px-ax:ax-px;target=dragon_distances[(s->left?0:3)+(d<32?0:d<96?1:2)];break;}
  case 14:case 16:launch(1,0,PX(a->x)+(s->left?22:86),PX(a->y)+16,s->profile,s->left);break;
  /* These callbacks deliberately select a fixed profile, even on another dragon. */
  case 17:case 18:target=choose(a,s,0,seg->event-16);break;
  case 19:target=aim(a,s);break;
  case 20:s->alternate=!s->alternate;target=choose(a,s,1,s->profile);break;
  }
  select_segment(s,target);
 }
}
const AnimFrame *dragon_frame(u16 slot){DragonState *s=&dragons[slot];return s->animation.remaining?animation_current(&s->animation,dragon_segments[s->segment].clip):0;}
u8 dragon_present(void){u16 i;for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && dragon_kinds[game.actors[i].def])return 1;return 0;}
u8 dragon_locked(void){u16 i;for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && dragon_kinds[game.actors[i].def] && game.actors[i].state==2)return 1;return 0;}
void dragon_screen_attack(u16 slot){Actor *a=&game.actors[slot];DragonState *s=&dragons[slot];if(a->state!=2){a->hp=1;a->life=1;s->pending=1;s->mode|=3;a->state=1;}}
static LargeContactShape shape(DragonState *s){LargeContactShape result=dragon_shapes[s->profile];result.weak_x=s->weak_x;return result;}
u8 dragon_player_contact(u16 slot){Actor *a=&game.actors[slot];DragonState *s=&dragons[slot];LargeContactShape box=shape(s);return !(s->mode&2) && (game.frame&1) && wide_player_contact(&box,PX(a->x)-game.cam_x,PX(a->y)-game.cam_y,PX(game.p.x)-game.cam_x,PX(game.p.y)-game.cam_y,contact_player_width,contact_player_height,game.player_low);}
u8 dragon_weapon_contact(u16 slot,s16 x,s16 y,u8 dagger){Actor *a=&game.actors[slot];DragonState *s=&dragons[slot];LargeContactShape box=shape(s);if((s->mode&1) || a->state==2)return 0;return wide_weapon_contact(&box,PX(a->x)-game.cam_x,PX(a->y)-game.cam_y,x-game.cam_x,y-game.cam_y,dagger?dagger_width:8,dagger?dagger_height:4,dagger);}
