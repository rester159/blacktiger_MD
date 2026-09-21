#ifndef BOSS_RUSH_H
#define BOSS_RUSH_H
#include "game.h"
/* Continuous upper palace hall; floor matches the original map at Y=256. */
#define RUSH_X 576
#define RUSH_Y 64
#define RUSH_WIDTH 768
#define RUSH_FLOOR 256
#define RUSH_START_X (RUSH_X+(RUSH_WIDTH-32)/2)
#define RUSH_CAMERA_X (RUSH_START_X-112)
typedef struct {u8 active,stage,shopping,complete;u16 reward;} BossRush;
extern BossRush boss_rush;
void boss_rush_prepare(void);
void boss_rush_actor_bounds(Actor *actor,s32 previous_x);
void boss_rush_win(void);
void boss_rush_shop_exit(void);
#endif
