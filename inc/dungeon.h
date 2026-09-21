#ifndef DUNGEON_H
#define DUNGEON_H
#include "game.h"
enum {D_SETUP,D_STAGE_INTRO,D_STAGE_PLAY,D_DEATH,D_GATE,D_RESULTS};
typedef struct {
 u32 seed,streams[8],clock,run_xp,banked_xp,score,zenny;
 u16 timer,freeze,kills,last_kills,deaths,revision,seen_revision;
 u8 active,phase,stage,max_hp,charges,cleared,banked,scene_reload,boon,rank;
} Dungeon;
extern Dungeon dungeon;
extern const u16 dungeon_act_drain[4];
extern const u8 dungeon_fallback_stages[16];
u32 dungeon_rng(u32 *state);
u32 dungeon_mix(u32 seed,u32 tag);
void dungeon_seed(u32 seed);
void dungeon_open(void);
void dungeon_start(u32 seed);
u8 dungeon_tick(u16 input,u16 pressed);
void dungeon_reward(u16 seconds);
u8 dungeon_spend(u16 seconds);
u16 dungeon_seconds(void);
void dungeon_results(u8 victory);
void dungeon_screen(void);
void dungeon_hud(void);
void dungeon_ui_reset(void);
#endif
