#include "progress.h"
#include "npc.h"
#include "assets.h"
#include "npc_sequence_data.inc"
NpcSequence npc_sequence;
static AnimFrame rescue_frame;
const u16 *npc_dialogue(void){return npc_pages[npc_sequence.page];}
static void sequence_step(void);
/* Native state is separate from the old machine's actor records. */
static AnimState npc_animation[MAX_ACTORS];
static u8 respawn_delay[160];
void npc_reset(void) {
    u16 i;npc_sequence=(NpcSequence){0};
    for (i = 0; i < MAX_ACTORS; i++)
        animation_reset(&npc_animation[i]);
    for (i = 0; i < 160; i++)
        respawn_delay[i] = 0;
}
void npc_spawn(u16 slot) {
    animation_reset(&npc_animation[slot]);
}
u8 npc_spawn_ready(u16 source) {
    if (respawn_delay[source]) {
        --respawn_delay[source];
        return 0;
    }
    return 1;
}
static const AnimClip *clip_for(u16 slot) {
    u8 state = game.actors[slot].state;
    return state == 1 ? &npc_rescue : state == 2 ? &npc_released : &npc_idle;
}
const AnimFrame *npc_frame(u16 slot) {
    if(game.actors[slot].state==1){rescue_frame=(AnimFrame){.code=npc_sequence.code,.palette=4};return &rescue_frame;}
    return animation_current(&npc_animation[slot], clip_for(slot));
}
void npc_step(u16 slot, u8 contact) {
    Actor *a = &game.actors[slot];
    const ActorDef *d = &actor_defs[a->def];
    AnimState *anim = &npc_animation[slot];
    if (a->state == 0 && contact && game.mode == PLAY) {
        a->state = 1;
        animation_reset(anim);
        game.rescue_actor = slot;
        game.rescue_kind = d->npc_kind;
        game.mode = RESCUE;
        game.p.attack = 0;
        game.rescued++;
        npc_sequence=(NpcSequence){0};sequence_step();
        return;
    }
    if (!animation_tick(anim, clip_for(slot)) && a->state == 2) {
        a->active = 0;
        if (d->npc_kind == 8) {
            game.spawned[a->source] = 0;
            respawn_delay[a->source] = 8;
        } else
            game.spawned[a->source] = 2;
    }
}
static void reward(u8 kind) {
    switch(kind) {
    case 1:game.coins+=100;break;
    case 3:game.p.hp=progress_max_hp;game.p.invincible=0;break;
    case 4:game.time+=30;break;
    }
}
static void sequence_step(void) {
    const NpcEvent *events=npc_events[game.rescue_kind-1];
    while(!npc_sequence.complete && events[npc_sequence.index].tick==npc_sequence.tick) {
        const NpcEvent *e=&events[npc_sequence.index++];
        switch(e->type) {
        case 0:npc_sequence.code=e->value;break;
        case 1:npc_sequence.page=e->value;break;
        case 2:game_sound(e->value);break;
        case 3:reward(e->value);break;
        case 4:
            npc_sequence.complete=1;
            game.actors[game.rescue_actor].state=2;
            animation_reset(&npc_animation[game.rescue_actor]);
            game.mode=e->value?SHOP:PLAY;game.shop_item=0;break;
        }
    }
    ++npc_sequence.tick;
}
void npc_rescue_tick(void){sequence_step();}
