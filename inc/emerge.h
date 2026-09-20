#ifndef EMERGE_H
#define EMERGE_H
#include "animation.h"
typedef struct { const AnimClip *clips[6]; u16 score; u8 health, width, height; } EmergeProfile;
void emerge_reset(void);
u8 emerge_spawn_ready(u16 row);
void emerge_spawn(u16 slot);
u8 emerge_vulnerable(u16 slot);
u8 emerge_hit(u16 slot, u8 damage);
u8 emerge_step(u16 slot);
const AnimFrame *emerge_frame(u16 slot);
#endif
