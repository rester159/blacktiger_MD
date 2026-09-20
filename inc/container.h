#ifndef CONTAINER_H
#define CONTAINER_H
#include "game.h"
u16 container_shuffle(u8 round,u16 seed,u8 *out);
void container_new(void);
void container_round(u8 round);
u8 container_content(u8 persistent);
#endif
