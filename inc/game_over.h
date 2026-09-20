#ifndef GAME_OVER_H
#define GAME_OVER_H
#include "game.h"
typedef struct {u16 remaining;u8 phase,digit;} GameOver;
extern GameOver game_over;
void game_over_reset(void);
void game_over_start(void);
/* 0: display, 1: continue accepted, 2: offer expired. */
u8 game_over_step(u16 input);
#endif
