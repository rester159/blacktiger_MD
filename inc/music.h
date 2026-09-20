#ifndef MUSIC_H
#define MUSIC_H
#include "game.h"
extern u8 music_active,music_round;
extern u16 music_tick;
extern u32 music_writes;
void music_start(u8 round);
void music_stop(void);
void music_advance(u16 video_frames,u8 pal);
void music_write(u8 part,u8 reg,u8 value);
#endif
