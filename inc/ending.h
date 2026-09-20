#ifndef ENDING_H
#define ENDING_H
#include "game.h"
typedef struct {u16 tick,cell;u8 value,type;} EndingEvent;
typedef struct {u16 tick,index;u8 active,palette,scene,complete;} Ending;
extern Ending ending;
extern u8 ending_text[896];
extern u32 ending_dirty_rows;
void ending_reset(void);
void ending_start(void);
u8 ending_step(void);
#endif
