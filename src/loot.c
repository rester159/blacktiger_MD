#include "loot.h"
#include "assets.h"
Loot loot[MAX_LOOT];
u8 loot_active_end;
volatile u16 loot_random;
void loot_reset(void) {
    loot_active_end=0;
    u16 i;
    for (i = 0; i < MAX_LOOT; i++)
        loot[i].active = 0;
}
void loot_new(void) {
    loot_random = 451;
    loot_reset();
}
void loot_random_tick(void) {
    /* Original recurrence: triple the word, then add its old low byte to the high byte. */
    u16 old = loot_random;
    loot_random = (old << 1) + old + (old << 8);
}
u8 loot_spawn(u8 category, u8 sample, s16 x, s16 y) {
    u8 kind;
    u16 i;
    if (category >= 28)
        return 0;
    kind = drop_table[category][sample & 31];
    if (!kind)
        return 0;
    for (i = 0; i < MAX_LOOT; i++)
        if (!loot[i].active) {
            Loot *p = &loot[i];
            p->x = x + 8;
            p->y = y;
            p->kind = kind - 1;
            p->active = 1;
            if(loot_active_end<=i)loot_active_end=i+1;
            animation_reset(&p->animation);
            return 1;
        }
    return 0;
}
void loot_tick(void) {
    u16 i,end=loot_active_end;
    loot_active_end=0;
    for (i = 0; i < end; i++) {
        Loot *p = &loot[i];
        s16 dx, dy;
        if (!p->active)
            continue;
        if (p->active == 2 || !animation_step(&p->animation, loot_clips[p->kind])) {
            p->active = 0;
            continue;
        }
        loot_active_end=i+1;
        p->x += p->animation.vx;
        p->y += p->animation.vy;
        dx = p->x - PX(game.p.x) - 8;
        dy = p->y - PX(game.p.y) - 8;
        /* Uses the current native player bounds; exact player geometry is still being ported. */
        if (dx >= -18 && dx <= 18 && dy >= -20 && dy <= 20) {
            game.coins += loot_values[p->kind];
            p->active = 2;
            game_sound(6);
        }
    }
}
const AnimFrame *loot_frame(u16 slot) {
    Loot *p = &loot[slot];
    if (!p->active || !p->animation.remaining)
        return 0;
    return animation_current(&p->animation, loot_clips[p->kind]);
}
