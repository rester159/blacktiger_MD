#ifndef ARMOR_BREAK_H
#define ARMOR_BREAK_H
#include "animation.h"
typedef struct {AnimState anim;s16 x,y;u8 active;} ArmorFragment;
extern ArmorFragment armor_fragments[4];
void armor_break_reset(void);
void armor_break_start(void);
void armor_break_step(void);
const AnimFrame *armor_break_frame(u16 index);
#endif
