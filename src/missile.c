#include "missile.h"
Missile missiles[MAX_MISSILES];
void missile_reset(void) {u16 i;for(i=0;i<MAX_MISSILES;i++)missiles[i].active=0;}
u8 missile_spawn(s16 x,s16 y,const AnimClip *flight,const AnimClip *death,u8 damage,u8 width,u8 height) {
 u16 i;for(i=0;i<MAX_MISSILES;i++)if(!missiles[i].active) {
  Missile *m=&missiles[i];animation_reset(&m->animation);m->clip=flight;m->death=death;
  m->x=x;m->y=y;m->active=1;m->dying=0;m->damage=damage;m->width=width;m->height=height;return 1;
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
 m->dying=1;m->clip=m->death;animation_reset(&m->animation);return 1;
}
u8 missile_hit_at(s16 x,s16 y,u8 damage) {
 u16 i;for(i=0;i<MAX_MISSILES;i++) {
  Missile *m=&missiles[i];s16 dx=x-m->x,dy=y-m->y;
  /* Player projectile size remains provisional with the current native weapons. */
  if(m->active && !m->dying && dx>=-(m->width+4) && dx<=m->width+4 && dy>=-(m->height+4) && dy<=m->height+4)
   return missile_hit(i,damage);
 }
 return 0;
}
const AnimFrame *missile_frame(u16 slot) {
 Missile *m=&missiles[slot];return m->active && m->animation.remaining?animation_current(&m->animation,m->clip):0;
}
