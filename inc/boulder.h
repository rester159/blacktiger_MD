#ifndef BOULDER_H
#define BOULDER_H
#include "animation.h"
typedef struct {const AnimClip *clip;u16 next[2];u8 event;} BoulderSegment;
void boulder_spawn(u16 slot);
void boulder_step(u16 slot);
u8 boulder_hit(u16 slot,u8 damage);
u8 boulder_damage(u16 slot);
const AnimFrame *boulder_frame(u16 slot);
#endif
