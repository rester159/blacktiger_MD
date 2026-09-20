#ifndef ZOMBIE_H
#define ZOMBIE_H
#include "animation.h"
void zombie_reset(void);
u8 zombie_prepare_variant(u16 row,u8 variant,s16 *x,s16 *y);
u8 zombie_prepare(u16 row,s16 *x,s16 *y);
void zombie_spawn(u16 slot);
u8 zombie_hit(u16 slot,u8 damage);
void zombie_step(u16 slot);
u8 zombie_vulnerable(u16 slot);
const AnimFrame *zombie_frame(u16 slot);
#endif
