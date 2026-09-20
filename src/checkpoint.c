#include "checkpoint.h"
#include "assets.h"
void checkpoint_lookup(u8 round,u16 camera_x,u16 camera_y,u16 *x,u16 *y) {
 u8 column=(u16)(camera_x+112)>>8,row=(u16)(camera_y+144)>>8,index;
 index=checkpoint_wide[round]?((row&3)*8+(column&7)):((row&7)*4+(column&3));
 *x=checkpoint_grid[round][index][0];*y=checkpoint_grid[round][index][1];
}
