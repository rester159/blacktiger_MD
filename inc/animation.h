#ifndef ANIMATION_H
#define ANIMATION_H
#include "game.h"
enum { ANIM_HOLD_X = 1, ANIM_HOLD_Y = 2 };
#define ANIM_NO_LOOP 65535u
/* Native frame data: no source pointers, CPU registers, or bytecode dispatch. */
typedef struct {
    u16 code;
    u8 duration, palette, flip, hold;
    s8 vx, vy;
} AnimFrame;
typedef struct {
    const AnimFrame *frames;
    u16 count, loop;
} AnimClip;
typedef struct {
    u16 frame, remaining;
    s8 vx, vy;
    u8 finished;
} AnimState;
void animation_reset(AnimState *state);
const AnimFrame *animation_tick(AnimState *state, const AnimClip *clip);
const AnimFrame *animation_current(const AnimState *state, const AnimClip *clip);
#endif
