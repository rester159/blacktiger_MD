#ifndef BOSS_H
#define BOSS_H
#include "animation.h"
typedef struct {const AnimClip *clip;u16 next[2];u8 event;} BossSegment;
u8 boss_hit(u16 slot,u8 damage);
void boss_step(u16 slot);
u8 boss_vulnerable(u16 slot);
u8 boss_locked(void);
const AnimFrame *boss_frame(u16 slot);
void boss_spawn(u16 slot);
u8 boss_break_layer(Actor *actor);
#endif
