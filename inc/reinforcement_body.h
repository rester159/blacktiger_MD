#ifndef REINFORCEMENT_BODY_H
#define REINFORCEMENT_BODY_H
#include "animation.h"
extern const AnimSegment reinforcement_segments[];
extern const u16 reinforcement_roots[2][25],reinforcement_scores[2];
extern const u8 reinforcement_choices[2][8][16],reinforcement_health[2],reinforcement_layers[2];
extern const AnimClip *const reinforcement_clips[12];
typedef struct {AnimState animation;s16 x,y;u8 active,part;} ReinforcementShot;
extern ReinforcementShot reinforcement_shots[24];
/* Source player posture byte; normal posture until the player controller is ported. */
extern u8 reinforcement_player_low;
void reinforcement_body_spawn(u16 slot);
void reinforcement_body_step(u16 slot);
u8 reinforcement_body_hit(u16 slot,u8 damage);
u8 reinforcement_body_vulnerable(u16 slot);
u8 reinforcement_body_contact(u16 slot);
void reinforcement_screen_attack(u16 slot);
const AnimFrame *reinforcement_body_frame(u16 slot);
void reinforcement_shots_reset(void);
void reinforcement_shots_step(void);
u8 reinforcement_shot_contact(u16 slot);
const AnimFrame *reinforcement_shot_frame(u16 slot);
#endif
