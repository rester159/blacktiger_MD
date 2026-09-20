#include "progress.h"
#include "world.h"
#include "assets.h"
u8 world_opened, world_rows[256];
static u8 taken, effect_active[6];
static AnimState animations[MAX_ACTORS], effects[6];
static u8 patch_for(u16 source) {
    const Round *r = &rounds[game.round];
    u8 i;
    for (i = 0; i < r->patch_count; i++)
        if (r->patches[i].source == source)
            return i;
    return 255;
}
void world_reset(void) {
    const Round *r = &rounds[game.round];
    u16 i, j, shift = r->width == 2048 ? 7 : 6;
    world_opened = taken = 0;
    for (i = 0; i < 256; i++)
        world_rows[i] = 0;
    for (i = 0; i < 6; i++)
        effect_active[i] = 0;
    for (i = 0; i < r->patch_count; i++) {
        u16 y = (r->patches[i].cell >> shift) * 2;
        for (j = 0; j < 4; j++)
            world_rows[y + j] |= 1 << i;
    }
}
void world_restart(void) {
    u8 opened=world_opened,collected=taken;
    world_reset();world_opened=opened;taken=collected;
}
u16 world_word(u16 x, u16 y, u16 original) {
    const Round *r = &rounds[game.round];
    u8 mask = world_rows[y] & world_opened, i;
    u16 shift = r->width == 2048 ? 7 : 6;
    for (i = 0; mask; i++, mask >>= 1)
        if (mask & 1) {
            u16 cell = r->patches[i].cell, px = (cell & ((1 << shift) - 1)) * 2;
            if (x >= px && x < px + 2)
                return r->open_tile[((y & 1) << 1) + x - px];
        }
    return original;
}
u8 world_collision(u16 cell, u8 original) {
    const Round *r = &rounds[game.round];
    u8 i, mask = world_opened;
    u16 width = r->width >> 4;
    for (i = 0; mask; i++, mask >>= 1)
        if (mask & 1) {
            u16 p = r->patches[i].cell;
            if (cell == p || cell == p + width)
                return r->open_collision;
        }
    return original;
}
void world_tick(void) {
    u8 i;
    for (i = 0; i < 6; i++)
        if (effect_active[i] && !animation_tick(&effects[i], &hidden_explosion))
            effect_active[i] = 0;
}
const AnimFrame *world_effect(u16 patch) {
    return effect_active[patch] ? animation_current(&effects[patch], &hidden_explosion) : 0;
}
void hidden_spawn(u16 slot) {
    Actor *a = &game.actors[slot];
    u8 p = patch_for(a->source);
    animation_reset(&animations[slot]);
    if (p != 255 && (world_opened & (1 << p))) {
        a->state = 1;
        if (taken & (1 << p))
            a->active = 0;
    }
}
void hidden_break(u16 slot) {
    Actor *a = &game.actors[slot];
    u8 p = patch_for(a->source);
    if (p == 255)
        return;
    world_opened |= 1 << p;
    a->state = 1;
    a->hit = 0;
    animation_reset(&animations[slot]);
    animation_reset(&effects[p]);
    effect_active[p] = 1;
    game.sound = SND_KILL;
}
const AnimFrame *hidden_frame(u16 slot) {
    Actor *a = &game.actors[slot];
    if (!a->state)
        return 0;
    return animation_current(&animations[slot], a->state == 2 ? &hidden_life_collected
                                                              : hidden_clips[hidden_kinds[a->def]]);
}
u8 hidden_step(u16 slot, u8 contact) {
    Actor *a = &game.actors[slot];
    AnimState *anim = &animations[slot];
    u8 kind = hidden_kinds[a->def], p = patch_for(a->source);
    if (!a->state)
        return 0;
    if (!animation_tick(anim, a->state == 2 ? &hidden_life_collected : hidden_clips[kind])) {
        a->active = 0;
        return 0;
    }
    a->x += (s16)anim->vx * FX;
    a->y += (s16)anim->vy * FX;
    if (a->state != 1 || !contact)
        return 0;
    if (p != 255)
        taken |= 1 << p;
    game.spawned[a->source] = 2;
    a->active = 0;
    game.sound = SND_COIN;
    switch (kind) {
    case 1:
        game.p.lives++;
        a->active = 1;
        a->state = 2;
        animation_reset(anim);
        break;
    case 2:
        game.p.hp = progress_max_hp;
    case 6:
        game.p.armor = game.p.armor > 6 ? 8 : game.p.armor + 2;
        break;
    case 7:
        game.p.armor = game.p.armor > 5 ? 8 : game.p.armor + 3;
        break;
    case 3:
        return 1;
    case 4:
        game.time += 30;
        break;
    case 5:
        game.coins += 1000;
        break;
    case 10:
        game.coins += 500;
        break;
    case 8:
        progress_score(1000);
        break;
    case 9:
        progress_score(5000);
        break;
    case 11:
        progress_score(7000);
        break;
    default:
        break;
    }
    return 0;
}
