#ifndef DUNGEON_LAYOUT_H
#define DUNGEON_LAYOUT_H
#include "game.h"
#define DUNGEON_TOP 512
#define DUNGEON_FLOOR 704
/* Compact source-map views: no RAM tilemap or duplicate graphics atlas. */
typedef struct {u8 x,y,anchor_count,anchors[4];} DungeonChunk;
typedef struct {
 u8 ready,count,source,ids[10];
 u16 exit_x;
} DungeonLayout;
extern DungeonLayout dungeon_layout;
extern Round dungeon_round;
void dungeon_generate(void);
u8 dungeon_terrain(s16 x,s16 y);
u16 dungeon_word(u16 x,u16 y);
void dungeon_checkpoint(u16 x,u16 *px,u16 *py);
#endif
