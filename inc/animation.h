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
/* Native actors only need a live/finished result. A held frame can advance
 * locally without a call and frame-pointer calculation; transitions retain the
 * complete interpreter, including zero-duration and malformed-state handling. */
static inline u8 animation_hold_step(AnimState *s,const AnimClip *clip) {
    if(s->remaining>1 && !s->finished && clip && s->frame<clip->count){
        --s->remaining;return 1;
    }
    return 0;
}
static inline u8 animation_step(AnimState *s,const AnimClip *clip) {
    return animation_hold_step(s,clip) || animation_tick(s,clip)!=0;
}
const AnimFrame *animation_current(const AnimState *state, const AnimClip *clip);
#endif
