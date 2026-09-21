#ifndef WAVEBOSS_H
#define WAVEBOSS_H
#include "animation.h"
typedef struct {const AnimClip *clip;u16 next[2];u8 event;} WaveBossSegment;
typedef struct {AnimState animation;u16 segment;s16 x,y;u8 active,left,profile;} WaveBossSeed;
#define MAX_WAVEBOSS_SEEDS 8
extern WaveBossSeed waveboss_seeds[MAX_WAVEBOSS_SEEDS];
u8 waveboss_player_contact(u16 slot);
u8 waveboss_weapon_contact(u16 slot,s16 x,s16 y,u8 dagger);
void waveboss_reset(void);
void waveboss_spawn(u16 slot);
void waveboss_step(u16 slot);
u8 waveboss_hit(u16 slot,u8 damage);
u8 waveboss_vulnerable(u16 slot);
u8 waveboss_contact(u16 slot);
u8 waveboss_present(void);
u8 waveboss_locked(void);
void waveboss_screen_attack(u16 slot);
const AnimFrame *waveboss_frame(u16 slot);
/* Conservative occupancy from the update; retired entries may still count. */
u8 waveboss_seeds_tick(void);
const AnimFrame *waveboss_seed_frame(u16 slot);
#endif
