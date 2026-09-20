#include "pickup.h"
#include "assets.h"
#include "hazard.h"
u8 pickup_step(u16 slot) {
    Actor *a = &game.actors[slot];
    u8 kind = pickup_kinds[a->def];
    if (a->state) { a->active = 0; return 0; }
    if (!player_contact(PX(a->x), PX(a->y), pickup_width, pickup_height)) return 0;
    a->state = 1;
    game.spawned[a->source] = 2;
    game.sound = SND_COIN;
    if (kind == 1) game.time += pickup_seconds;
    return kind == 2;
}
