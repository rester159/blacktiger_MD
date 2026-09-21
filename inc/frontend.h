#ifndef FRONTEND_H
#define FRONTEND_H
#include "game.h"
typedef struct {u8 lives,difficulty,coinage,continues,music,sfx,credits;} GameSettings;
typedef struct {u8 mode,page,selected,option,credits,coin_meter,message,revision,arcade_credits;} Frontend;
extern Frontend frontend;
extern GameSettings settings[2];
void frontend_init(void);
void frontend_coin(u16 pressed);
u8 frontend_step(u16 pressed);
u8 frontend_lives(void);
u8 frontend_continue(void);
void frontend_return(void);
void frontend_spend(void);
void ui_game_init(void);
void ui_hud(void);
void ui_title(void);
#endif
