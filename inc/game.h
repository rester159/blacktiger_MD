#ifndef GAME_H
#define GAME_H
#ifdef HOST_TEST
#include <stdint.h>
typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;
typedef int32_t s32;
#else
#include <genesis.h>
#endif
#define MAX_ACTORS 24
#define MAX_SHOTS 18
#define IN_LEFT 1
#define IN_RIGHT 2
#define IN_UP 4
#define IN_DOWN 8
#define IN_JUMP 16
#define IN_ATTACK 32
#define IN_START 64
#define IN_MAGIC 128
#define FX 256
#define PX(v) ((v) / FX)
enum { WALKER, FLYER, TURRET, ROCK, HAZARD, CHEST, CAPTIVE, PICKUP, BOSS, HIDDEN_WALL };
enum { TITLE, PLAY, PAUSED, SHOP, DEAD, CLEAR, ENDING, GAMEOVER, RESCUE };
enum {
    SND_NONE,
    SND_ATTACK,
    SND_JUMP,
    SND_HIT,
    SND_KILL,
    SND_COIN,
    SND_RESCUE,
    SND_BUY,
    SND_DIE,
    SND_CLEAR
};
typedef struct {
    u16 code[5];
    u8 flip, weapon_flip;
    s8 dx, dy;
} HeroFrame;
typedef struct {
    u16 code;
    u8 kind, palette, hp, pieces, frames, npc_kind;
} ActorDef;
typedef struct {
    u16 x, y, def, persistent;
} Spawn;
typedef struct {
    u16 cell;
    u8 source;
} WorldPatch;
typedef struct {
    const u32 *patterns;
    const u16 *map, *palette;
    const u8 *collision;
    const Spawn *spawns;
    u16 pattern_count, spawn_count, width, height, start_x, start_y;
    const WorldPatch *patches;
    const u16 *open_tile;
    u8 patch_count, open_collision;
} Round;
typedef struct {
    s32 x, y;
    s16 vx, vy;
    u16 def, timer, life;
    u8 active, hp, hit, source;
    s8 face;
    u8 state;
} Actor;
typedef struct {
    s32 x, y;
    s16 vx, vy;
    u8 active, enemy, life, damage, kind;
} Shot;
typedef struct {
    s32 x, y;
    s16 vx, vy;
    u16 invincible, attack;
    u8 grounded, climb, face, hp, armor, weapon, lives, magic;
} Player;
typedef struct {
    Player p;
    Actor actors[MAX_ACTORS];
    Shot shots[MAX_SHOTS];
    u8 spawned[160];
    u32 score;
    u16 coins, time, clock, frame, cam_x, cam_y, previous_input, mode_timer;
    u8 round, mode, sound, shop_item, rescued, boss_dead;
    u16 kills;
    u8 rescue_actor, rescue_kind, player_low;
} Game;
extern Game game;
void game_new(void);
void game_round(u8 round);
void game_tick(u16 input);
u8 terrain(s16 x, s16 y);
void video_init(void);
void video_round(void);
void video_frame(void);
void audio_tick(void);
void game_boss_clear(void);
#endif
