#ifndef PAIR_H
#define PAIR_H
#include "animation.h"
typedef struct {const AnimClip *clip;u16 next;u8 event;} PairSegment;
u8 pair_ready(s16 x,s16 y);
void pair_spawn(u16 slot);
void pair_step(u16 slot);
u8 pair_hit(u16 slot,u8 damage);
u8 pair_vulnerable(u16 slot);
const AnimFrame *pair_frame(u16 slot);
#endif
