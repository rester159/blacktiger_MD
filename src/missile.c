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
u8 missile_tick(void) {
 u8 occupied=0;
 u16 i;for(i=0;i<MAX_MISSILES;i++) {
  Missile *m=&missiles[i];if(!m->active)continue;occupied=1;
  if(animation_tick(&m->animation,m->clip)) {
   m->x+=m->animation.vx;
   if(!small_actor_axis_active(m->x-game.cam_x,0)){m->active=0;continue;}
   m->y+=m->animation.vy;
   if(!small_actor_axis_active(m->y-game.cam_y,1))m->active=0;
  }
  else m->active=0;
 }
 return occupied;
}
u8 missile_hit(u16 slot,u8 damage) {
 Missile *m=&missiles[slot];if(!m->active || m->dying || !damage)return 0;
 if(m->health>damage){m->health-=damage;return 1;}
 m->dying=1;m->clip=m->death;animation_reset(&m->animation);return 1;
}
u8 missile_hit_at(s16 x,s16 y,u8 damage,u8 kind) {
 u16 i;u8 width=kind?dagger_width:8,height=kind?dagger_height:4;
 if(kind && (game.frame&1))return 0;for(i=0;i<MAX_MISSILES;i++) {
  Missile *m=&missiles[i];s16 dx=x-m->x,dy=y-m->y;
  /* Chain links use half-width 8; daggers use the source 4/2 box. */
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
 dx=PX(game.p.x)+8-m->x;dy=PX(game.p.y)+(game.player_low?18:8)-m->y;
 width=(game.player_low?3:m->width)+contact_player_width;height=(game.player_low?3:m->height)+contact_player_height;
 return dx>=-width && dx<=width && dy>=-height && dy<=height;
}
