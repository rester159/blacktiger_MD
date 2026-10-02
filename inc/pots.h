#ifndef POTS_H
#define POTS_H
#include "animation.h"
#define MAX_POTS 33
#define POT_TRAP_SOURCE 159
typedef struct {u16 x,y;u8 id;} PotPlacement;
typedef struct {AnimState animation;s16 x,y;u16 segment;u8 active,id,kind,phase,hits,pending;} Pot;
extern Pot pots[MAX_POTS],pot_puffs[8];
extern u8 pots_end,pot_puffs_end,pot_contents[32];
extern const PotPlacement *const pot_placements[8];
extern const u8 pot_counts[8],pot_initial[8][32];
extern const u16 pot_roots[14][3],pot_puff,pot_cracked,pot_score,pot_trap_defs[4];
extern const AnimSegment pot_segments[];
void pots_round(u8 preserve);
void pots_clear(void);
void pots_tick(u8 bosses);
/* Prepare once before a batch; only pending-hit flags change within it. */
void pots_prepare_weapons(void);
u8 pots_weapon(s16 x,s16 y,u8 dagger);
const AnimFrame *pot_frame(u16 slot);
u16 pots_shuffle(u8 round,u16 seed,u8 *out);
#endif
