#include "armor_break.h"
#include "hazard.h"
#include "player_death.h"
#include "assets.h"
u8 player_contact(s16 x, s16 y, u8 half_width, u8 half_height) {
    s16 dx=PX(game.p.x)+8-x;
    u16 width=(game.player_low?3:half_width)+contact_player_width;
    u16 height;
    s16 dy;
    if((u16)(dx+width)>width*2)return 0;
    height=(game.player_low?3:half_height)+contact_player_height;
    dy=PX(game.p.y)+(game.player_low?18:8)-y;
    return (u16)(dy+height)<=height*2;
}
u8 actor_contact(u16 slot) {
    const Actor *a=&game.actors[slot];
    u16 def=a->def;
    u8 pool=actor_contact_pool[def];
    s16 dx=PX(game.p.x)-PX(a->x),dy;
    if(pool==32 || pool==48) {
        u16 width=(game.player_low?3:actor_contact_half_width[def])+contact_player_width;
        u16 height;
        if(pool==32)dx+=8;
        if((u16)(dx+width)>width*2)return 0;
        height=(game.player_low?3:actor_contact_half_height[def])+contact_player_height;
        dy=PX(game.p.y)-PX(a->y)+(game.player_low?18:8)-(pool==48?8:0);
        return (u16)(dy+height)<=height*2;
    }
    if((u16)(dx+23)>46)return 0;
    dy=PX(game.p.y)-PX(a->y);
    return (u16)(dy+29)<=58;
}
void hazard_step(u16 slot) {
    Actor *a = &game.actors[slot];
    if (game.mode == PLAY && !game.p.exploration && !game.boss_dead && player_contact(PX(a->x), PX(a->y), hazard_width, hazard_height)) {
        /* Source contact 39 enters death directly, bypassing armor and hurt invulnerability. */
        armor_break_start();
        game.p.hp = 0;
        game.p.climb = 0;
        game.p.vx = game.p.vy = 0;
        player_death_start(1,game.p.face);
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
