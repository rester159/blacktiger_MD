#ifndef BACKDROP_H
#define BACKDROP_H
#include <genesis.h>
typedef struct {
 const u32 *extra,*far;
 const u16 *remap0,*remap1,*map;
 u16 original_tiles,far_tiles;
} Backdrop;
const Backdrop *backdrop_for_round(u8 round);
#endif
