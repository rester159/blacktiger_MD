#ifndef PLAYER_DAGGER_H
#define PLAYER_DAGGER_H
#include "animation.h"
#define PLAYER_DAGGERS 9
typedef struct {
    AnimState animation;
    u16 segment;
    s16 x,y;
    u8 active,pending,hidden;
} PlayerDagger;
extern PlayerDagger player_daggers[PLAYER_DAGGERS];
void player_daggers_reset(void);
u8 player_daggers_launch(s16 x,s16 y,u8 left,u8 low);
void player_daggers_step(void);
void player_dagger_hit(u16 slot,u8 terrain_effect);
const AnimFrame *player_dagger_frame(u16 slot);
#endif
