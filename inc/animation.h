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
typedef struct {const AnimClip *clip;u16 next;u8 event;} AnimSegment;
typedef struct {
    u16 frame, remaining;
    s8 vx, vy;
    u8 finished;
} AnimState;
u8 small_actor_axis_active(s16 coordinate,u8 vertical);
/* Common small/medium source integration: X retirement precedes Y movement.
 * Mode bit 4 suppresses edge retirement. Preserve consumed-row state. */
static inline void actor_motion(Actor *a,s16 dx,s16 dy,u8 mode) {
    a->x+=dx;
    if(!(mode&16) && !small_actor_axis_active(PX(a->x)-game.cam_x,0))goto retire;
    a->y+=dy;
    if((mode&16) || small_actor_axis_active(PX(a->y)-game.cam_y,1))return;
retire:
    a->active=0;game.spawned[a->source]&=254;
}
void animation_reset(AnimState *state);
const AnimFrame *animation_tick(AnimState *state, const AnimClip *clip);
const AnimFrame *animation_current(const AnimState *state, const AnimClip *clip);
#endif
