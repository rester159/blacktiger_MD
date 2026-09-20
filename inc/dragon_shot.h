#ifndef DRAGON_SHOT_H
#define DRAGON_SHOT_H
#include "dragon.h"
typedef struct {AnimState animation;u16 segment;s16 x,y;u8 active,kind,mode,left,profile,pending;} DragonShot;
extern DragonShot dragon_shots[24];
extern const DragonSegment dragon_shot_segments[];
extern const u16 dragon_shot_roots[21];
void dragon_shots_reset(void);
void dragon_projectile_spawn(u8 kind,u8 direction,s16 x,s16 y,u8 profile,u8 left);
void dragon_shots_step(void);
u8 dragon_shot_hit_slot(u16 slot,u8 damage);
u8 dragon_shot_contact(u16 slot);
const AnimFrame *dragon_shot_frame(u16 slot);
u8 dragon_shot_hit(s16 x,s16 y,u8 damage,u8 dagger);
#endif
