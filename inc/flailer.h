#ifndef FLAILER_H
#define FLAILER_H
#include "animation.h"
typedef struct {AnimState animation;u16 segment;s16 x,y;u8 active,profile,pending,dying;} FlailerWeapon;
extern FlailerWeapon flailer_weapons[MAX_ACTORS];
void flailer_reset(void);
void flailer_spawn(u16 slot);
void flailer_step(u16 slot);
u8 flailer_vulnerable(u16 slot);
u8 flailer_hit(u16 slot,u8 damage);
void flailer_screen_attack(u16 slot);
const AnimFrame *flailer_frame(u16 slot);
/* Conservative occupancy from the update; retired entries may still count. */
u8 flailer_weapons_tick(void);
u8 flailer_weapon_hit(s16 x,s16 y,u8 kind);
u8 flailer_weapon_contact(u16 slot);
void flailer_weapons_clear_attack(void);
const AnimFrame *flailer_weapon_frame(u16 slot);
#endif
