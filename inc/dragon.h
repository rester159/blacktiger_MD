#ifndef DRAGON_H
#define DRAGON_H
#include "animation.h"
typedef struct {const AnimClip *clip;u16 next[2];u8 event;} DragonSegment;
typedef struct {AnimState animation;u16 segment;u8 mode,pending,left,profile,engaged,alternate,direction,recovery;s8 weak_x;} DragonState;
/* The projectile owner handles allocation; the body never waits for a free slot. */
typedef void (*DragonLaunch)(u8 kind,u8 direction,s16 x,s16 y,u8 profile,u8 left);
extern const DragonSegment dragon_segments[];
extern const u16 dragon_roots[],dragon_choices[3][4][16],dragon_aims[16],dragon_distances[6],dragon_score;
extern const u8 dragon_health[3],dragon_layers[3];
void dragon_spawn(u16 slot,u8 profile);
void dragon_step(u16 slot,DragonLaunch launch);
u8 dragon_hit(u16 slot,u8 damage);
const AnimFrame *dragon_frame(u16 slot);
#endif
