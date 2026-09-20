#include "reinforcement.h"
typedef struct {u8 delay,waiting,attempts;} ReinforcementRow;
static ReinforcementRow reinforcement_rows[160];
void reinforcement_reset(void) {
 u16 i;for(i=0;i<160;i++)reinforcement_rows[i]=(ReinforcementRow){0,0,0};
}
u8 reinforcement_prepare(u16 row,s16 x,s16 y) {
 ReinforcementRow *s=&reinforcement_rows[row];
 s16 sx=x-game.cam_x,sy=y-game.cam_y;
 if((u16)sx>=256 || (u16)sy>=256)return 0;
 if((u8)(PX(game.p.x)-game.cam_x+48-sx)>=96 ||
    (u8)(PX(game.p.y)-game.cam_y+32-sy)>=64)return 0;
 if(s->waiting) {
  if(++s->delay==40)s->delay=s->waiting=0;
  return 0;
 }
 s->waiting=1;
 if(++s->attempts>=2)game.spawned[row]|=2;
 /* Original updates the row before allocating: a full pool consumes an attempt. */
 return 1;
}
