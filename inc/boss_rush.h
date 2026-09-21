#ifndef BOSS_RUSH_H
#define BOSS_RUSH_H
#include "game.h"
#define RUSH_X 1664
#define RUSH_Y 192
#define RUSH_FLOOR 384
typedef struct {u8 active,stage,shopping,complete;u16 reward;} BossRush;
extern BossRush boss_rush;
void boss_rush_prepare(void);
void boss_rush_win(void);
void boss_rush_shop_exit(void);
#endif
