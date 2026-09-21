#ifndef DAMAGE_H
#define DAMAGE_H
#include "game.h"
extern volatile u8 combat_difficulty;
u8 player_attack_damage(u8 tier);
void player_hurt(u8 damage);
void player_hurt_from(u8 damage,s16 source_x);
#endif
