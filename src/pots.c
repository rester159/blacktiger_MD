#include "pots.h"
#include "assets.h"
#include "loot.h"
#include "container.h"
#include "progress.h"
#include "hazard.h"
#include "boss_rush.h"
#include "crawler.h"
#include "statue.h"
#include "reinforcement_body.h"
Pot pots[MAX_POTS],pot_puffs[8];
u8 pots_end,pot_puffs_end,pot_contents[32];
static u8 pot_opened[32],pot_collected[32];
static u8 rotate(u8 v){return (v>>1)|(v<<7);}
u16 pots_shuffle(u8 round,u16 seed,u8 *out){
 u16 i;for(i=0;i<32;i++)out[i]=pot_initial[round][i];
 for(i=0;i<16;i++){
  u8 a=rotate(seed>>8)&31,b=rotate((u8)(rotate(seed>>8)+(u8)seed))&31,t=out[a];
  out[a]=out[b];out[b]=t;seed=seed*259;seed=seed*259;
 }return seed;
}
void pots_clear(void){u16 i;for(i=0;i<MAX_POTS;i++)pots[i].active=0;for(i=0;i<8;i++)pot_puffs[i].active=0;pots_end=pot_puffs_end=0;}
void pots_round(u8 preserve){
 u16 i;pots_clear();if(preserve)return;
 for(i=0;i<32;i++)pot_opened[i]=pot_collected[i]=0;
 loot_random=pots_shuffle(game.round,loot_random,pot_contents);
}
static void select_clip(Pot *p,u16 segment){animation_reset(&p->animation);p->segment=segment;}
static void puff(Pot *p){
 u16 i;for(i=0;i<8;i++)if(!pot_puffs[i].active){Pot *q=&pot_puffs[i];*q=(Pot){0};q->x=p->x-8;q->y=p->y-16;q->active=1;if(pot_puffs_end<=i)pot_puffs_end=i+1;select_clip(q,pot_puff);break;}
}
static void trap(Pot *p){
 u16 i;for(i=0;i<MAX_ACTORS;i++)if(!game.actors[i].active){
  Actor *a=&game.actors[i];u8 kind=p->kind-12;
  /* Slot 159 is reserved for transient pot enemies, never a level row. */
  *a=(Actor){0};a->active=1;a->source=POT_TRAP_SOURCE;a->def=pot_trap_defs[kind];
  a->hp=actor_defs[a->def].hp;a->x=(p->x-8)*FX;a->y=(p->y-16)*FX;
  a->face=PX(game.p.x)<p->x?-1:1;
  if(kind==0)crawler_spawn(i,0);
  else if(kind==1)statue_spawn(i);
  else if(kind==2)boss_spawn(i);
  else reinforcement_body_spawn(i);
  return;
 }
}
static void collect(Pot *p){
 pot_collected[p->id]=1;p->active=0;
 if(p->kind>=4 && p->kind<=9)game.coins+=loot_values[p->kind-3];
 else if(p->kind==10){if(container_keys<99)container_keys++;}
 else if(p->kind==11)game.time+=30;
 progress_score(p->kind==10?10:5);game_sound(p->kind>=10?5:6);
}
void pots_tick(u8 bosses){
 u16 i,width_mask=rounds[game.round].width-1,height_mask=rounds[game.round].height-1;
 if(boss_rush.active || (bosses&1)){pots_clear();return;}
 for(i=0;i<pot_puffs_end;i++)if(pot_puffs[i].active && !animation_step(&pot_puffs[i].animation,pot_segments[pot_puff].clip))pot_puffs[i].active=0;
 while(pot_puffs_end && !pot_puffs[pot_puffs_end-1].active)--pot_puffs_end;
 for(i=game.frame&3;i<pot_counts[game.round];i+=4){
  const PotPlacement *row=&pot_placements[game.round][i];Pot *p=&pots[i];s16 x,y;u16 j,dx,dy;
  if(p->active || pot_collected[row->id])continue;
  /* Power-of-two terrain wrap, relative to the activation rectangle. */
  dx=(row->x-game.cam_x+16)&width_mask;if(dx>288)continue;
  dy=row->y-game.cam_y+16;if(WORLD_WRAP_Y)dy&=height_mask;if(dy>256)continue;
  x=(s16)game.cam_x+dx-16;y=(s16)game.cam_y+dy-16;
  /* Only a newly eligible placement needs a shared-ID ownership check. */
  for(j=0;j<pots_end;j++)if(pots[j].active && pots[j].id==row->id)break;
  if(j<pots_end)continue;
  *p=(Pot){0};p->x=x;p->y=y;p->id=row->id;p->kind=pot_contents[row->id];p->hits=2;p->active=1;
  p->phase=pot_opened[p->id]?2:0;select_clip(p,pot_roots[p->kind-2][p->phase==2?1:0]);
  if(pots_end<=i)pots_end=i+1;
 }
 for(i=0;i<pots_end;i++){
  Pot *p=&pots[i];u16 tries;if(!p->active)continue;
  if(!small_actor_axis_active(p->x-game.cam_x,0)||!small_actor_axis_active(p->y-game.cam_y,1)){p->active=0;continue;}
  if(p->pending){p->pending=0;if(--p->hits){select_clip(p,pot_cracked);game_sound(14);}
   else{p->phase=1;select_clip(p,pot_roots[p->kind-2][2]);progress_score(pot_score);game_sound(8);}}
  for(tries=0;tries<4;tries++){
   const AnimSegment *seg=&pot_segments[p->segment];
   if(animation_step(&p->animation,seg->clip))break;
   if(seg->event==2){pot_opened[p->id]=1;p->phase=2;select_clip(p,pot_roots[p->kind-2][1]);}
   else if(seg->event==3){pot_collected[p->id]=1;p->active=0;break;}
   else if(seg->event==4){puff(p);game_sound(19);select_clip(p,seg->next);}
   else if(seg->event==5){trap(p);select_clip(p,seg->next);}
   else{p->active=0;break;}
  }
  if(p->active && p->phase==2 && (game.frame&1) && p->kind>=4 && p->kind<=11 && player_contact(p->x,p->y,8,8))collect(p);
 }
 while(pots_end && !pots[pots_end-1].active)--pots_end;
}
u8 pots_weapon(s16 x,s16 y,u8 dagger){
 u16 i;if(dagger && (game.frame&1))return 0;
 for(i=0;i<pots_end;i++){
  Pot *p=&pots[i];s16 dx,dy;u16 w=8+(dagger?dagger_width:8),h=8+(dagger?dagger_height:4);
  if(!p->active || p->phase || p->pending || (u16)(p->x-game.cam_x)>=256 || (dagger && (u16)(x-game.cam_x)>=256))continue;
  dx=(u8)(x-game.cam_x)-(u8)(p->x-game.cam_x);dy=(u8)(y-game.cam_y)-(u8)(p->y-game.cam_y);
  if((u16)(dx+w)<=2*w && (u16)(dy+h)<=2*h){p->pending=1;return 1;}
 }return 0;
}
const AnimFrame *pot_frame(u16 slot){Pot *p=&pots[slot];return p->active?animation_current(&p->animation,pot_segments[p->segment].clip):0;}
