#ifndef SFX_H
#define SFX_H
#include "game.h"
typedef struct {u16 value;u8 kind,delta;} SfxOp;
typedef struct {const SfxOp *data;u16 length;u8 flags;} SfxTrack;
typedef struct {const SfxTrack *track;u16 position,tick;u8 command,active,regs[11];u16 pitch[3],remaining;u8 volume[3],noise,mixer,pitch_delta[3],volume_delta[3],noise_delta,repeat;} SfxSlot;
extern SfxSlot sfx_slots[2];
extern u8 sfx_active,sfx_phase,sfx_request;
extern u32 sfx_ticks;
void sfx_reset(void);
u8 sfx_start(u8 command);
void sfx_timer_step(void);
void sfx_advance(u16 video_frames,u8 pal);
void sfx_render(u8 pal);
void sfx_invalidate(void);
void sfx_tone(u8 channel,u16 period);
void sfx_volume(u8 channel,u8 attenuation);
void sfx_noise(u8 control);
#endif
