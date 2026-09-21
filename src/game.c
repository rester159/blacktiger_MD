#include "ending.h"
#include "round_clear.h"
#include "game_over.h"
#include "actor_dispatch.h"
#include "bonus.h"
#include "music.h"
#include "armor_break.h"
#include "progress.h"
#include "player_motion.h"
#include "player_death.h"
#include "player_dagger.h"
#include "reinforcement.h"
#include "edge_spawn.h"
#include "checkpoint.h"
#include "game.h"
#include "container.h"
#include "shop.h"
#include "status.h"
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
#include "statue_shell.h"
#include "npc.h"
#include "skeleton.h"
#include "world.h"
Game game;
PlayerMotion player_motion;
PlayerAttack player_attack;
static void motion_reset(void) {
    Player *p=&game.p;
    player_motion=(PlayerMotion){.scroll_x=PX(p->x)-128,.scroll_y=PX(p->y)-144,
        .screen_x=128,.screen_y=144,.selector=p->face?4:0,.previous=p->face?4:0,.ladder=p->climb};
}
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
        u8 value=bonus_collision(cell,r->collision[cell]);
        return world_opened ? world_collision(cell,value) : value;
    }
}
static u8 support(s16 x, s16 y) {
    return terrain(x, y) >= 2;
}
static u8 restart_pending,loaded_round=255;
void game_round(u8 round) {
    round_clear_reset();game_over_reset();
    music_request=0x21+(round&7);
    Player *p = &game.p;
    const Round *r = &rounds[round];
    u8 preserve=restart_pending && loaded_round==round;
    u16 restart_x=r->start_x,restart_y=r->start_y;
    if(preserve)checkpoint_lookup(round,game.cam_x,game.cam_y,&restart_x,&restart_y);
    status_reverse=shop_poison=0;loaded_round=round;game.round = round;
    zero(game.actors, sizeof game.actors);
    zero(game.shots, sizeof game.shots);
    if(preserve){u16 i;for(i=0;i<160;i++)game.spawned[i]&=254;world_restart();}
    else {zero(game.spawned,sizeof game.spawned);world_reset();teleporter_reset();eruption_reset();reinforcement_reset();}
    bonus_reset(preserve);
    npc_reset();
    skeleton_reset();
    emerge_reset();
    zombie_reset();
    missile_reset();statue_shell_reset();waveboss_reset();flailer_reset();reinforcement_shots_reset();edge_shots_reset();dragon_shots_reset();
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
    motion_reset();game.player_low=0;player_death_reset();armor_break_reset();
    player_attack=(PlayerAttack){0};player_daggers_reset();
}
void game_bonus_transition(void) {
 u16 i,x=player_motion.scroll_x,y=player_motion.scroll_y;
 music_request=bonus_entered?0x21+game.round:0x2d;
 bonus_destination(game.round,bonus_entered,&x,&y,&bonus_saved_x,&bonus_saved_y);
 bonus_entered=1;bonus_animation_reset();
 zero(game.actors,sizeof game.actors);zero(game.shots,sizeof game.shots);
 for(i=0;i<160;i++)game.spawned[i]&=254;
 world_restart();npc_reset();skeleton_reset();emerge_reset();zombie_reset();
 missile_reset();statue_shell_reset();waveboss_reset();flailer_reset();
 reinforcement_shots_reset();edge_shots_reset();dragon_shots_reset();loot_reset();container_actor_restart();
 player_attack=(PlayerAttack){0};player_daggers_reset();armor_break_reset();
 shop_poison=0;game.p.attack=0;
 player_motion.scroll_x=x;player_motion.scroll_y=y;
 game.p.x=(s32)(u16)(x+player_motion.screen_x)*FX;
 game.p.y=(s32)(u16)(y+player_motion.screen_y)*FX;
 game.cam_x=bound_axis(PX(game.p.x)-112,0,rounds[game.round].width-256);
 game.cam_y=bound_axis(PX(game.p.y)-144,0,rounds[game.round].height-224);
}
void game_new(void) {
    ending_reset();
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
    game_round(0);
}
void game_boss_clear(void) {
 round_clear_reset();armor_break_reset();game.p.attack=0;
 player_attack=(PlayerAttack){0};player_daggers_reset();
 zero(game.actors,sizeof game.actors);zero(game.shots,sizeof game.shots);
 missile_reset();statue_shell_reset();waveboss_reset();flailer_reset();reinforcement_shots_reset();edge_shots_reset();dragon_shots_reset();loot_reset();skeleton_reset();container_actor_restart();
 game.boss_dead=1;game.mode=CLEAR;game.mode_timer=0;game.sound=SND_CLEAR;
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
    if (edge_spawn_kinds[a->def]){edge_actor_hit(a-game.actors,damage);return;}
    if (reinforcement_kinds[a->def]){reinforcement_body_hit(a-game.actors,damage);return;}
    if (flailer_kinds[a->def]){flailer_hit(a-game.actors,damage);return;}
    if (dragon_kinds[a->def]){dragon_hit(a-game.actors,damage);return;}
    if (waveboss_kinds[a->def]){waveboss_hit(a-game.actors,damage);return;}
    if (eruption_kinds[a->def])return;
    if (teleporter_kinds[a->def]){teleporter_hit(a-game.actors,damage);return;}
    if (hunter_kinds[a->def]){hunter_hit(a-game.actors,damage);return;}
    if (crawler_kinds[a->def]){crawler_hit(a-game.actors,damage);return;}
    if (statue_kinds[a->def]){statue_hit(a-game.actors,damage);return;}
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
    if(!reinforcement_kinds[a->def])game.spawned[a->source] = 2;
    game.kills++;
    progress_score(layered_boss_kinds[a->def] ? layered_boss_score : d->kind == BOSS ? 5000 : 100);
    if (!layered_boss_kinds[a->def])
        loot_spawn(drop_categories[a->def], loot_random >> 8, PX(a->x), PX(a->y));
    game.sound = SND_KILL;
    if (d->kind == BOSS) {
        game_boss_clear();
    }
}
/* Ordinary scenes need one actor scan, not one full scan per boss family. */
static u8 any_boss(u8 locked) {
    u16 i;
    for(i=0;i<MAX_ACTORS;i++) {
        const Actor *a=&game.actors[i];
        if(!a->active)continue;
        if(layered_boss_kinds[a->def]) {
            if(locked?boss_locked():boss_present())return 1;
        } else if(hunter_kinds[a->def]==2 || waveboss_kinds[a->def] || dragon_kinds[a->def]) {
            if(!locked || a->state==2)return 1;
        }
    }
    return 0;
}
static void spawn_actors(void) {
    const Round *r = &rounds[game.round];
    u16 i, j;
    if(any_boss(0))return;
    for (i = game.frame & 3; i < r->spawn_count; i += 4) {
        const Spawn *s = &r->spawns[i];
        s16 sx=s->x,sy=s->y;
        if (game.spawned[i] && !eruption_kinds[s->def] && !(game.spawned[i]==1 && zombie_kinds[s->def]))
            continue;
        if (absolute((s16)s->x - (s16)game.cam_x - 128) > 176 ||
            absolute((s16)s->y - (s16)game.cam_y - 112) > 152)
            continue;
        if (zombie_kinds[s->def] && !zombie_prepare_variant(i,zombie_kinds[s->def]-1,&sx,&sy)) continue;
        if (!emerge_spawn_ready(i))
            continue;
        if (eruption_kinds[s->def] && !eruption_prepare(i,sx,sy))continue;
        if (reinforcement_kinds[s->def] && !reinforcement_prepare(i,sx,sy))continue;
        if (edge_spawn_kinds[s->def] && !edge_spawn_prepare(i,&sx,&sy))continue;
        if (teleporter_kinds[s->def] && !teleporter_prepare(i,&sx,&sy))continue;
        if (pair_kinds[s->def] && !pair_ready(sx,sy))continue;
        if (!npc_spawn_ready(i))
            continue;
        if(layered_boss_kinds[s->def] || hunter_kinds[s->def]==2 || waveboss_kinds[s->def] || dragon_kinds[s->def]) {
            music_request=music_boss_commands[game.round];
            zero(game.actors,sizeof game.actors);zero(game.shots,sizeof game.shots);
            missile_reset();statue_shell_reset();waveboss_reset();flailer_reset();reinforcement_shots_reset();edge_shots_reset();dragon_shots_reset();loot_reset();skeleton_reset();container_actor_restart();
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
                a->face = PX(game.p.x) < (edge_spawn_kinds[s->def]?sx:s->x) ? -1 : 1;
                a->timer = i * 7;
                if(actor_defs[a->def].kind==CHEST)container_spawn(j);
                boss_spawn(j);
                if(flailer_kinds[a->def])flailer_spawn(j);
                if(reinforcement_kinds[a->def])reinforcement_body_spawn(j);
                if(edge_spawn_kinds[a->def])edge_actor_spawn(j);
                if(waveboss_kinds[a->def])waveboss_spawn(j);
                if(dragon_kinds[a->def])dragon_spawn(j,dragon_kinds[a->def]-1);
                if(eruption_kinds[a->def])eruption_spawn(j);
                if(teleporter_kinds[a->def])teleporter_spawn(j);
                if(hunter_kinds[a->def])hunter_spawn(j,hunter_kinds[a->def]-1);
                if(crawler_kinds[a->def])crawler_spawn(j,0);
                if(statue_kinds[a->def])statue_spawn(j);
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
                game.spawned[i] = (eruption_kinds[s->def] || reinforcement_kinds[s->def])?game.spawned[i]:pair_kinds[s->def]?2:1;
                if(layered_boss_kinds[s->def] || hunter_kinds[s->def]==2 || waveboss_kinds[s->def] || dragon_kinds[s->def])return;
                break;
            }
    }
}
static void player_step(u16 in, u16 pressed) {
    Player *p = &game.p;
    u8 raw=0;
    status_tick();
    /* A restart/teleport establishes a fresh logical camera origin. */
    if ((s16)(player_motion.scroll_x+player_motion.screen_x)!=PX(p->x) ||
        (s16)(player_motion.scroll_y+player_motion.screen_y)!=PX(p->y)) motion_reset();
    if(in&IN_RIGHT)raw|=1;
    if(in&IN_LEFT)raw|=2;
    if(in&IN_DOWN)raw|=4;
    if(in&IN_UP)raw|=8;
    if(in&IN_JUMP)raw|=32;
    if(in&IN_ATTACK)raw|=16;
    player_motion_frame=game.frame;
    player_control_step(&player_motion,&player_attack,raw,status_reverse,p->weapon-1);
    {u8 i;for(i=0;i<player_motion_sound_count;++i)game_sound(player_motion_sounds[i]);}
    player_motion_sound_count=0;
    p->x=(s32)(s16)(player_motion.scroll_x+player_motion.screen_x)*FX;
    p->y=(s32)(s16)(player_motion.scroll_y+player_motion.screen_y)*FX;
    p->vx=player_motion.vx*FX;p->vy=player_motion.vy*FX+player_motion.fraction;
    p->climb=player_motion.ladder;
    p->grounded=!player_motion.jumping && !player_motion.falling && !p->climb;
    p->face=((player_motion.selector+1)&4)!=0;
    reinforcement_player_low=player_motion.low;
    game.player_low=player_motion.low && !player_motion.jumping;
    if(p->invincible)--p->invincible;
    p->attack=player_attack.active;
    p->x=bound_axis(PX(p->x),0,rounds[game.round].width-32)*FX;
    if(player_attack.launch && !shop_poison) {
        player_daggers_launch(PX(p->x),PX(p->y),(player_attack.selector+1)&4,player_motion.low);
        player_attack.launch=0;
    }
    player_daggers_step();
    if (PX(p->y) > rounds[game.round].height + 32) {
        p->invincible = 0;
        p->hp = 1;
        p->armor = 0;
        player_hurt(1);
    }
}
static void screen_attack(void) {
    flailer_weapons_clear_attack();reinforcement_shots_reset();edge_shots_reset();dragon_shots_reset();
    u16 j;
    for(j=0;j<MAX_MISSILES;j++)missile_hit(j,255);
    for (j = 0; j < MAX_ACTORS; j++) {
        Actor *a = &game.actors[j];
        if (!a->active || !screen_attack_targets[a->def]) continue;
        if (a->state && (edge_spawn_kinds[a->def] || reinforcement_kinds[a->def] || skeleton_kinds[a->def] != 255 || sentry_kinds[a->def] || emerge_kinds[a->def] || wisp_kinds[a->def] || zombie_kinds[a->def] || layered_boss_kinds[a->def] || stone_kinds[a->def] || boulder_kinds[a->def] || pair_kinds[a->def] || statue_kinds[a->def] || crawler_kinds[a->def] || hunter_kinds[a->def] || teleporter_kinds[a->def])) continue;
        a->hit = 0;
        a->hp = 1;
        a->life = 1;
        if(edge_spawn_kinds[a->def])edge_screen_attack(j);
        else if(reinforcement_kinds[a->def])reinforcement_screen_attack(j);
        else if(flailer_kinds[a->def])flailer_screen_attack(j);
        else if(dragon_kinds[a->def])dragon_screen_attack(j);
        else if(waveboss_kinds[a->def])waveboss_screen_attack(j);
        else if(eruption_kinds[a->def]){a->active=0;game.spawned[a->source]^=1;}
        else if(teleporter_kinds[a->def])teleporter_screen_attack(j);
        else if(hunter_kinds[a->def])hunter_screen_attack(j);
        else if(crawler_kinds[a->def])crawler_screen_attack(j);
        else if(statue_kinds[a->def])statue_screen_attack(j);
        else actor_hit(a, 200);
    }
}
static void actor_step(u16 i, u16 pressed) {
    Actor *a = &game.actors[i];
    const ActorDef *d = &actor_defs[a->def];
    Player *p = &game.p;
    s16 x = PX(a->x), y = PX(a->y), dx, dy;
    u8 close;
    if (a->hit)
        --a->hit;
    a->timer++;
    if (layered_boss_kinds[a->def]) {
        boss_step(i);
        if (!a->state && (!boss_vulnerable(i) || (game.frame&1)) && actor_contact(i)) player_hurt_from(boss_contact_damage(i),PX(a->x));
        return;
    }
    if (pair_kinds[a->def]) {
        pair_step(i);
        if(a->active && pair_vulnerable(i) && !(game.frame&1) && actor_contact(i))player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    if(dragon_kinds[a->def]){dragon_step(i,dragon_projectile_spawn);if(a->active && dragon_player_contact(i))player_hurt_from(actor_damage[a->def],PX(a->x));return;}
    /* These families integrate source edge checks themselves, including the
       dynamic suppression flag. Do not preempt them with the broad fallback. */
    switch(actor_dispatch[a->def].behavior) {
    case BEHAVIOR_EDGE:case BEHAVIOR_REINFORCEMENT:case BEHAVIOR_FLAILER:
    case BEHAVIOR_TELEPORTER:case BEHAVIOR_HUNTER:case BEHAVIOR_CRAWLER:
    case BEHAVIOR_WISP:break;
    default:
        if(skeleton_kinds[a->def]==255 &&
           (absolute(x-(s16)game.cam_x-128)>352 || absolute(y-(s16)game.cam_y-112)>300)) {
            game.spawned[a->source]&=254;a->active=0;return;
        }
    }
    switch(actor_dispatch[a->def].behavior) {
    case BEHAVIOR_EDGE: {
        edge_actor_step(i);
        if(a->active && (game.frame&1) && actor_contact(i) && edge_actor_contact(i))player_hurt_from(2,PX(a->x));
        return;
    }
    case BEHAVIOR_REINFORCEMENT: {
        reinforcement_body_step(i);
        if(a->active && reinforcement_body_contact(i) && (game.frame&1) && actor_contact(i))player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_FLAILER: {
        flailer_step(i);
        if(a->active && flailer_vulnerable(i) && (game.frame&1) && actor_contact(i))player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_WAVEBOSS: {
        waveboss_step(i);
        if(a->active && waveboss_contact(i) && waveboss_player_contact(i))player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_ERUPTION: {
        eruption_step(i);
        if(a->active && eruption_contact(i) && (game.frame&1) && actor_contact(i)){
            if(eruption_kinds[a->def]>=3)status_poison_contact();
            player_hurt_from(actor_damage[a->def],PX(a->x));
        }
        return;
    }
    case BEHAVIOR_TELEPORTER: {
        teleporter_step(i);
        if(a->active && teleporter_contact(i) && (game.frame&1) && actor_contact(i))player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_HUNTER: {
        hunter_step(i);
        if(a->active && hunter_contact(i) && (game.frame&1) && actor_contact(i))player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_CRAWLER: {
        crawler_step(i);
        if(a->active && crawler_contact(i) && !(game.frame&1) && actor_contact(i)) {
            if(crawler_kinds[a->def]!=3 || status_poison_cloud_contact())player_hurt_from(actor_damage[a->def],PX(a->x));
        }
        return;
    }
    case BEHAVIOR_STATUE: {
        statue_step(i);
        if(a->active && statue_contact(i) && (game.frame&1) && actor_contact(i))player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_BOULDER: {
        boulder_step(i);
        if (a->active && boulder_damage(i) && (game.frame&1) && actor_contact(i)) player_hurt_from(boulder_damage(i),PX(a->x));
        return;
    }
    case BEHAVIOR_STONE: {
        boss_step(i);
        if (!a->state && (!boss_vulnerable(i) || (game.frame&1)) && actor_contact(i)) player_hurt_from(boss_contact_damage(i),PX(a->x));
        return;
    }
    case BEHAVIOR_ZOMBIE: {
        zombie_step(i);
        if ((game.frame&1) && zombie_vulnerable(i) && actor_contact(i)) player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_WISP: {
        wisp_step(i);
        if (a->active && (game.frame & 1) && player_contact(PX(a->x)+8,PX(a->y)+8,12,12)) player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_EMERGE: {
        if (emerge_step(i)) player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    case BEHAVIOR_HAZARD: {
        hazard_step(i);
        return;
    }
    default:break;
    }
    /* These families use pre-movement contact. Earlier native families perform
       their own contact checks after movement and need no duplicate query. */
    close=actor_contact(i);dx=PX(p->x)-x;dy=PX(p->y)-y;
    if (sentry_kinds[a->def]) {
        sentry_step(i);
        if (a->active && !a->state && close) player_hurt_from(actor_damage[a->def],PX(a->x));
        return;
    }
    if (skeleton_kinds[a->def] != 255) {
        skeleton_step(i);
        if (a->active && !a->state && close)
            player_hurt_from(actor_damage[a->def],PX(a->x));
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
            player_hurt_from(actor_damage[a->def],PX(a->x));
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
        player_hurt_from(actor_damage[a->def],PX(a->x));
}
static u8 weapon_target(u16 j) {
    ActorVulnerable check;
    if(!game.actors[j].active)return 0;
    check=actor_vulnerable[game.actors[j].def];
    return !check || check(j);
}
static u8 weapon_contact(u16 j,s16 x,s16 y,u8 dagger) {
    Actor *a=&game.actors[j];
    if(actor_contact_pool[a->def]!=32 && actor_contact_pool[a->def]!=48 && !(game.frame&1))return 0;
    if(dragon_kinds[a->def])return dragon_weapon_contact(j,x,y,dagger);
    if(waveboss_kinds[a->def])return waveboss_weapon_contact(j,x,y,dagger);
    return (dagger?actor_dagger_contact(j,x,y):actor_chain_contact(j,x,y))?2:0;
}
/* Captured immediately before projectile collisions; hit callbacks only mutate
   their own pools, so an empty family stays empty throughout this pass. */
static u8 weapon_pools(void) {
    u16 i;u8 mask=0;
    for(i=0;i<24;i++) {
        if(i<16 && dragon_shots[i].active)mask|=1;
        if(edge_shots[i].active)mask|=2;
        if(flailer_weapons[i].active)mask|=4;
        if(i<MAX_STATUE_SHELLS) {
            if(hunter_shells[i].active)mask|=8;
            if(statue_shells[i].active)mask|=16;
        }
        if(i<MAX_MISSILES && missiles[i].active)mask|=32;
    }
    return mask;
}
static u8 weapon_projectile(s16 x,s16 y,u8 damage,u8 dagger,u8 pools) {
    return ((pools&1) && dragon_shot_hit(x,y,damage,dagger)) || ((pools&2) && edge_shot_hit(x,y,damage,dagger)) ||
        ((pools&4) && flailer_weapon_hit(x,y,dagger)) || ((pools&8) && hunter_shell_hit_at(x,y,dagger)) ||
        ((pools&16) && statue_shell_hit_at(x,y,dagger)) || ((pools&32) && missile_hit_at(x,y,damage,dagger));
}
static void player_weapons_contact(void) {
    u16 i,j;u8 damage=player_attack.damage,pools;
    s16 y=PX(game.p.y)+(player_motion.jumping || player_motion.ladder || !(player_motion.selector&3)?6:14);
    if(player_attack.hit)return;
    if(!player_attack.count) {
        for(i=0;i<PLAYER_DAGGERS && player_daggers[i].active!=1;i++);
        if(i==PLAYER_DAGGERS)return;
    }
    /* Each source actor checks every extended link, then the nine daggers. */
    for(j=0;j<MAX_ACTORS;j++) {
        u8 chain_hit=0;
        if(!weapon_target(j))continue;
        for(i=0;i<player_attack.count;i++) {
            s16 x=PX(game.p.x)+(((player_attack.selector+1)&4)?-16-16*i:32+16*i);
            u8 contact=weapon_contact(j,x,y,0);
            if(contact) {
                if(contact==2)actor_hit(&game.actors[j],damage);
                player_attack_hit(&player_attack);chain_hit=1;break;
            }
        }
        for(i=0;i<PLAYER_DAGGERS;i++) {
            PlayerDagger *p=&player_daggers[i];u8 contact;
            if(p->active!=1)continue;
            contact=weapon_contact(j,p->x,p->y,1);
            if(contact) {
                if(contact==2)actor_hit(&game.actors[j],damage>1?damage>>1:1);
                player_dagger_hit(i,contact==1 || actor_dagger_effect[game.actors[j].def]);
            }
        }
        if(chain_hit)return;
    }
    pools=weapon_pools();
    if(!pools)return;
    for(i=0;i<player_attack.count;i++) {
        s16 x=PX(game.p.x)+(((player_attack.selector+1)&4)?-16-16*i:32+16*i);
        if(weapon_projectile(x,y,damage,0,pools)){player_attack_hit(&player_attack);return;}
    }
    for(i=0;i<PLAYER_DAGGERS;i++) {
        PlayerDagger *p=&player_daggers[i];
        if(p->active==1 && weapon_projectile(p->x,p->y,damage,1,pools))player_dagger_hit(i,0);
    }
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
                player_hurt_from(s->damage,x);
                s->active = 0;
            }
        } else if(dragon_shot_hit(x,y,s->damage,s->kind) || edge_shot_hit(x,y,s->damage,s->kind) || flailer_weapon_hit(x,y,s->kind) || hunter_shell_hit_at(x,y,s->kind) || statue_shell_hit_at(x,y,s->kind) || missile_hit_at(x,y,s->damage,s->kind))s->active=0;
        else
            for (j = 0; j < MAX_ACTORS; j++) {
                Actor *a = &game.actors[j];
                if(a->active && dragon_kinds[a->def]){
                    u8 contact=dragon_weapon_contact(j,x,y,s->kind==1);
                    if(contact){if(contact==2)actor_hit(a,s->kind==1?(s->damage>1?s->damage>>1:1):s->damage);s->active=0;break;}
                    continue;
                }
                if(a->active && waveboss_kinds[a->def]){
                    u8 contact=waveboss_weapon_contact(j,x,y,s->kind==1);
                    if(contact){if(contact==2)actor_hit(a,s->kind==1?(s->damage>1?s->damage>>1:1):s->damage);s->active=0;break;}
                    continue;
                }
                if (a->active && (s->kind==1?actor_dagger_contact(j,x,y):
                    (absolute(x - PX(a->x) - 16) < 20 && absolute(y - PX(a->y) - 16) < 20))) {
                    u8 k = actor_defs[a->def].kind;
                    if (k == CHEST || k == CAPTIVE || k == PICKUP || k == HAZARD || k == HIDDEN_WALL)
                        continue;
                    if (waveboss_kinds[a->def] && !waveboss_vulnerable(j))continue;
                    if (flailer_kinds[a->def] && !flailer_vulnerable(j))continue;
                    if (reinforcement_kinds[a->def] && !reinforcement_body_vulnerable(j))continue;
                    if (edge_spawn_kinds[a->def] && !edge_actor_vulnerable(j))continue;
                    if (eruption_kinds[a->def])continue;
                    if (teleporter_kinds[a->def] && !teleporter_vulnerable(j))continue;
                    if (hunter_kinds[a->def] && !hunter_vulnerable(j))continue;
                    if (crawler_kinds[a->def] && !crawler_vulnerable(j))continue;
                    if (statue_kinds[a->def] && !statue_vulnerable(j))continue;
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
    if(game.mode!=ENDING && game.mode!=GAMEOVER)bonus_tick();
    if (game.mode == RESCUE) {
        npc_rescue_tick();
        return;
    }
    if (game.mode == SHOP) {
        shop_move(pressed);
        if (pressed & IN_ATTACK) {
            u8 item=shop_grid[game.shop_item];
            if(item==11)game.mode=PLAY;
            else {u8 status=shop_poison || status_reverse;
                if(shop_buy(item) && item==10 && status)player_attack.launch=0;}
        }
        if (pressed & (IN_START | IN_JUMP))
            game.mode = PLAY;
        return;
    }
    if (game.mode == PLAY || game.mode == DEAD)armor_break_step();
    if (game.mode == DEAD) {
        if(player_death.active) {
            player_attack=(PlayerAttack){0};
            player_daggers_step();
            if(!player_death_step()){if(game.mode_timer)--game.mode_timer;return;}
            game.mode_timer=0;
        }
        if (game.mode_timer)
            --game.mode_timer;
        else {
            p->armor=progress_initial_armor;shop_poison=0;status_reverse=0;
            if(p->lives)p->lives--;
            if(p->lives) {restart_pending=1;game_round(game.round);restart_pending=0;}
            else {game.mode=GAMEOVER;game_over_start();}
        }
        return;
    }
    if (game.mode == CLEAR) {
        if(!round_clear.active) {
            if(player_motion.jumping || player_motion.falling || player_motion.ladder) {
                player_step(player_motion.ladder?IN_DOWN:0,0);
                game.cam_x=bound_axis(PX(p->x)-112,0,rounds[game.round].width-256);
                game.cam_y=bound_axis(PX(p->y)-144,0,rounds[game.round].height-224);
                return;
            }
            round_clear_start();
        }
        if(round_clear_step()) {
            if(game.round<7)game_round(game.round+1);
            else {game.mode=ENDING;ending_start();ending_step();}
        }
        return;
    }
    if (game.mode == GAMEOVER) {
        u8 action;
        if(!game_over.phase)game_over_start();
        if(ending.complete && game_over.phase==1 && game_over.remaining==1) {
            game_over_reset();game.mode=TITLE;return;
        }
        action=game_over_step(input);
        if(action==1) {
            game.score=0;p->lives=progress_initial_lives;
            restart_pending=1;game_round(game.round);restart_pending=0;
            game.previous_input=input;
        } else if(action==2) {
            game_over_reset();game.mode=TITLE;
        }
        return;
    }
    if (game.mode == ENDING) {
        if(!ending.active)ending_start();
        if(ending_step()){game.p.lives=0;game.mode=GAMEOVER;game_over_start();}
        return;
    }
    if (pressed & IN_START) {
        game.mode = PAUSED;
        return;
    }
    if(container_locked_hint)container_locked_hint--;
    world_tick();
    if (any_boss(1)) input=pressed=0;
    player_step(input, pressed);
    if (game.mode != PLAY)
        return;
    loot_tick();
    {
    u8 moving_missiles=missile_tick();
    u8 shells=statue_shell_tick();shells|=hunter_shell_tick();
    if(shells){u16 i;for(i=0;i<MAX_STATUE_SHELLS;i++) {
        if(hunter_shells[i].active && !game.p.invincible && hunter_shell_player_contact(i,0))hunter_shell_contact(i);
        if(hunter_blasts[i].active && hunter_shell_player_contact(i,1))player_hurt_from(1,hunter_blasts[i].x);
        if(statue_shells[i].active && !game.p.invincible && statue_shell_player_contact(i,0))statue_shell_contact(i);
        if(statue_blasts[i].active && statue_shell_player_contact(i,1))player_hurt_from(1,statue_blasts[i].x);
    }}
    {
    u8 traps=container_traps_tick(),seeds=waveboss_seeds_tick();
    u8 flailers=flailer_weapons_tick(),reinforcements=reinforcement_shots_step();
    u8 edges=edge_shots_step(),dragons=dragon_shots_step();
    /* Seeds and dragon shots can create container waves after the trap update.
       Keep the later contact scan in those cases, including new entries. */
    traps|=seeds|dragons;
    if(dragons){u16 i;for(i=0;i<24;i++)if(dragon_shots[i].active && dragon_shot_contact(i))player_hurt_from(1,dragon_shots[i].x);}
    if(edges){u16 i;for(i=0;i<24;i++){u8 damage;if(!edge_shots[i].active)continue;damage=edge_shot_contact(i);if(damage)player_hurt_from(damage,edge_shots[i].x);}}
    if(reinforcements){u16 i;for(i=0;i<24;i++)if(reinforcement_shots[i].active && reinforcement_shot_contact(i))player_hurt_from(1,reinforcement_shots[i].x);}
    if(flailers){u16 i;for(i=0;i<MAX_ACTORS;i++){u8 contact;if(!flailer_weapons[i].active)continue;contact=flailer_weapon_contact(i);if(contact==1)player_hurt_from(1,flailer_weapons[i].x);else if(contact==2 && status_poison_cloud_contact())player_hurt_from(2,flailer_weapons[i].x);}}
    if(traps){u16 i;for(i=0;i<MAX_CONTAINER_TRAPS;i++){u8 contact;if(!container_traps[i].active)continue;contact=container_trap_contact(i);if(contact==1)player_hurt_from(1,container_traps[i].x);else if(contact==2 && !game.p.invincible)status_reverse_contact();}}
    }
    if(moving_missiles){
        u16 i;for(i=0;i<MAX_MISSILES;i++) {
            Missile *m=&missiles[i];
            if(m->active && missile_player_contact(i))player_hurt_from(m->damage,m->x);
        }
    }
    }
    {
        u16 i;u32 active=skeleton_weapons_tick();
        for (i=0;active;i++,active>>=1)if(active&1) {
            u8 damage = skeleton_weapon_contact(i);
            if (damage) {s16 wx,wy;skeleton_weapon_frame(i,&wx,&wy);player_hurt_from(damage,wx);}
        }
    }
    if (game.mode != PLAY)
        return;
    if(bonus_contact()){game_bonus_transition();return;}
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
    player_weapons_contact();
    shots_step();
    if (++game.clock == 60) {
        game.clock = 0;
        if (game.time)
            game.time--;
        else {
            p->hp = 1;
            armor_break_start();p->invincible = 0;
            player_hurt(1);
        }
    }
    game.cam_x = bound_axis(PX(p->x) - 112, 0, rounds[game.round].width - 256);
    game.cam_y = bound_axis(PX(p->y) - 144, 0, rounds[game.round].height - 224);
}
