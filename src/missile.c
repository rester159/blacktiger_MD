#include "missile.h"
#include "assets.h"
Missile missiles[MAX_MISSILES];
void missile_reset(void) {u16 i;for(i=0;i<MAX_MISSILES;i++)missiles[i].active=0;}
u8 missile_spawn(s16 x,s16 y,const AnimClip *flight,const AnimClip *death,u8 damage,u8 width,u8 height,u8 health) {
 u16 i;for(i=0;i<MAX_MISSILES;i++)if(!missiles[i].active) {
  Missile *m=&missiles[i];animation_reset(&m->animation);m->clip=flight;m->death=death;
  m->x=x;m->y=y;m->active=1;m->dying=0;m->damage=damage;m->width=width;m->height=height;m->health=health;return 1;
 }
 return 0;
}
void missile_tick(void) {
 u16 i;for(i=0;i<MAX_MISSILES;i++) {
  Missile *m=&missiles[i];if(!m->active)continue;
  if(animation_tick(&m->animation,m->clip)){m->x+=m->animation.vx;m->y+=m->animation.vy;}
  else m->active=0;
 }
}
u8 missile_hit(u16 slot,u8 damage) {
 Missile *m=&missiles[slot];if(!m->active || m->dying || !damage)return 0;
 if(m->health>damage){m->health-=damage;return 1;}
 m->dying=1;m->clip=m->death;animation_reset(&m->animation);return 1;
}
u8 missile_hit_at(s16 x,s16 y,u8 damage,u8 kind) {
 u16 i;u8 width=kind?dagger_width:4,height=kind?dagger_height:4;
 if(kind && (game.frame&1))return 0;for(i=0;i<MAX_MISSILES;i++) {
  Missile *m=&missiles[i];s16 dx=x-m->x,dy=y-m->y;
  /* The native chain projectile still has provisional geometry. */
  if(m->active && !m->dying && dx>=-(m->width+width) && dx<=m->width+width && dy>=-(m->height+height) && dy<=m->height+height)
   return missile_hit(i,kind?(damage>1?damage>>1:1):damage);
 }
 return 0;
}
const AnimFrame *missile_frame(u16 slot) {
 Missile *m=&missiles[slot];return m->active && m->animation.remaining?animation_current(&m->animation,m->clip):0;
}

u8 missile_player_contact(u16 slot) {
 const Missile *m=&missiles[slot];s16 dx,dy,width,height;
 if(!m->active || m->dying || (game.frame&1))return 0;
 dx=PX(game.p.x)+8-m->x;dy=PX(game.p.y)+8-m->y;
 width=m->width+contact_player_width;height=m->height+contact_player_height;
 return dx>=-width && dx<=width && dy>=-height && dy<=height;
}
