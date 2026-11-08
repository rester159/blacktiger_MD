#ifndef PROGRESS_H
#define PROGRESS_H
#include "game.h"
extern volatile u8 progress_max_hp;
/* Arcade score storage uses tens; fixed 0568 appends the displayed zero.
   Keep save records and vitality thresholds in the original internal units. */
static inline u32 progress_display_score(u32 score) {return score * 10UL;}
void progress_new(void);
void progress_score(u16 points);
#endif
