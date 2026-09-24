#ifndef BACKDROP_H
#define BACKDROP_H
#include <genesis.h>
typedef struct {
 const u32 *extra,*far;
 const u16 *remap0,*remap1,*map;
 u16 original_tiles,far_tiles;
} Backdrop;
const u32 *backdrop_hud_patterns(void);
void backdrop_hud_edge_load(u16 x,u16 tile);
const Backdrop *backdrop_for_round(u8 round);
#endif
