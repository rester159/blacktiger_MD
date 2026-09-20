#ifndef ERUPTION_H
#define ERUPTION_H
#include "animation.h"
void eruption_reset(void);
u8 eruption_prepare(u16 row,s16 x,s16 y);
void eruption_spawn(u16 slot);
void eruption_step(u16 slot);
u8 eruption_contact(u16 slot);
const AnimFrame *eruption_frame(u16 slot);
#endif
