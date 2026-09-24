#include "player_dagger.h"
#include "player_dagger_data.inc"
PlayerDagger player_daggers[PLAYER_DAGGERS];
void player_daggers_reset(void) {
    u16 i;for(i=0;i<PLAYER_DAGGERS;i++)player_daggers[i].active=0;
}
static void select_segment(PlayerDagger *p,u16 segment) {
    animation_reset(&p->animation);p->segment=segment;
}
u8 player_daggers_launch(s16 x,s16 y,u8 left,u8 low) {
    u16 i,j;
    for(i=0;i<PLAYER_DAGGERS;i+=3) {
        if(player_daggers[i].active || player_daggers[i+1].active || player_daggers[i+2].active)continue;
        for(j=0;j<3;j++) {
            PlayerDagger *p=&player_daggers[i+j];
            *p=(PlayerDagger){.x=x+8,.y=y+(low?16:8),.active=1};
            select_segment(p,dagger_roots[(left?3:0)+j]);
        }
        return 1;
    }
    return 0;
}
void player_dagger_hit(u16 slot,u8 terrain_effect) {
    PlayerDagger *p=&player_daggers[slot];
    if(p->active==1){p->active=2;p->pending=terrain_effect?2:1;}
}
static u8 on_screen(s16 coordinate) {return !((u16)coordinate>>8) || (u8)coordinate>=240;}
void player_daggers_step(void) {
    u16 i;
    for(i=0;i<PLAYER_DAGGERS;i++) {
        PlayerDagger *p=&player_daggers[i];u8 tries;
        if(!p->active)continue;
        if(p->pending){select_segment(p,dagger_roots[p->pending==2?7:6]);p->pending=0;}
        for(tries=0;tries<4;tries++) {
            const AnimSegment *s=&dagger_segments[p->segment];
            if(animation_step(&p->animation,s->clip))break;
            if(!s->event){p->active=0;break;}
            if(terrain(p->x+8,p->y+8)>=2)select_segment(p,dagger_roots[7]);
            else select_segment(p,s->next);
        }
        if(!p->active)continue;
        p->x+=p->animation.vx;
        if(!on_screen(p->x-game.cam_x)){p->active=0;continue;}
        p->y+=p->animation.vy;
        if(!on_screen(p->y-game.cam_y)){p->active=0;continue;}
        p->hidden=((u16)(p->y-game.cam_y)>>8)!=0;
    }
}
const AnimFrame *player_dagger_frame(u16 slot) {
    PlayerDagger *p=&player_daggers[slot];
    return p->active && !p->hidden?animation_current(&p->animation,dagger_segments[p->segment].clip):0;
}
