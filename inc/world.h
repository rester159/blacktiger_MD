#ifndef WORLD_H
#define WORLD_H
#include "animation.h"
#define WORLD_BOSS_CLOSED 128
typedef struct { u16 cell, words[4]; u8 collision, pad; } BossTerrainPatch;
typedef struct { const BossTerrainPatch *patches; u16 count; } BossTerrain;
extern const BossTerrain boss_terrain[8];
extern u8 world_opened, world_rows[256];
void world_close_boss(void);
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
