#ifndef LARGE_CONTACT_H
#define LARGE_CONTACT_H
#include "game.h"
typedef struct {s8 weak_x,weak_y;u8 weak_width,weak_height,body_width,body_height;} LargeContactShape;
u8 large_weapon_contact(const LargeContactShape *shape,s16 ax,s16 ay,s16 x,s16 y,u8 width,u8 height,u8 dagger);
u8 large_player_contact(const LargeContactShape *shape,s16 ax,s16 ay,s16 x,s16 y,u8 width,u8 height,u8 alternate);
u8 wide_weapon_contact(const LargeContactShape *shape,s16 ax,s16 ay,s16 x,s16 y,u8 width,u8 height,u8 dagger);
u8 wide_player_contact(const LargeContactShape *shape,s16 ax,s16 ay,s16 x,s16 y,u8 width,u8 height,u8 alternate);
#endif
