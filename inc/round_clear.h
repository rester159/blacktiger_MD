#ifndef ROUND_CLEAR_H
#define ROUND_CLEAR_H
#include "game.h"
typedef struct {u16 code;u8 palette,flip,dx,dy;} ClearSprite;
typedef struct {u8 ticks,visible,hold;ClearSprite sprites[6];} ClearFrame;
typedef struct {const ClearFrame *frames;u8 count,ending_count;} ClearClip;
typedef struct {u8 phase,active,profile,index,remaining,x,y,original_armor;} RoundClear;
extern RoundClear round_clear;
void round_clear_reset(void);
void round_clear_start(void);
u8 round_clear_step(void);
u16 round_clear_reward(u8 round);
const ClearFrame *round_clear_frame(void);
#endif
