#ifndef LOOT_H
#define LOOT_H
#include "animation.h"
#define MAX_LOOT 33
typedef struct {
    s16 x, y;
    AnimState animation;
    u8 active, kind;
} Loot;
extern Loot loot[MAX_LOOT];
/* One past the last occupied slot; allocation expands it, updates shrink it. */
extern u8 loot_active_end;
/* Force a word load: GCC 16/m68k can otherwise widen the high-byte mask to an odd longword access. */
extern volatile u16 loot_random;
void loot_new(void);
void loot_reset(void);
void loot_random_tick(void);
u8 loot_spawn(u8 category, u8 sample, s16 x, s16 y);
void loot_tick(void);
const AnimFrame *loot_frame(u16 slot);
#endif
