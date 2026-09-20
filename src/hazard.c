#include "hazard.h"
#include "assets.h"
u8 player_contact(s16 x, s16 y, u8 half_width, u8 half_height) {
    s16 dx = PX(game.p.x) + 8 - x, dy = PX(game.p.y) + 8 - y;
    s16 width = half_width + contact_player_width, height = half_height + contact_player_height;
    return dx >= -width && dx <= width && dy >= -height && dy <= height;
}
u8 actor_contact(u16 slot) {
    const Actor *a = &game.actors[slot];
    u8 pool = actor_contact_pool[a->def];
    s16 x = PX(a->x), y = PX(a->y);
    if (pool == 32 || pool == 48) {
        /* Medium actor coordinates already share the player's origin. */
        if (pool == 48) { x += 8; y += 8; }
        return player_contact(x, y, actor_contact_half_width[a->def], actor_contact_half_height[a->def]);
    }
    /* Large and profile-dependent constructors still need their own contact port. */
    x = PX(game.p.x) - x; y = PX(game.p.y) - y;
    return x > -24 && x < 24 && y > -30 && y < 30;
}
void hazard_step(u16 slot) {
    Actor *a = &game.actors[slot];
    if (game.mode == PLAY && !game.boss_dead && player_contact(PX(a->x), PX(a->y), hazard_width, hazard_height)) {
        /* Source contact 39 enters death directly, bypassing armor and hurt invulnerability. */
        game.p.hp = 0;
        game.p.climb = 0;
        game.p.vx = game.p.vy = 0;
        game.mode = DEAD;
        game.mode_timer = 120; /* Existing native death presentation, still provisional. */
        game.sound = SND_DIE;
    }
}
