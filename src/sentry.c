#include "progress.h"
#include "sentry.h"
#include "assets.h"
#include "loot.h"
typedef struct { AnimState animation; u8 direction, clip, pending; } SentryState;
static SentryState sentries[MAX_ACTORS];
u8 aim_direction(u8 x, u8 y, u8 tx, u8 ty) {
    u8 quadrant = 0, minor, major, step, threshold, band = 0;
    if (tx < x) { minor = x - tx; quadrant = 4; } else minor = tx - x;
    if (ty < y) { major = y - ty; quadrant += 2; } else major = ty - y;
    if (major < minor) {
        u8 temp = major; major = minor; minor = temp;
        if (quadrant == 0 || quadrant == 4) quadrant++;
    } else if (quadrant == 2 || quadrant == 6) quadrant++;
    step = major >> 3;
    threshold = step;
    while (band < 4 && threshold < minor) { band++; threshold += 2 * step; }
    return aim_table[quadrant * 8 + band];
}
void sentry_spawn(u16 slot) {
    SentryState *s = &sentries[slot];
    animation_reset(&s->animation);
    s->direction = s->pending = 0;
    s->clip = 255;
    game.actors[slot].hp = sentry_health;
    game.actors[slot].state = 0;
    game.actors[slot].vx = game.actors[slot].vy = 0;
}
u8 sentry_hit(u16 slot, u8 damage) {
    Actor *a = &game.actors[slot];
    SentryState *s = &sentries[slot];
    if (!sentry_kinds[a->def]) return 0;
    if (!a->state && a->active) {
        if (a->hp > damage) a->hp -= damage;
        else { a->state = 1; s->pending = 1; progress_score(sentry_score); }
    }
    return 1;
}
void sentry_step(u16 slot) {
    Actor *a = &game.actors[slot];
    SentryState *s = &sentries[slot];
    if (s->pending) {
        s->pending = 0; s->clip = 6;
        animation_reset(&s->animation);
        game.spawned[a->source] = 2;
        game.kills++;
        loot_spawn(drop_categories[a->def], loot_random >> 8, PX(a->x), PX(a->y));
        game.sound = SND_KILL;
    } else if (s->clip == 255 || (!a->state && s->animation.remaining == 1)) {
        u8 bright = (loot_random >> 8) < 63, facing;
        if (!bright)
            s->direction = aim_direction(PX(a->x)-game.cam_x, PX(a->y)-game.cam_y,
                                        PX(game.p.x)-game.cam_x, PX(game.p.y)-game.cam_y);
        facing = s->direction + 4;
        s->clip = ((facing & 15) >= 8 ? 1 : (facing & 31) >= 16 ? 2 : 0) + (bright ? 3 : 0);
        animation_reset(&s->animation);
    }
    if (!animation_tick(&s->animation, sentry_clips[s->clip])) a->active = 0;
}
const AnimFrame *sentry_frame(u16 slot) {
    SentryState *s = &sentries[slot];
    return s->clip < 7 && s->animation.remaining ? animation_current(&s->animation, sentry_clips[s->clip]) : 0;
}
