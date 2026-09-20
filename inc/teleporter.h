#ifndef TELEPORTER_H
#define TELEPORTER_H
#include "animation.h"
void teleporter_reset(void);
u8 teleporter_prepare(u16 row,s16 *x,s16 *y);
u8 teleporter_contact(u16 slot);
void teleporter_screen_attack(u16 slot);
void teleporter_spawn(u16 slot);
u8 teleporter_hit(u16 slot,u8 damage);
u8 teleporter_vulnerable(u16 slot);
void teleporter_step(u16 slot);
const AnimFrame *teleporter_frame(u16 slot);
#endif
