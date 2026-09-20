#ifndef STATUE_SHELL_H
#define STATUE_SHELL_H
#include "statue.h"
#define MAX_STATUE_SHELLS 12
typedef struct {
 AnimState animation;
 u16 segment;
 s16 x,y;
 u8 active,cycles,mode,pending;
} StatueShell;
extern StatueShell statue_shells[MAX_STATUE_SHELLS],statue_blasts[MAX_STATUE_SHELLS];
void statue_shell_reset(void);
u8 statue_shell_spawn(s16 x,s16 y,u8 direction);
void statue_shell_tick(void);
u8 statue_shell_hit(u16 slot);
u8 statue_shell_hit_at(s16 x,s16 y,u8 kind);
u8 statue_shell_player_contact(u16 slot,u8 blast);
void statue_shell_contact(u16 slot);
const AnimFrame *statue_shell_frame(const StatueShell *s);
extern StatueShell hunter_shells[MAX_STATUE_SHELLS],hunter_blasts[MAX_STATUE_SHELLS];
u8 hunter_shell_spawn(s16 x,s16 y,u8 direction,u8 boss);
void hunter_shell_tick(void);
u8 hunter_shell_hit(u16 slot);
u8 hunter_shell_hit_at(s16 x,s16 y,u8 kind);
u8 hunter_shell_player_contact(u16 slot,u8 blast);
void hunter_shell_contact(u16 slot);
const AnimFrame *hunter_shell_frame(const StatueShell *s);
#endif
