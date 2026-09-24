#include "wisp.h"
#include "assets.h"
#include "loot.h"
typedef struct {AnimState animation;u16 segment;u8 pending;} WispState;
static WispState wisps[MAX_ACTORS];
void wisp_spawn(u16 slot) {
    WispState *s=&wisps[slot];animation_reset(&s->animation);s->segment=wisp_roots[0];s->pending=0;
    game.actors[slot].hp=1;game.actors[slot].state=0;
}
u8 wisp_hit(u16 slot) {
    Actor *a=&game.actors[slot];
    if (!wisp_kinds[a->def]) return 0;
    wisps[slot].pending=1;a->state=1;
    return 1;
}
__attribute__((noinline)) static void wisp_transition(u16 slot) {
    Actor *a=&game.actors[slot];WispState *s=&wisps[slot];u16 tries;
    if (s->pending) {
        s->pending=0;s->segment=wisp_roots[0];animation_reset(&s->animation);
        a->hp=1;game.sound=SND_HIT;
    }
    for (tries=0;tries<8;tries++) {
        const WispSegment *seg=&wisp_segments[s->segment];u16 target;
        if (animation_step(&s->animation,seg->clip)) {
            a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;
            actor_motion(a,a->vx,a->vy,8);return;
        }
        u8 near=(u8)(PX(game.p.y)+70-PX(a->y))<140;
        switch(seg->event) {
        case 0:target=near?wisp_roots[1+((loot_random>>8)&1)]:seg->next[0];break;
        case 1:target=seg->next[near];break;
        case 2:target=wisp_roots[1+((loot_random>>8)&1)];break;
        case 3:target=wisp_roots[((loot_random>>8)&1)?4:3];break;
        default:target=wisp_roots[((loot_random>>8)&1)?6:5];break;
        }
        s->segment=target;animation_reset(&s->animation);
    }
}
const AnimFrame *wisp_frame(u16 slot) {
    WispState *s=&wisps[slot];
    return s->animation.remaining?animation_current(&s->animation,wisp_segments[s->segment].clip):0;
}

/* Held frames avoid the transition interpreter's large register frame. */
void wisp_step(u16 slot) {
 WispState *s=&wisps[slot];
 if(!s->pending && animation_hold_step(&s->animation,wisp_segments[s->segment].clip)) {
  Actor *a=&game.actors[slot];a->vx=(s16)s->animation.vx*FX;a->vy=(s16)s->animation.vy*FX;
  actor_motion(a,a->vx,(s16)s->animation.vy*FX,8);return;
 }
 wisp_transition(slot);
}
