#ifndef INTRO_H
#define INTRO_H
#include "game.h"
extern u16 intro_tick;
void intro_start(void);
u8 intro_step(u16 pressed);
void intro_video(void);
#endif
