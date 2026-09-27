#ifndef ATTRACT_H
#define ATTRACT_H
#include "game.h"
extern u16 attract_frame;
extern u8 attract_running,attract_credit;
u8 attract_active(void);
void attract_step(void);
void attract_reset(void);
u8 *video_attract_workspace(void);
void attract_video(void);
void video_attract_piece(u16 key,u16 slot);
void ui_attract_version(void);
#endif
