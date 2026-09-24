#include "progress.h"
u8 skeleton_weapons_occupied;
#include "skeleton.h"
#include "assets.h"
#include "loot.h"
enum {
    INITIAL,
    WALK_R,
    WALK_L,
    APPROACH_R,
    APPROACH_L,
    SWING_R,
    SWING_L,
    WEAPON_R,
    WEAPON_L,
    JUMP_R,
    JUMP_L,
    RETREAT_R,
    RETREAT_L,
    FALL_R,
    FALL_L,
    DEATH_R,
    DEATH_L,
    DAMAGE
};
typedef struct {
    AnimState body, weapon;
    u16 segment, weapon_segment;
    s16 wx, wy;
    u8 left, fraction, attacking, pending, dying, weapon_active;
} SkeletonState;
static SkeletonState skeletons[MAX_ACTORS];
static void select_segment(AnimState *a, u16 *segment, u16 target) {
    s8 vx = a->vx, vy = a->vy;
    animation_reset(a);
    a->vx = vx;
    a->vy = vy;
    *segment = target;
}
static const SkeletonProfile *profile(u16 slot) {
    return &skeleton_profiles[skeleton_kinds[game.actors[slot].def]];
}
static u8 ground(Actor *a, s16 dx, s16 dy) {
    return terrain(PX(a->x) + dx, PX(a->y) + dy) >= 2;
}
static u16 face_attack(u16 slot) {
    SkeletonState *s = &skeletons[slot];
    s->left = game.actors[slot].x >= game.p.x;
    return profile(slot)->roots[s->left ? APPROACH_L : APPROACH_R];
}
static u16 fall(u16 slot) {
    SkeletonState *s = &skeletons[slot];
    Actor *a = &game.actors[slot];
    if (ground(a, 16, 32))
        return face_attack(slot);
    s16 v = (s16)s->body.vy * 256 + s->fraction + 64;
    if (v >= 1280)
        v = 1280;
    s->body.vy = v >> 8;
    s->fraction = v & 255;
    return profile(slot)->roots[s->left ? FALL_L : FALL_R];
}
static u16 start_fall(u16 slot) {
    SkeletonState *s = &skeletons[slot];
    s->body.vx = s->body.vy = s->fraction = 0;
    return fall(slot);
}
static u16 swing(u16 slot) {
    SkeletonState *s = &skeletons[slot];
    Actor *a = &game.actors[slot];
    const SkeletonProfile *p = profile(slot);
    if (!ground(a, 16, 32))
        return start_fall(slot);
    s->wx = PX(a->x) + (s->left ? 32 : -16);
    s->wy = PX(a->y) + 8;
    animation_reset(&s->weapon);
    s->weapon_segment = p->roots[s->left ? WEAPON_L : WEAPON_R];
    s->weapon_active = s->attacking = 1;skeleton_weapons_occupied=1;
    return p->roots[s->left ? SWING_L : SWING_R];
}
static u16 event(u16 slot, u8 action, u16 next) {
    SkeletonState *s = &skeletons[slot];
    Actor *a = &game.actors[slot];
    const SkeletonProfile *p = profile(slot);
    s16 x = PX(a->x), y = PX(a->y), px = PX(game.p.x), py = PX(game.p.y);
    switch (action) {
    case 1:
        return p->roots[x < px ? WALK_R : WALK_L];
    case 2:
        if ((u16)(y + 8 - py) < 16 && (u16)(x + 48 + (s->body.vx < 0 ? -16 : 16) - px) < 96)
            return face_attack(slot);
        return next;
    case 3:
        return face_attack(slot);
    case 4:
        return swing(slot);
    case 5:
        s->attacking = 0;
        if ((u16)(x + 48 - px) < 96)
            return swing(slot);
        if (!ground(a, 16, 32))
            return start_fall(slot);
        if (!ground(a, s->left ? 0 : 32, 16))
            return next;
        if (!ground(a, s->left ? 0 : 32, -16)) {
            s->body.vy = -4;
            s->fraction = 0;
            return p->roots[s->left ? JUMP_L : JUMP_R];
        }
        return p->roots[s->left ? RETREAT_L : RETREAT_R];
    case 6:
        if (s->body.vy >= 0 && ground(a, 16, 32))
            return face_attack(slot);
        {
            s16 v = (s16)s->body.vy * 256 + s->fraction + 64;
            if (v >= 1280)
                v = 1280;
            s->body.vy = v >> 8;
            s->fraction = v & 255;
        }
        return p->roots[s->left ? JUMP_L : JUMP_R];
    case 7:
        return fall(slot);
    case 8: {
        u8 damage = s->pending, blocked = p->guard && !s->attacking && (game.p.face != s->left);
        s->pending = 0;
        s->weapon_active = 0;
        a->hit = 0;
        if (p->variant == 2)
            game.spawned[a->source] = 2;
        if (blocked) {
            if (damage < p->guard)
                return face_attack(slot);
            damage -= p->guard;
            if (a->hp >= damage) {
                a->hp -= damage;
                game.sound = SND_HIT;
                return face_attack(slot);
            }
        } else if (a->hp > damage) {
            a->hp -= damage;
            game.sound = SND_HIT;
            return face_attack(slot);
        }
        s->dying = 1;
        a->state = 1;
        game.spawned[a->source] = 2;
        game.kills++;
        loot_spawn(drop_categories[a->def], loot_random >> 8, x, y);
        progress_score(p->score);
        game.sound = SND_KILL;
        return p->roots[px >= x ? DEATH_R : DEATH_L];
    }
    case 9:
        game.sound = SND_ATTACK;
        return next;
    default:
        a->active = 0;
        return 65535;
    }
}
void skeleton_reset(void) {
    skeleton_weapons_occupied=0;
    u16 i;
    for (i = 0; i < MAX_ACTORS; i++)
        skeletons[i].weapon_active = 0;
}
void skeleton_spawn(u16 slot) {
    SkeletonState *s = &skeletons[slot];
    const SkeletonProfile *p = profile(slot);
    animation_reset(&s->body);
    animation_reset(&s->weapon);
    s->segment = p->roots[INITIAL];
    s->left = s->fraction = s->attacking = s->pending = s->dying = s->weapon_active = 0;
    game.actors[slot].hp = p->durability;
    game.actors[slot].state = 0;
}
u8 skeleton_hit(u16 slot, u8 damage) {
    Actor *a = &game.actors[slot];
    SkeletonState *s = &skeletons[slot];
    if (skeleton_kinds[a->def] == 255)
        return 0;
    if (a->active && !s->pending && !s->dying) {
        s->pending = damage;
        a->hit = 1;
        select_segment(&s->body, &s->segment, profile(slot)->roots[DAMAGE]);
    }
    return 1;
}
__attribute__((noinline)) static void skeleton_transition(u16 slot) {
    SkeletonState *s = &skeletons[slot];
    Actor *a = &game.actors[slot];
    u16 i;
    for (i = 0; i < 8; i++) {
        const SkeletonSegment *seg = &skeleton_segments[s->segment];
        if (animation_step(&s->body, seg->clip)) {
            a->vx = (s16)s->body.vx * FX;
            a->vy = (s16)s->body.vy * FX + s->fraction;
            actor_motion(a,a->vx,(s16)s->body.vy*FX,8);
            return;
        }
        u16 target = event(slot, seg->event, seg->next);
        if (target == 65535)
            return;
        select_segment(&s->body, &s->segment, target);
    }
}
u32 skeleton_weapons_tick(void) {
    u16 i;u32 active=0;
    for (i = 0; i < MAX_ACTORS; i++) {
        SkeletonState *s = &skeletons[i];
        u16 tries;
        if (!s->weapon_active)
            continue;
        for (tries = 0; tries < 4; tries++) {
            const SkeletonSegment *seg = &skeleton_segments[s->weapon_segment];
            if (animation_step(&s->weapon, seg->clip)) {
                s->wx += s->weapon.vx;
                s->wy += s->weapon.vy;
                break;
            }
            if (seg->event != 9) {
                s->weapon_active = 0;
                break;
            }
            game.sound = SND_ATTACK;
            select_segment(&s->weapon, &s->weapon_segment, seg->next);
        }
        if(s->weapon_active && s->weapon.remaining)active|=(u32)1<<i;
    }
    skeleton_weapons_occupied=active!=0;return active;
}
const AnimFrame *skeleton_frame(u16 slot) {
    SkeletonState *s = &skeletons[slot];
    return animation_current(&s->body, skeleton_segments[s->segment].clip);
}
const AnimFrame *skeleton_weapon_frame(u16 slot, s16 *x, s16 *y) {
    SkeletonState *s = &skeletons[slot];
    if (!s->weapon_active || !s->weapon.remaining)
        return 0;
    *x = s->wx;
    *y = s->wy;
    return animation_current(&s->weapon, skeleton_segments[s->weapon_segment].clip);
}

u8 skeleton_weapon_contact(u16 slot) {
    const SkeletonState *s = &skeletons[slot];
    const SkeletonProfile *p;
    s16 dx, dy, width, height;
    if (!s->weapon_active || !s->weapon.remaining) return 0;
    p = profile(slot);
    dx = PX(game.p.x) + 8 - s->wx;
    dy = PX(game.p.y) + (game.player_low?18:8) - s->wy;
    width = (game.player_low?3:p->weapon_width) + contact_player_width;
    height = (game.player_low?3:p->weapon_height) + contact_player_height;
    return dx >= -width && dx <= width && dy >= -height && dy <= height ? p->weapon_damage : 0;
}

/* Held frames avoid the transition interpreter's large register frame. */
void skeleton_step(u16 slot) {
 SkeletonState *s=&skeletons[slot];
 if(animation_hold_step(&s->body,skeleton_segments[s->segment].clip)) {
  Actor *a=&game.actors[slot];a->vx=(s16)s->body.vx*FX;a->vy=(s16)s->body.vy*FX + s->fraction;
  actor_motion(a,a->vx,(s16)s->body.vy*FX,8);return;
 }
 skeleton_transition(slot);
}
