#ifndef STATUS_H
#define STATUS_H
#include "game.h"
extern u8 status_reverse,status_gate;
void status_new(void);
void status_tick(void);
void status_poison_contact(void);
void status_reverse_contact(void);
u16 status_controls(u16 input);
#endif
