#include "boss.h"
#include "assets.h"
#include "loot.h"
typedef struct {AnimState animation;u16 segment;u8 left,fraction,worn,vulnerable,pending,dying,part,owner;} BossState;
static BossState bosses[MAX_ACTORS];
static const u16 *roots(const BossState *s) {return s->part?boss_upper_roots:boss_roots;}
static const BossSegment *segments(const BossState *s) {return s->part?boss_upper_segments:boss_segments;}
static void init(u16 slot,u8 part,u8 owner) {
 Actor *a=&game.actors[slot];BossState *s=&bosses[slot];
 animation_reset(&s->animation);s->part=part;s->owner=owner;
 s->segment=roots(s)[part>1?part+13:0];
 s->left=s->fraction=s->worn=s->vulnerable=s->pending=s->dying=0;
 a->life=part?boss_upper_layers:layered_boss_layers[layered_boss_kinds[a->def]-1];
 if(part)a->hp=boss_upper_health[layered_boss_kinds[a->def]-1];
}
void boss_spawn(u16 slot) {
 Actor *a=&game.actors[slot];u8 kind=layered_boss_kinds[a->def];u16 i;u8 part=1;
 if(!kind)return;
 init(slot,0,slot);
 for(i=slot+1;i<MAX_ACTORS && part<boss_component_counts[kind-1];i++)if(!game.actors[i].active) {
  game.actors[i]=*a;game.actors[i].y-=part*22*FX;init(i,part++,slot);
 }
}
u8 boss_present(void) {
 u16 i;for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && layered_boss_kinds[game.actors[i].def] && !bosses[i].part)return 1;
 return 0;
}
u8 boss_contact_damage(u16 slot) {return bosses[slot].part?boss_upper_damage:actor_damage[game.actors[slot].def];}
u8 boss_break_layer(Actor *a) {
 if(!layered_boss_kinds[a->def])return 0;
 if(a->life>1){a->life--;a->hp=bosses[a-game.actors].part?boss_upper_reset_health:layered_boss_reset_health;game.sound=SND_HIT;return 1;}
 a->life=0;return 0;
}

u8 boss_hit(u16 slot,u8 damage) {
 Actor *a=&game.actors[slot];BossState *s=&bosses[slot];
 if(!layered_boss_kinds[a->def])return 0;
 if(!s->pending && !s->dying) {
  if(a->hp>damage)a->hp-=damage;
  else {s->pending=1;s->vulnerable=0;a->state=1;}
 }
 return 1;
}
u8 boss_vulnerable(u16 slot) {return bosses[slot].vulnerable && !bosses[slot].pending && !bosses[slot].dying;}
u8 boss_locked(void) {
 u16 i;for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && layered_boss_kinds[game.actors[i].def] && !bosses[i].part && bosses[i].dying)return 1;
 return 0;
}
static void select_segment(BossState *s,u16 segment) {
 s8 vx=s->animation.vx,vy=s->animation.vy;animation_reset(&s->animation);
 s->animation.vx=vx;s->animation.vy=vy;s->segment=segment;
}
static u8 ground(u16 slot,s16 dx,s16 dy) {
 Actor *a=&game.actors[slot];u8 t=terrain(PX(a->x)+dx,PX(a->y)+dy);return t==2 || t==3;
}
static void gravity(BossState *s,u16 acceleration) {
 u16 v=((u16)(u8)s->animation.vy<<8)+s->fraction+acceleration;
 if((v>>8)==5)v=1280;
 s->animation.vy=v>>8;s->fraction=v&255;
}
static u16 choose(u16 slot) {
 BossState *s=&bosses[slot];u8 action=(s->part?boss_upper_choices:boss_choices)[(loot_random>>8)&15],left;
 s->left=(u16)PX(game.actors[slot].x)>=(u16)PX(game.p.x);
 if(!action)return roots(s)[1+s->worn];
 s->animation.vy=action==3?-5:-4;s->fraction=0;
 left=s->left^(action==2);
 return roots(s)[(action==3?(left?9:7):(left?5:3))+s->worn];
}
void boss_step(u16 slot) {
 Actor *a=&game.actors[slot];BossState *s=&bosses[slot];u16 tries;
 if(s->pending) {
  s->pending=0;
  if(boss_break_layer(a)) {s->worn=1;s->vulnerable=1;a->state=0;select_segment(s,choose(slot));}
  else {
   a->state=2;game.kills++;game.sound=SND_KILL;
   if(s->part) {s->dying=2;game.score+=boss_upper_score;select_segment(s,roots(s)[13]);}
   else {
    u16 i;game.boss_dead=1;s->dying=1;s->animation.remaining=1;game.spawned[a->source]=2;
    game.score+=layered_boss_score;
    for(i=0;i<MAX_ACTORS;i++)if(game.actors[i].active && layered_boss_kinds[game.actors[i].def] && bosses[i].part && bosses[i].owner==slot && !bosses[i].dying) {
     bosses[i].pending=0;bosses[i].dying=1;bosses[i].vulnerable=0;game.actors[i].state=2;
    }
    return;
   }
  }
 } else if(s->dying==1) {s->dying=2;select_segment(s,roots(s)[13]);}
 for(tries=0;tries<8;tries++) {
  const BossSegment *seg=&segments(s)[s->segment];u16 target=seg->next[0];
  if(animation_tick(&s->animation,seg->clip)) {
   a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;a->x+=a->vx;a->y+=a->vy;return;
  }
  switch(seg->event) {
  case 0:
   if((u8)(PX(game.p.x)+80-PX(a->x))<160){s->vulnerable=1;target=seg->next[1];}
   break;
  case 1:target=choose(slot);break;
  case 2:
   if(ground(slot,s->animation.vx<0?0:32,16) || (s->animation.vy<0 && ground(slot,16,0))) {
    s->animation.vy=0;s->fraction=0;target=roots(s)[11+s->worn];
   } else if(s->animation.vy>=0 && ground(slot,16,32)) {
    s->animation.vy=-2;s->fraction=0;target=seg->next[1];
   } else gravity(s,80);
   break;
  case 3:if(ground(slot,16,32))target=choose(slot);else gravity(s,64);break;
  case 6:a->active=0;return;
  case 5:a->active=0;game.boss_dead=1;game.mode=CLEAR;game.mode_timer=180;game.sound=SND_CLEAR;return;
  default:return;
  }
  select_segment(s,target);
 }
}
const AnimFrame *boss_frame(u16 slot) {
 BossState *s=&bosses[slot];return s->animation.remaining?animation_current(&s->animation,segments(s)[s->segment].clip):0;
}
