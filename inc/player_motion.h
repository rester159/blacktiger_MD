#ifndef PLAYER_MOTION_H
#define PLAYER_MOTION_H
#include "game.h"
/* Native movement state. Scroll coordinates are logical arcade coordinates;
 * the Genesis viewport may display the resulting world position independently. */
typedef struct {
    u16 scroll_x, scroll_y, screen_x, screen_y, jump_origin;
    s8 vx, vy;
    u8 fraction, subtick, pose, jumping, jump_request, direction, redirected;
    u8 camera_return, below_origin, falling, ladder, low, frame;
    u8 selector, previous, idle, jump_history, screen_motion;
} PlayerMotion;
typedef struct {
    u8 active, request, history, launch, selector, reach, damage;
    u8 counter, holding, hit, links, count;
} PlayerAttack;
/* Ordered output from one controller update, drained by audio_tick. */
extern u8 player_motion_sounds[4],player_motion_sound_count,player_motion_frame;
extern PlayerMotion player_motion;
extern PlayerAttack player_attack;
void player_control_step(PlayerMotion *p, PlayerAttack *attack, u8 input, u8 reversed, u8 tier);
void player_attack_hit(PlayerAttack *attack);
void player_motion_step(PlayerMotion *p, u8 input, u8 reversed);
#endif
