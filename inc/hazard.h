#ifndef HAZARD_H
#define HAZARD_H
#include "game.h"
u8 player_contact(s16 x, s16 y, u8 half_width, u8 half_height);
u8 actor_contact(u16 slot);
u8 actor_dagger_contact(u16 slot,s16 x,s16 y);
void hazard_step(u16 slot);
#endif
