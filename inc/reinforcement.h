#ifndef REINFORCEMENT_H
#define REINFORCEMENT_H
#include "game.h"
/* Secondary source-row bytes survive a checkpoint restart. */
void reinforcement_reset(void);
u8 reinforcement_prepare(u16 row,s16 x,s16 y);
#endif
