#include "npc.h"
#include "assets.h"
/* Native state is separate from the old machine's actor records. */
static AnimState npc_animation[MAX_ACTORS];
static u8 respawn_delay[160];
void npc_reset(void) {
    u16 i;
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
        game.sound = SND_RESCUE;
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
void npc_rescue_tick(void) {
    Actor *a = &game.actors[game.rescue_actor];
    AnimState *anim = &npc_animation[game.rescue_actor];
    if (animation_tick(anim, &npc_rescue))
        return;
    a->state = 2;
    animation_reset(anim);
    game.mode = PLAY;
    /* Fixed 5FCD dispatch table: seven one-shot rewards and repeatable shop. */
    switch (game.rescue_kind) {
    case 1:
        game.coins += 100;
        game.sound = SND_COIN;
        break;
    case 2:
    case 8:
        game.mode = SHOP;
        game.shop_item = 0;
        break;
    case 3:
        game.p.hp = 4;
        game.sound = SND_RESCUE;
        break;
    case 4:
        game.time += 30;
        game.sound = SND_RESCUE;
        break;
    default:
        break; /* Hint-only variants have no numerical reward. */
    }
}
