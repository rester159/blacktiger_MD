#ifndef WORLD_H
#define WORLD_H
#include "animation.h"
extern u8 world_opened, world_rows[256];
void world_reset(void);
void world_restart(void);
void world_tick(void);
u16 world_override(u16 x,u16 y,u16 original,u8 opened);
u16 world_word(u16 x, u16 y, u16 original);
u8 world_collision(u16 cell, u8 original);
void hidden_spawn(u16 slot);
void hidden_break(u16 slot);
u8 hidden_step(u16 slot, u8 contact);
const AnimFrame *hidden_frame(u16 slot);
const AnimFrame *world_effect(u16 patch);
#endif
