#ifndef NPC_H
#define NPC_H
#include "animation.h"
typedef struct {u16 tick,value;u8 type;} NpcEvent;
typedef struct {u16 tick,index,code;u8 page,complete;} NpcSequence;
extern NpcSequence npc_sequence;
const u16 *npc_dialogue(void);
void npc_reset(void);
void npc_spawn(u16 slot);
u8 npc_spawn_ready(u16 source);
void npc_step(u16 slot, u8 contact);
void npc_rescue_tick(void);
const AnimFrame *npc_frame(u16 slot);
#endif
