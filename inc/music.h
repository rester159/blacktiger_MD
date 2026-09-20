#ifndef MUSIC_H
#define MUSIC_H
#include "game.h"
extern u8 music_active,music_round,music_command,music_request;
extern const u8 music_boss_commands[8];
extern u16 music_tick;
extern u32 music_writes;
void music_start(u8 round);
void music_start_command(u8 command);
void music_stop(void);
void music_advance(u16 video_frames,u8 pal);
void music_write(u8 part,u8 reg,u8 value);
#endif
