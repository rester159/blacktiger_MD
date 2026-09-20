#include "animation.h"
u8 small_actor_axis_active(s16 coordinate,u8 vertical) {
    u16 value=(u16)coordinate;
    return !(value>>8) || (u8)(value-48)>=(vertical?160:161);
}
void animation_reset(AnimState *s) {
    s->frame = s->remaining = 0;
    s->vx = s->vy = 0;
    s->finished = 0;
}
const AnimFrame *animation_current(const AnimState *s, const AnimClip *clip) {
    if (!clip || !clip->count || s->frame >= clip->count)
        return 0;
    return &clip->frames[s->frame];
}
const AnimFrame *animation_tick(AnimState *s, const AnimClip *clip) {
    const AnimFrame *frame;
    if (s->finished || !clip || !clip->count)
        return 0;
    if (s->remaining > 1) {
        --s->remaining;
        return animation_current(s, clip);
    }
    if (s->remaining == 1 && ++s->frame >= clip->count) {
        if (clip->loop == ANIM_NO_LOOP) {
            s->finished = 1;
            s->remaining = 0;
            s->frame = clip->count - 1;
            return 0;
        }
        s->frame = clip->loop;
    }
    frame = animation_current(s, clip);
    if (!frame || !frame->duration) {
        s->finished = 1;
        return 0;
    }
    s->remaining = frame->duration;
    if (!(frame->hold & ANIM_HOLD_X))
        s->vx = frame->vx;
    if (!(frame->hold & ANIM_HOLD_Y))
        s->vy = frame->vy;
    return frame;
}
