#include "progress.h"
#include "checkpoint.h"
#include "game.h"
#include "container.h"
#include "shop.h"
#include "damage.h"
#include "boss.h"
#include "assets.h"
#include "loot.h"
#include "sentry.h"
#include "hazard.h"
#include "pickup.h"
#include "emerge.h"
#include "wisp.h"
#include "zombie.h"
#include "missile.h"
#include "npc.h"
#include "skeleton.h"
#include "world.h"
Game game;
static s16 absolute(s16 x) {
    return x < 0 ? -x : x;
}
static s16 bound_axis(s16 x, s16 lo, s16 hi) {
    return x < lo ? lo : x > hi ? hi : x;
}
static void zero(void *p, u16 n) {
    u8 *b = p;
    while (n--)
        *b++ = 0;
}
u8 terrain(s16 x, s16 y) {
    const Round *r = &rounds[game.round];
    if (x < 0 || x >= r->width || y < 0)
        return 3;
    if (y >= r->height)
        return 0;
    {
        u16 cell = ((y >> 4) << (r->width == 2048 ? 7 : 6)) + (x >> 4);
        return world_opened ? world_collision(cell, r->collision[cell]) : r->collision[cell];
    }
}
static u8 support(s16 x, s16 y) {
    return terrain(x, y) >= 2;
}
static u8 restart_pending,loaded_round=255;
void game_round(u8 round) {
    Player *p = &game.p;
    const Round *r = &rounds[round];
    u8 preserve=restart_pending && loaded_round==round;
    u16 restart_x=r->start_x,restart_y=r->start_y;
    if(preserve)checkpoint_lookup(round,game.cam_x,game.cam_y,&restart_x,&restart_y);
    loaded_round=round;game.round = round;
    zero(game.actors, sizeof game.actors);
    zero(game.shots, sizeof game.shots);
    if(preserve){u16 i;for(i=0;i<160;i++)game.spawned[i]&=254;world_restart();}
    else {zero(game.spawned,sizeof game.spawned);world_reset();}
    npc_reset();
    skeleton_reset();
    emerge_reset();
    zombie_reset();
    missile_reset();
    loot_reset();
    container_round(round);
    if(preserve)container_actor_restart();else container_actor_reset();
    game.mode = PLAY;
    game.mode_timer = 0;
    game.boss_dead = 0;
    game.rescued = 0;
    game.time = 180;
    game.clock = 0;
    game.cam_x = restart_x;
    game.cam_y = restart_y;
    p->x = (restart_x + checkpoint_player_x) * FX;
    p->y = (restart_y + checkpoint_player_y) * FX;
    p->vx = p->vy = 0;
    p->climb = p->grounded = p->attack = 0;
    p->invincible = 120;
    p->face = 0;
    p->hp = progress_max_hp;
}
void game_new(void) {
    restart_pending=0;loaded_round=255;
    zero(&game, sizeof game);
    loot_new();
    container_new();
    container_keys=0;
    shop_new();
    progress_new();
    game.coins=progress_initial_coins;
    game.p.lives = progress_initial_lives;
    game.p.armor = progress_initial_armor;
    game.p.weapon = 1;
    game.p.magic = 2;
    game_round(0);
}
static void shot(s16 x, s16 y, s16 vx, s16 vy, u8 enemy, u8 kind) {
    u16 i;
    for (i = 0; i < MAX_SHOTS; i++)
        if (!game.shots[i].active) {
            Shot *s = &game.shots[i];
            s->active = 1;
            s->x = x * FX;
            s->y = y * FX;
            s->vx = vx;
            s->vy = vy;
            s->enemy = enemy;
            s->kind = kind;
            s->damage = enemy ? 1 : player_attack_damage(game.p.weapon);
            s->life = 80;
            break;
        }
}
static void actor_hit(Actor *a, u8 damage) {
    const ActorDef *d = &actor_defs[a->def];
    if (a->hit || !a->active || d->kind == CHEST || d->kind == CAPTIVE || d->kind == PICKUP || d->kind == HAZARD)
        return;
    if (pair_hit(a-game.actors,damage)) return;
    if (boulder_hit(a-game.actors,damage)) return;
    if (boss_hit(a-game.actors,damage)) return;
    if (zombie_hit(a-game.actors,damage)) return;
    if (wisp_hit(a - game.actors))
        return;
    if (emerge_hit(a - game.actors, damage))
        return;
    if (sentry_hit(a - game.actors, damage))
        return;
    if (skeleton_hit(a - game.actors, damage))
        return;
    if (d->kind == HIDDEN_WALL && a->state)
        return;
    a->hit = 10;
    if (a->hp > damage) {
        a->hp -= damage;
        game.sound = SND_HIT;
        return;
    }
    if (d->kind == HIDDEN_WALL) {
        hidden_break(a - game.actors);
        return;
    }
    a->active = 0;
    game.spawned[a->source] = 2;
    game.kills++;
    progress_score(layered_boss_kinds[a->def] ? layered_boss_score : d->kind == BOSS ? 5000 : 100);
    if (!layered_boss_kinds[a->def])
        loot_spawn(drop_categories[a->def], loot_random >> 8, PX(a->x), PX(a->y));
    game.sound = SND_KILL;
    if (d->kind == BOSS) {
        game.boss_dead = 1;
        game.mode = CLEAR;
        game.mode_timer = 180;
        game.sound = SND_CLEAR;
    }
}
static void spawn_actors(void) {
    const Round *r = &rounds[game.round];
    u16 i, j;
    if(boss_present())return;
    for (i = game.frame & 3; i < r->spawn_count; i += 4) {
        const Spawn *s = &r->spawns[i];
        s16 sx=s->x,sy=s->y;
        if (game.spawned[i] && !(game.spawned[i]==1 && zombie_kinds[s->def]))
            continue;
        if (absolute((s16)s->x - (s16)game.cam_x - 128) > 176 ||
            absolute((s16)s->y - (s16)game.cam_y - 112) > 152)
            continue;
        if (zombie_kinds[s->def] && !zombie_prepare_variant(i,zombie_kinds[s->def]-1,&sx,&sy)) continue;
        if (!emerge_spawn_ready(i))
            continue;
        if (pair_kinds[s->def] && !pair_ready(sx,sy))continue;
        if (!npc_spawn_ready(i))
            continue;
        if(layered_boss_kinds[s->def]) {
            zero(game.actors,sizeof game.actors);zero(game.shots,sizeof game.shots);
            missile_reset();loot_reset();skeleton_reset();
        }
        for (j = 0; j < MAX_ACTORS; j++)
            if (!game.actors[j].active) {
                Actor *a = &game.actors[j];
                zero(a, sizeof *a);
                a->active = 1;
                a->source = i;
                a->def = s->def;
                a->hp = actor_defs[s->def].hp;
                a->x = sx * FX;
                a->y = sy * FX;
                a->face = PX(game.p.x) < s->x ? -1 : 1;
                a->timer = i * 7;
                if(actor_defs[a->def].kind==CHEST)container_spawn(j);
                boss_spawn(j);
                if(pair_kinds[a->def])pair_spawn(j);
                if(boulder_kinds[a->def])boulder_spawn(j);
                npc_spawn(j);
                if (zombie_kinds[a->def]) zombie_spawn(j);
                if (wisp_kinds[a->def]) wisp_spawn(j);
                if (emerge_kinds[a->def]) emerge_spawn(j);
                if (sentry_kinds[a->def])
                    sentry_spawn(j);
                if (skeleton_kinds[a->def] != 255)
                    skeleton_spawn(j);
                if (actor_defs[s->def].kind == HIDDEN_WALL)
                    hidden_spawn(j);
                game.spawned[i] = pair_kinds[s->def]?2:1;
                if(layered_boss_kinds[s->def])return;
                break;
            }
    }
}
static void player_step(u16 in, u16 pressed) {
    Player *p = &game.p;
    s16 x = PX(p->x), y = PX(p->y), nx, ny, feet;
    u8 ladder = terrain(x + 16, y + 16) == 1 || terrain(x + 16, y + 28) == 1;
    if (p->invincible)
        --p->invincible;
    if (p->attack)
        --p->attack;
    if ((pressed & IN_JUMP) && (p->grounded || p->climb)) {
        p->vy = -1408;
        p->grounded = p->climb = 0;
        game.sound = SND_JUMP;
    }
    if ((in & (IN_UP | IN_DOWN)) && ladder) {
        p->climb = 1;
        p->x = ((x + 16) & ~15) * FX - 8 * FX;
        p->vx = p->vy = 0;
    }
    if (p->climb) {
        p->vy = (in & IN_UP) ? -384 : (in & IN_DOWN) ? 384 : 0;
        if ((in & (IN_LEFT | IN_RIGHT)) || (!ladder && !(in & IN_UP)))
            p->climb = 0;
    }
    if (!p->climb) {
        p->vx = (in & IN_LEFT) ? -512 : (in & IN_RIGHT) ? 512 : 0;
        if (in & IN_LEFT)
            p->face = 1;
        if (in & IN_RIGHT)
            p->face = 0;
        p->vy += 48;
        if (p->vy > 1536)
            p->vy = 1536;
    }
    nx = PX(p->x + p->vx);
    if (p->vx && (terrain(nx + (p->vx > 0 ? 25 : 6), y + 9) == 3 ||
                  terrain(nx + (p->vx > 0 ? 25 : 6), y + 24) == 3))
        p->vx = 0;
    p->x += p->vx;
    x = PX(p->x);
    ny = PX(p->y + p->vy);
    feet = y + 32;
    p->grounded = 0;
    if (!p->climb && p->vy >= 0) {
        s16 row;
        for (row = feet >> 4; row <= (ny + 32) >> 4; row++) {
            s16 top = row * 16;
            if (top >= feet && (support(x + 7, top) || support(x + 24, top))) {
                p->y = (top - 32) * FX;
                p->vy = 0;
                p->grounded = 1;
                break;
            }
        }
    }
    if (!p->grounded) {
        if (!p->climb && p->vy < 0 &&
            (terrain(x + 8, ny + 2) == 3 || terrain(x + 23, ny + 2) == 3)) {
            p->vy = 0;
        } else
            p->y += p->vy;
    }
    if (p->climb && p->vy < 0 && terrain(x + 16, PX(p->y) + 32) != 1) {
        p->climb = 0;
        p->vy = 0;
    }
    p->x = bound_axis(PX(p->x), 0, rounds[game.round].width - 32) * FX;
    if ((in & IN_ATTACK) && !p->attack) {
        s16 dir = p->face ? -1 : 1;
        p->attack = 20;
        game.sound = SND_ATTACK;
        shot(x + 16 + dir * 16, y + 14, dir * 1280, 0, 0, 0);
        shot(x + 16, y + 12, dir * 1024, -128, 0, 1);
        shot(x + 16, y + 20, dir * 1024, 128, 0, 1);
    }
    if ((pressed & IN_MAGIC) && p->magic) {
        u16 i;
        p->magic--;
        game.sound = SND_KILL;
        for (i = 0; i < MAX_ACTORS; i++)
            if (actor_defs[game.actors[i].def].kind != HIDDEN_WALL)
                actor_hit(&game.actors[i], 8);
    }
    if (PX(p->y) > rounds[game.round].height + 32) {
        p->invincible = 0;
        p->hp = 1;
        p->armor = 0;
        player_hurt(1);
    }
}
static void screen_attack(void) {
    u16 j;
    for(j=0;j<MAX_MISSILES;j++)missile_hit(j,255);
    for (j = 0; j < MAX_ACTORS; j++) {
        Actor *a = &game.actors[j];
        if (!a->active || !screen_attack_targets[a->def]) continue;
        if (a->state && (skeleton_kinds[a->def] != 255 || sentry_kinds[a->def] || emerge_kinds[a->def] || wisp_kinds[a->def] || zombie_kinds[a->def] || layered_boss_kinds[a->def] || stone_kinds[a->def] || boulder_kinds[a->def] || pair_kinds[a->def])) continue;
        a->hit = 0;
        a->hp = 1;
        a->life = 1;
        actor_hit(a, 200);
    }
}
static void actor_step(u16 i, u16 pressed) {
    Actor *a = &game.actors[i];
    const ActorDef *d = &actor_defs[a->def];
    Player *p = &game.p;
    s16 x = PX(a->x), y = PX(a->y), dx = PX(p->x) - x, dy = PX(p->y) - y;
    u8 close = actor_contact(i);
    if (a->hit)
        --a->hit;
    a->timer++;
    if (layered_boss_kinds[a->def]) {
        boss_step(i);
        if (!a->state && (!boss_vulnerable(i) || (game.frame&1)) && actor_contact(i)) player_hurt(boss_contact_damage(i));
        return;
    }
    if (pair_kinds[a->def]) {
        pair_step(i);
        if(a->active && pair_vulnerable(i) && !(game.frame&1) && actor_contact(i))player_hurt(actor_damage[a->def]);
        return;
    }
    if (absolute(x - (s16)game.cam_x - 128) > 352 || absolute(y - (s16)game.cam_y - 112) > 300) {
        if (game.spawned[a->source] != 2)
            game.spawned[a->source] = 0;
        a->active = 0;
        return;
    }
    if (boulder_kinds[a->def]) {
        boulder_step(i);
        if (a->active && boulder_damage(i) && (game.frame&1) && actor_contact(i)) player_hurt(boulder_damage(i));
        return;
    }
    if (stone_kinds[a->def]) {
        boss_step(i);
        if (!a->state && (!boss_vulnerable(i) || (game.frame&1)) && actor_contact(i)) player_hurt(boss_contact_damage(i));
        return;
    }
    if (zombie_kinds[a->def]) {
        zombie_step(i);
        if ((game.frame&1) && zombie_vulnerable(i) && actor_contact(i)) player_hurt(actor_damage[a->def]);
        return;
    }
    if (wisp_kinds[a->def]) {
        wisp_step(i);
        if ((game.frame & 1) && player_contact(PX(a->x)+8,PX(a->y)+8,12,12)) player_hurt(actor_damage[a->def]);
        return;
    }
    if (emerge_kinds[a->def]) {
        if (emerge_step(i)) player_hurt(actor_damage[a->def]);
        return;
    }
    if (hazard_kinds[a->def]) {
        hazard_step(i);
        return;
    }
    if (sentry_kinds[a->def]) {
        sentry_step(i);
        if (a->active && !a->state && close) player_hurt(actor_damage[a->def]);
        return;
    }
    if (skeleton_kinds[a->def] != 255) {
        skeleton_step(i);
        if (a->active && !a->state && close)
            player_hurt(actor_damage[a->def]);
        return;
    }
    if (d->kind == HIDDEN_WALL) {
        if (hidden_step(i, absolute(dx) < 24 && absolute(dy) < 30))
            screen_attack();
        return;
    }
    if (pickup_kinds[a->def]) {
        if (pickup_step(i)) screen_attack();
        return;
    }
    if (d->kind == CAPTIVE) {
        npc_step(i, close);
        return;
    }
    if (d->kind == CHEST) {
        container_step(i,close);return;
    }
    if (d->kind == HAZARD) {
        if (close)
            player_hurt(actor_damage[a->def]);
        return;
    }
    if (d->kind == FLYER) {
        a->vx = dx < 0 ? -256 : 256;
        a->vy = dy < 0 ? -128 : 128;
        a->x += a->vx;
        a->y += a->vy;
    } else if (d->kind == TURRET) {
        if (a->timer % 100 == 0) {
            a->face = dx < 0 ? -1 : 1;
            shot(x + 16, y + 12, a->face * 640, 0, 1, 2);
        }
    } else if (d->kind == ROCK) {
        if (absolute(dx) < 64)
            a->state = 1;
        if (a->state) {
            a->vy += 48;
            a->y += a->vy;
            if (support(x + 8, PX(a->y) + 16)) {
                a->active = 0;
                game.spawned[a->source] = 2;
            }
        }
    } else {
        s16 speed = d->kind == BOSS ? 256 : 128;
        s16 oldfeet = y + 32, newfeet;
        u8 edge;
        if (d->kind == BOSS) {
            a->face = dx < 0 ? -1 : 1;
            if (a->timer % 75 == 0) {
                shot(x + 16, y + 16, a->face * 768, -64, 1, 2);
                shot(x + 16, y + 16, a->face * 640, 128, 1, 2);
            }
            if (a->timer % 120 == 0)
                a->vy = -1024;
        } else if (a->timer % 64 == 0)
            a->face = dx < 0 ? -1 : 1;
        edge = terrain(x + (a->face > 0 ? 28 : 3), y + 20) == 3;
        if (edge || (support(x + 16, y + 33) && !support(x + 16 + a->face * 18, y + 34)))
            a->face = -a->face;
        a->vx = a->face * speed;
        a->x += a->vx;
        a->vy += 48;
        if (a->vy > 1280)
            a->vy = 1280;
        newfeet = PX(a->y + a->vy) + 32;
        if (a->vy >= 0 && ((oldfeet & 15) == 0 || newfeet / 16 != oldfeet / 16) &&
            support(PX(a->x) + 16, newfeet)) {
            a->y = ((newfeet & ~15) - 32) * FX;
            a->vy = 0;
        } else
            a->y += a->vy;
        if (d->kind == WALKER && absolute(dx) < 80 && absolute(dy) < 24 && a->timer % 95 == 0)
            shot(x + 16, y + 16, (dx < 0 ? -1 : 1) * 640, 0, 1, 2);
    }
    if (close)
        player_hurt(actor_damage[a->def]);
}
static void shots_step(void) {
    u16 i, j, wall_count = 65535;
    u8 wall_slots[MAX_ACTORS];
    for (i = 0; i < MAX_SHOTS; i++) {
        Shot *s = &game.shots[i];
        s16 x, y;
        if (!s->active)
            continue;
        s->x += s->vx;
        s->y += s->vy;
        x = PX(s->x);
        y = PX(s->y);
        if (!s->enemy) {
            u16 k;
            if (wall_count == 65535) {
                wall_count = 0;
                for (j = 0; j < MAX_ACTORS; j++) {
                    Actor *a = &game.actors[j];
                    if (a->active && actor_defs[a->def].kind == HIDDEN_WALL && !a->state)
                        wall_slots[wall_count++] = j;
                }
            }
            for (k = 0; k < wall_count; k++) {
                Actor *a = &game.actors[wall_slots[k]];
                if (!a->state && absolute(x - PX(a->x) - 8) < 12 &&
                    absolute(y - PX(a->y) - 8) < 20) {
                    actor_hit(a, s->damage);
                    s->active = 0;
                    break;
                }
            }
            if (!s->active)
                continue;
        }
        if (!--s->life || absolute(x - (s16)game.cam_x - 128) > 176 ||
            absolute(y - (s16)game.cam_y - 112) > 152 || terrain(x, y) == 3) {
            s->active = 0;
            continue;
        }
        if (s->enemy) {
            if (absolute(x - PX(game.p.x) - 16) < 12 && absolute(y - PX(game.p.y) - 16) < 14) {
                player_hurt(s->damage);
                s->active = 0;
            }
        } else if(missile_hit_at(x,y,s->damage,s->kind))s->active=0;
        else
            for (j = 0; j < MAX_ACTORS; j++) {
                Actor *a = &game.actors[j];
                if (a->active && (s->kind==1?actor_dagger_contact(j,x,y):
                    (absolute(x - PX(a->x) - 16) < 20 && absolute(y - PX(a->y) - 16) < 20))) {
                    u8 k = actor_defs[a->def].kind;
                    if (k == CHEST || k == CAPTIVE || k == PICKUP || k == HAZARD || k == HIDDEN_WALL)
                        continue;
                    if (pair_kinds[a->def] && !pair_vulnerable(j))continue;
                    if ((layered_boss_kinds[a->def] || stone_kinds[a->def]) && !boss_vulnerable(j)) continue;
                    if (zombie_kinds[a->def] && !zombie_vulnerable(j)) continue;
                    if (emerge_kinds[a->def] && !emerge_vulnerable(j))
                        continue;
                    actor_hit(a, s->kind==1?(s->damage>1?s->damage>>1:1):s->damage);
                    s->active = 0;
                    break;
                }
            }
    }
}
void game_tick(u16 input) {
    u16 pressed = input & ~game.previous_input;
    Player *p = &game.p;
    game.previous_input = input;
    game.sound = 0;
    game.frame++;
    loot_random_tick();
    if (game.mode == TITLE) {
        if (pressed & IN_START) {
            game_new();game.previous_input=input;
        }
        return;
    }
    if (game.mode == PAUSED) {
        if (pressed & IN_START)
            game.mode = PLAY;
        return;
    }
    if (game.mode == RESCUE) {
        npc_rescue_tick();
        return;
    }
    if (game.mode == SHOP) {
        shop_move(pressed);
        if (pressed & IN_ATTACK) {
            u8 item=shop_grid[game.shop_item];
            if(item==11)game.mode=PLAY;
            else shop_buy(item);
        }
        if (pressed & (IN_START | IN_JUMP))
            game.mode = PLAY;
        return;
    }
    if (game.mode == DEAD) {
        if (game.mode_timer)
            --game.mode_timer;
        else {
            p->armor=progress_initial_armor;shop_poison=0;
            if(p->lives)p->lives--;
            if(p->lives) {restart_pending=1;game_round(game.round);restart_pending=0;}
            else game.mode=GAMEOVER;
        }
        return;
    }
    if (game.mode == CLEAR) {
        if (game.mode_timer)
            --game.mode_timer;
        else if (game.round < 7)
            game_round(game.round + 1);
        else
            game.mode = ENDING;
        return;
    }
    if (game.mode == GAMEOVER || game.mode == ENDING) {
        if (pressed & IN_START) {
            game_new();game.previous_input=input;
        }
        return;
    }
    if (pressed & IN_START) {
        game.mode = PAUSED;
        return;
    }
    world_tick();
    if (boss_locked()) input=pressed=0;
    player_step(input, pressed);
    if (game.mode != PLAY)
        return;
    loot_tick();
    missile_tick();
    container_traps_tick();
    {u16 i;for(i=0;i<MAX_CONTAINER_TRAPS;i++)if(container_trap_contact(i))player_hurt(1);}
    {
        u16 i;for(i=0;i<MAX_MISSILES;i++) {
            Missile *m=&missiles[i];
            if(missile_player_contact(i))player_hurt(m->damage);
        }
    }
    skeleton_weapons_tick();
    {
        u16 i;
        for (i = 0; i < MAX_ACTORS; i++) {
            u8 damage = skeleton_weapon_contact(i);
            if (damage) player_hurt(damage);
        }
    }
    if (game.mode != PLAY)
        return;
    spawn_actors();
    {
        u16 i;
        for (i = 0; i < MAX_ACTORS; i++) {
            if (game.actors[i].active)
                actor_step(i, pressed);
            if (game.mode != PLAY)
                return;
        }
    }
    shots_step();
    if (++game.clock == 60) {
        game.clock = 0;
        if (game.time)
            game.time--;
        else {
            p->hp = 1;
            p->armor = p->invincible = 0;
            player_hurt(1);
        }
    }
    game.cam_x = bound_axis(PX(p->x) - 112, 0, rounds[game.round].width - 256);
    game.cam_y = bound_axis(PX(p->y) - 144, 0, rounds[game.round].height - 224);
}
