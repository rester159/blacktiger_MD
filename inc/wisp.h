#ifndef WISP_H
#define WISP_H
#include "animation.h"
typedef struct {const AnimClip *clip;u16 next[2];u8 event;} WispSegment;
void wisp_spawn(u16 slot);
u8 wisp_hit(u16 slot);
void wisp_step(u16 slot);
const AnimFrame *wisp_frame(u16 slot);
#endif
