#ifndef TELEPORTER_H
#define TELEPORTER_H
#include "animation.h"
void teleporter_spawn(u16 slot);
u8 teleporter_hit(u16 slot,u8 damage);
u8 teleporter_vulnerable(u16 slot);
void teleporter_step(u16 slot);
const AnimFrame *teleporter_frame(u16 slot);
#endif
