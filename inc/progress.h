#ifndef PROGRESS_H
#define PROGRESS_H
#include "game.h"
extern volatile u8 progress_max_hp;
void progress_new(void);
void progress_score(u16 points);
#endif
