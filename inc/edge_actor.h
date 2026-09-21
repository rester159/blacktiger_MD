#ifndef EDGE_ACTOR_H
#define EDGE_ACTOR_H
#include "animation.h"
extern u8 edge_shots_occupied;
extern const AnimSegment edge_segments[],edge_shot_segments[];
extern const u16 edge_roots[41],edge_shot_roots[38],edge_score;
extern const u8 edge_choices[8][16],edge_attacks[16],edge_health,edge_layers;
typedef struct {AnimState animation;u16 segment;s16 x,y;u8 active,profile,hp,pending,dying;} EdgeShot;
extern EdgeShot edge_shots[24];
void edge_shots_reset(void);
void edge_actor_spawn(u16 slot);
void edge_actor_step(u16 slot);
u8 edge_actor_hit(u16 slot,u8 damage);
u8 edge_actor_vulnerable(u16 slot);
u8 edge_actor_contact(u16 slot);
void edge_screen_attack(u16 slot);
const AnimFrame *edge_actor_frame(u16 slot);
/* Conservative occupancy from the update; retired entries may still count. */
u8 edge_shots_step(void);
u8 edge_shot_contact(u16 slot);
u8 edge_shot_hit(s16 x,s16 y,u8 damage,u8 dagger);
const AnimFrame *edge_shot_frame(u16 slot);
#endif
