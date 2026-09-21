#ifndef ARENA_VIDEO_H
#define ARENA_VIDEO_H
#include <genesis.h>
extern u8 arena_video_active;
void arena_video_init(void);
void arena_video_reset(void);
void arena_video_frame(void);
void arena_video_restore(u8 shop);
u16 arena_video_text_x(u16 x,u16 y);
#endif
