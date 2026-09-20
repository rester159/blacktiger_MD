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

u8 actor_dagger_contact(u16 slot,s16 x,s16 y) {
 const Actor *a=&game.actors[slot];u8 pool=actor_contact_pool[a->def];s16 ax,ay,dx,dy;
 if(pool!=32 && pool!=48)return (x-PX(a->x)-16)>-20 && (x-PX(a->x)-16)<20 && (y-PX(a->y)-16)>-20 && (y-PX(a->y)-16)<20;
 if((game.frame&1)!=(pool==48))return 0;
 ax=PX(a->x)-game.cam_x;ay=PX(a->y)-game.cam_y;x-=game.cam_x;y-=game.cam_y;
 if((u16)ax>=256 || (u16)x>=256 || (pool==48 && (u16)ay>=256))return 0;
 dx=(u8)(x-(pool==48?8:0))-(u8)ax;
 dy=(u8)(y-(pool==48?8:0))-(u8)ay;
 return dx>=-(actor_contact_half_width[a->def]+dagger_width) && dx<=actor_contact_half_width[a->def]+dagger_width &&
        dy>=-(actor_contact_half_height[a->def]+dagger_height) && dy<=actor_contact_half_height[a->def]+dagger_height;
}

u8 actor_chain_contact(u16 slot,s16 x,s16 y) {
 const Actor *a=&game.actors[slot];u8 pool=actor_contact_pool[a->def];s16 ax,ay,dx,dy;
 if(pool!=32 && pool!=48)return (x-PX(a->x)-16)>=-24 && (x-PX(a->x)-16)<=24 && (y-PX(a->y)-16)>=-20 && (y-PX(a->y)-16)<=20;
 ax=PX(a->x)-game.cam_x;ay=PX(a->y)-game.cam_y;
 if((u16)ax>=256 || (pool==48 && (u16)ay>=256))return 0;
 dx=(u8)(x-game.cam_x-(pool==48?8:0))-(u8)ax;
 dy=(u8)(y-game.cam_y-(pool==48?8:0))-(u8)ay;
 return dx>=-(actor_contact_half_width[a->def]+8) && dx<=actor_contact_half_width[a->def]+8 &&
        dy>=-(actor_contact_half_height[a->def]+4) && dy<=actor_contact_half_height[a->def]+4;
}
