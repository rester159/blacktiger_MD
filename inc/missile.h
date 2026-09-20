#ifndef MISSILE_H
#define MISSILE_H
#include "animation.h"
#define MAX_MISSILES 12
typedef struct {
 AnimState animation;
 const AnimClip *clip,*death;
 s16 x,y;
 u8 active,dying,damage,width,height,health;
} Missile;
extern Missile missiles[MAX_MISSILES];
void missile_reset(void);
u8 missile_spawn(s16 x,s16 y,const AnimClip *flight,const AnimClip *death,u8 damage,u8 width,u8 height,u8 health);
void missile_tick(void);
u8 missile_hit(u16 slot,u8 damage);
u8 missile_hit_at(s16 x,s16 y,u8 damage,u8 kind);
u8 missile_player_contact(u16 slot);
const AnimFrame *missile_frame(u16 slot);
#endif
