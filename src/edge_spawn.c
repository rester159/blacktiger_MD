#include "edge_spawn.h"
u8 edge_spawn_prepare(u16 row,s16 *x,s16 *y){
 s16 sx=*x-game.cam_x,sy=*y-game.cam_y;u16 i;
 if(game.spawned[row] || (u16)sx>=256 || (u16)sy>=256)return 0;
 if((u8)(PX(game.p.x)-game.cam_x+16-sx)>=32 ||
    (u8)(PX(game.p.y)-game.cam_y+16-sy)>=32)return 0;
 for(i=0;i<MAX_ACTORS && game.actors[i].active;i++){}
 if(i==MAX_ACTORS)return 0;
 game.spawned[row]|=1;
 *x=game.cam_x+(game.p.face?0:224);*y=game.cam_y+96;
 for(i=0;i<6;i++,*y+=16){u8 t=terrain(*x+16,*y+32);if(t==2 || t==3)return 1;}
 /* The source consumes the active flag even when its ground search fails. */
 *x=*y=0;return 0;
}
