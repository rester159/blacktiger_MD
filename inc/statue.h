#ifndef STATUE_H
#define STATUE_H
#include "animation.h"
typedef AnimSegment StatueSegment;
void statue_spawn(u16 slot);
u8 statue_contact(u16 slot);
u8 statue_vulnerable(u16 slot);
u8 statue_hit(u16 slot,u8 damage);
void statue_screen_attack(u16 slot);
void statue_step(u16 slot);
const AnimFrame *statue_frame(u16 slot);
#endif
