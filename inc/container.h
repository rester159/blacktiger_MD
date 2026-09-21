#ifndef CONTAINER_H
#define CONTAINER_H
#include "animation.h"
extern u8 container_traps_occupied;
typedef struct {const AnimClip *clip;u16 next;u8 event;} ContainerSegment;
typedef struct {AnimState animation;u16 segment;s16 x,y;u8 active,left,contact,part;} ContainerTrap;
#define MAX_CONTAINER_TRAPS 24
extern ContainerTrap container_traps[MAX_CONTAINER_TRAPS];
extern u8 container_keys;
void container_actor_reset(void);
void container_actor_restart(void);
void container_spawn(u16 slot);
void container_step(u16 slot,u8 contact);
const AnimFrame *container_frame(u16 slot);
/* Conservative occupancy from the update; retired entries may still count. */
u8 container_traps_tick(void);
u8 container_trap_contact(u16 slot);
const AnimFrame *container_trap_frame(u16 slot);
/* Contact effect only: the animation owner gates contact and fires trap events. */
typedef struct {
 u16 coins,invincible;
 u8 keys,hp,max_hp,opened,collected;
} ContainerContact;
enum { CONTAINER_NO_CONTACT, CONTAINER_OPEN, CONTAINER_TRAP, CONTAINER_COLLECT };
u8 container_contact(u8 content,ContainerContact *state);
u16 container_shuffle(u8 round,u16 seed,u8 *out);
void container_new(void);
void container_round(u8 round);
u8 container_content(u8 persistent);
void container_ground_spawn(s16 x,u8 left);
extern const u16 dragon_wave_roots[2][6];
void dragon_wave_spawn(s16 x,u8 left,u8 profile);
void container_wave_spawn(s16 x,u8 left);
#endif
