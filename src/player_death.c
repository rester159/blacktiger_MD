#include "player_death.h"
#include "player_death_data.inc"
PlayerDeath player_death;
void player_death_reset(void){player_death=(PlayerDeath){0};}
void player_death_start(u8 hazard,u8 left) {
    u8 x=PX(game.p.x)-game.cam_x,y=PX(game.p.y)-game.cam_y;
    player_death=(PlayerDeath){.x={x,x},.y={y,y},.profile=(hazard?2:0)+!!left,.active=1};
    game.mode=DEAD;game.mode_timer=329;game.sound=SND_DIE;
}
u8 player_death_step(void) {
    PlayerDeath *p=&player_death;const PlayerDeathFrame *f;u16 i;
    if(!p->active)return p->finished;
    if(p->remaining && --p->remaining)return 0;
    if(p->index==33){p->active=0;p->finished=1;return 1;}
    f=&death_frames[p->profile][p->index++];p->remaining=f->ticks;
    for(i=0;i<2;i++){p->x[i]+=f->dx[i];p->y[i]+=f->dy[i];}
    return 0;
}
const PlayerDeathFrame *player_death_frame(void) {
    return player_death.active && player_death.index?&death_frames[player_death.profile][player_death.index-1]:0;
}
