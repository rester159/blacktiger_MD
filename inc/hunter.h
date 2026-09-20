#ifndef HUNTER_H
#define HUNTER_H
#include "animation.h"
typedef AnimSegment HunterSegment;
void hunter_spawn(u16 slot,u8 boss);
u8 hunter_hit(u16 slot,u8 damage);
u8 hunter_vulnerable(u16 slot);
u8 hunter_contact(u16 slot);
u8 hunter_present(void);
u8 hunter_locked(void);
void hunter_screen_attack(u16 slot);
void hunter_step(u16 slot);
const AnimFrame *hunter_frame(u16 slot);
#endif
