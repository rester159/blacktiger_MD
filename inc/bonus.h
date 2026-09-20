#ifndef BONUS_H
#define BONUS_H
#include "game.h"
typedef struct {u16 cell,words[2][4];u8 collision[2];} BonusPatch;
typedef struct {u16 x,y;} BonusTrigger;
typedef struct {const BonusPatch *patches;u16 count,camera_x,camera_y;u8 return_add,trigger_count;BonusTrigger triggers[2];} BonusRound;
extern const BonusRound bonus_rounds[8];
extern u8 bonus_entered,bonus_consumed,bonus_rows[128];
extern u16 bonus_saved_x,bonus_saved_y;
void bonus_reset(u8 preserve);
u8 bonus_gate(u8 jumping,u8 falling,u8 returning);
void bonus_destination(u8 round,u8 entered,u16 *x,u16 *y,u16 *saved_x,u16 *saved_y);
u8 bonus_contact(void);
u16 bonus_word(u16 x,u16 y,u16 original);
u8 bonus_collision(u16 cell,u8 original);
void game_bonus_transition(void);
#endif
