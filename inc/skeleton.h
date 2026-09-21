#ifndef SKELETON_H
#define SKELETON_H
#include "animation.h"
extern u8 skeleton_weapons_occupied;
typedef struct {
    const AnimClip *clip;
    u16 next;
    u8 event;
} SkeletonSegment;
typedef struct {
    u16 roots[18];
    u8 durability, guard, variant;
    u16 score;
    u8 weapon_damage, weapon_width, weapon_height, weapon_contact;
} SkeletonProfile;
void skeleton_reset(void);
void skeleton_spawn(u16 slot);
u8 skeleton_hit(u16 slot, u8 damage);
void skeleton_step(u16 slot);
u32 skeleton_weapons_tick(void);
u8 skeleton_weapon_contact(u16 slot);
const AnimFrame *skeleton_frame(u16 slot);
const AnimFrame *skeleton_weapon_frame(u16 slot, s16 *x, s16 *y);
#endif
