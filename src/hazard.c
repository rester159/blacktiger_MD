#include "hazard.h"
#include "assets.h"
u8 player_contact(s16 x, s16 y, u8 half_width, u8 half_height) {
    s16 dx = PX(game.p.x) + 8 - x, dy = PX(game.p.y) + 8 - y;
    s16 width = half_width + contact_player_width, height = half_height + contact_player_height;
    return dx >= -width && dx <= width && dy >= -height && dy <= height;
}
void hazard_step(u16 slot) {
    Actor *a = &game.actors[slot];
    if (game.mode == PLAY && player_contact(PX(a->x), PX(a->y), hazard_width, hazard_height)) {
        /* Source contact 39 enters death directly, bypassing armor and hurt invulnerability. */
        game.p.hp = 0;
        game.p.climb = 0;
        game.p.vx = game.p.vy = 0;
        game.mode = DEAD;
        game.mode_timer = 120; /* Existing native death presentation, still provisional. */
        game.sound = SND_DIE;
    }
}
