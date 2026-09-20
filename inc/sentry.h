#ifndef SENTRY_H
#define SENTRY_H
#include "animation.h"
u8 aim_direction(u8 x, u8 y, u8 target_x, u8 target_y);
void sentry_spawn(u16 slot);
u8 sentry_hit(u16 slot, u8 damage);
void sentry_step(u16 slot);
const AnimFrame *sentry_frame(u16 slot);
#endif
