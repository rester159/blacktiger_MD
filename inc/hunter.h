#ifndef HUNTER_H
#define HUNTER_H
#include "animation.h"
typedef struct {const AnimClip *clip;u16 next;u8 event;} HunterSegment;
void hunter_spawn(u16 slot,u8 boss);
u8 hunter_hit(u16 slot,u8 damage);
u8 hunter_vulnerable(u16 slot);
void hunter_step(u16 slot);
const AnimFrame *hunter_frame(u16 slot);
#endif
