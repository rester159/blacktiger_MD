#ifndef PLAYER_DEATH_H
#define PLAYER_DEATH_H
#include "game.h"
typedef struct {
    u16 code[2];
    u8 ticks,palette[2],flip[2];
    s8 dx[2],dy[2];
} PlayerDeathFrame;
typedef struct {u8 x[2],y[2],profile,index,remaining,active,finished;} PlayerDeath;
extern PlayerDeath player_death;
void player_death_reset(void);
void player_death_start(u8 hazard,u8 left);
u8 player_death_step(void);
const PlayerDeathFrame *player_death_frame(void);
#endif
