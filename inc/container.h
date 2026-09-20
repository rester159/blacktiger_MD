#ifndef CONTAINER_H
#define CONTAINER_H
#include "game.h"
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
#endif
